"""
Visualiza la rejilla GRID y la ruta planificada.

Genera tres PNG en herramientas/:
  - map_ida.png
  - map_vuelta.png
  - map_ida_vuelta.png  (tambien map_visualization_simple.png)

Uso:
    python3 controllers/pioneer_TFM/herramientas/mundo_a_grid.py
"""

import os
import shutil
import sys

MPLCONFIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mpl-cache")
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", MPLCONFIGDIR)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planificacion import algoritmos
from planificacion.algoritmos import coste_camino, imprimir_detalle_informe_ara, planificar_mision
from configuracion.config import (
    BATERIA_MAX,
    CELDA_INICIO,
    CELDAS_OBJETIVO,
    COLUMNAS_MAPA,
    FILAS_MAPA,
    GRID,
    ALGORITMO,
    HEURISTICA,
    MODO_ARA,
    PASOS_POR_FASE_ARA,
    COSTE_ZONA_1,
    COSTE_ZONA_2,
    COSTE_ZONA_3,
    coste_de_zona,
    ZONAS_COSTE,
    _GRID_BASE,
    imprimir_configuracion_planificacion,
)

COLOR_LIBRE = (1.0, 1.0, 1.0)
COLOR_MARGEN = (0.82, 0.82, 0.82)
COLOR_MURO = (0.15, 0.15, 0.15)
COLOR_ZONA_COSTE = (0.12, 0.45, 0.95)
# Colores baseColor del .wbt (pioneer3at.wbt)
COLORES_ZONA_MUNDO = {
    "COST_ZONE_2": (0.12, 0.45, 0.95),  # azul
    "COST_ZONE_3": (0.18, 0.72, 0.28),  # verde
    "COST_ZONE_4": (0.95, 0.55, 0.12),  # amarillo
}


def _color_zona_mundo(zona):
    return COLORES_ZONA_MUNDO.get(zona.get("name"), COLOR_ZONA_COSTE)


COLOR_RUTA_OFFLINE = "royalblue"
COLOR_RUTA_INICIAL = "0.55"
COLOR_RUTA_INTERMEDIA = "darkorange"
COLOR_RUTA_FINAL = "royalblue"
COLOR_IDA_COMBINADO = "green"
COLOR_VUELTA_COMBINADO = "royalblue"
MARKER_SIZE_IDA = 6
MARKER_SIZE_VUELTA = 11
MARKER_EDGE_VUELTA = 1.5


def son_la_misma_ruta_ida_vuelta(ruta_ida, ruta_vuelta):
    """True si la ida coincide exactamente con la vuelta en orden inverso."""
    if not ruta_ida or not ruta_vuelta:
        return False
    return list(ruta_ida) == list(reversed(ruta_vuelta))


def _rutas_ida_vuelta(rutas):
    if not rutas:
        return [], []
    ruta_ida = list(rutas[0])
    ruta_vuelta = list(rutas[-1]) if len(rutas) > 1 else []
    return ruta_ida, ruta_vuelta


def _informe_anytime_principal():
    """Primer tramo ARA* en modo anytime_simple (p. ej. inicio -> objetivo)."""
    for informe in algoritmos.INFORME_ARA_MISION:
        if informe.get("modo") == "anytime_simple":
            return informe
    return None


def _seleccionar_rutas_anytime(informe):
    """
    Elige que rutas dibujar:
    - inicial: siempre la primera
    - intermedias: solo si cambian respecto a la anterior
    - final: siempre la ruta final del informe
    """
    historial = informe.get("historial", [])
    if not historial:
        final = list(informe.get("ruta_final", []))
        return [], [], final

    inicial = list(historial[0]["ruta_calculada"])
    intermedias = []
    anterior = inicial

    for entry in historial[1:]:
        if entry.get("accion") != "ruta actualizada":
            continue
        nueva = list(entry["ruta_calculada"])
        if nueva != anterior:
            intermedias.append(nueva)
        anterior = nueva

    final = list(informe.get("ruta_final", historial[-1]["ruta_calculada"]))
    return inicial, intermedias, final


def _marcador_leyenda_ida(label="Ruta ida"):
    return Line2D(
        [0], [0], color=COLOR_IDA_COMBINADO, marker="o", markersize=MARKER_SIZE_IDA,
        linestyle="None", label=label,
    )


def _marcador_leyenda_vuelta(label="Ruta vuelta"):
    return Line2D(
        [0], [0], color=COLOR_VUELTA_COMBINADO, marker="o", markersize=MARKER_SIZE_VUELTA,
        fillstyle="none", markeredgewidth=MARKER_EDGE_VUELTA, linestyle="None", label=label,
    )


def _dibujar_circulo_ruta(ax, ruta, color, markersize, hueco=False, zorder=10):
    """Mismos circulos que la leyenda, centrados en (col, fila)."""
    omitir = {CELDA_INICIO, *CELDAS_OBJETIVO}
    for fila, col in ruta:
        if (fila, col) in omitir:
            continue
        ax.plot(
            col,
            fila,
            marker="o",
            markersize=markersize,
            markerfacecolor="none" if hueco else color,
            markeredgecolor=color,
            markeredgewidth=MARKER_EDGE_VUELTA if hueco else 0.8,
            linestyle="None",
            zorder=zorder,
        )


def _dibujar_ruta_combinada_ida_vuelta(ax, ruta_ida, ruta_vuelta, ida_vuelta_comun):
    """Mapa combinado: punto verde (ida) sobre circulo azul hueco (vuelta)."""
    if ida_vuelta_comun:
        _dibujar_circulo_ruta(
            ax, ruta_ida, COLOR_IDA_COMBINADO, MARKER_SIZE_IDA, hueco=False, zorder=10,
        )
        return
    _dibujar_circulo_ruta(
        ax, ruta_vuelta, COLOR_VUELTA_COMBINADO, MARKER_SIZE_VUELTA, hueco=True, zorder=9,
    )
    _dibujar_circulo_ruta(
        ax, ruta_ida, COLOR_IDA_COMBINADO, MARKER_SIZE_IDA, hueco=False, zorder=10,
    )


def _leyenda_rutas_anytime(rutas_intermedias):
    """Leyenda ARA* anytime en mapa de ida: gris / naranja / verde (ruta final)."""
    entradas = [
        Line2D(
            [0], [0], color=COLOR_RUTA_INICIAL, marker="o", markersize=MARKER_SIZE_IDA,
            linestyle="None", label="Ruta inicial",
        ),
    ]
    if rutas_intermedias:
        entradas.append(
            Line2D(
                [0], [0], color=COLOR_RUTA_INTERMEDIA, marker="o", markersize=MARKER_SIZE_IDA,
                linestyle="None", label="Ruta recalculada",
            )
        )
    entradas.append(_marcador_leyenda_ida("Ruta final"))
    return entradas


def _estilo_ruta_mapa():
    """Color y leyenda del camino cuando no es ARA* anytime."""
    if ALGORITMO == "ara_star":
        return COLOR_RUTA_OFFLINE, "Ruta final (offline)"
    return COLOR_RUTA_OFFLINE, "Ruta planificada"


def celda_libre(fila, columna):
    """True si la celda es transitable o esta fuera del mapa."""
    if fila < 0 or fila >= FILAS_MAPA or columna < 0 or columna >= COLUMNAS_MAPA:
        return True
    return GRID[fila][columna] != 1


def dibujar_contorno_exterior(ax):
    """
    Borde exterior de la zona no transitable (GRID == 1: muro físico + margen).

    Cada lado de una celda bloqueada se pinta solo si el vecino de ese lado
    es libre. Asi no aparecen lineas rojas en las juntas entre muros.
    """
    segmentos = []

    for fila in range(FILAS_MAPA):
        for columna in range(COLUMNAS_MAPA):
            if GRID[fila][columna] != 1:
                continue

            x0, x1 = columna - 0.5, columna + 0.5
            y0, y1 = fila - 0.5, fila + 0.5

            if celda_libre(fila - 1, columna):
                segmentos.append([(x0, y0), (x1, y0)])
            if celda_libre(fila + 1, columna):
                segmentos.append([(x0, y1), (x1, y1)])
            if celda_libre(fila, columna - 1):
                segmentos.append([(x0, y0), (x0, y1)])
            if celda_libre(fila, columna + 1):
                segmentos.append([(x1, y0), (x1, y1)])

    if segmentos:
        ax.add_collection(
            LineCollection(
                segmentos,
                colors="red",
                linewidths=1.2,
                linestyles="--",
                zorder=5,
            )
        )


def dibujar_zonas_coste(ax):
    """Pinta cada COST_ZONE_* con su color del .wbt y resalta celdas transitables con coste."""
    for zona in ZONAS_COSTE:
        grid_info = zona.get("grid", {})
        row_ini = grid_info.get("row_ini")
        row_fin = grid_info.get("row_fin")
        col_ini = grid_info.get("col_ini")
        col_fin = grid_info.get("col_fin")
        if None in (row_ini, row_fin, col_ini, col_fin):
            continue

        color = _color_zona_mundo(zona)
        ancho = col_fin - col_ini + 1
        alto = row_fin - row_ini + 1
        ax.add_patch(
            Rectangle(
                (col_ini - 0.5, row_ini - 0.5),
                ancho,
                alto,
                facecolor=color,
                edgecolor=color,
                alpha=0.22,
                linewidth=1.2,
                zorder=3,
            )
        )

        for row, col in grid_info.get("cells", []):
            if GRID[row][col] <= 1:
                continue
            ax.add_patch(
                Rectangle(
                    (col - 0.5, row - 0.5),
                    1,
                    1,
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.72,
                    linewidth=0.8,
                    zorder=4,
                )
            )


def _leyenda_zonas_coste():
    """Una entrada por zona con su color del .wbt y coste g de config."""
    if not ZONAS_COSTE:
        return []

    _etiquetas = {
        "COST_ZONE_2": "Zona 1 azul (arriba)",
        "COST_ZONE_3": "Zona 2 verde (izquierda)",
        "COST_ZONE_4": "Zona 3 amarilla (centro)",
    }
    entradas = []
    for zona in ZONAS_COSTE:
        nombre = zona["name"]
        color = _color_zona_mundo(zona)
        coste = coste_de_zona(nombre)
        etiqueta = _etiquetas.get(nombre, nombre)
        entradas.append(
            Patch(
                facecolor=color,
                edgecolor=color,
                alpha=0.55,
                label=f"{etiqueta}: coste g = {coste:g}",
            )
        )
    return entradas


def construir_capa_terreno():
    """Capa RGB: libre (blanco), margen (gris claro), muro físico (gris oscuro)."""
    base = np.array(_GRID_BASE, dtype=bool)
    bloqueado = np.array(GRID, dtype=float) == 1

    capa = np.empty((FILAS_MAPA, COLUMNAS_MAPA, 3), dtype=float)
    capa[:] = COLOR_LIBRE

    capa[bloqueado & ~base] = COLOR_MARGEN
    capa[base] = COLOR_MURO
    return capa


def construir_camino_mision():
    rutas, nodos = planificar_mision(
        CELDA_INICIO,
        CELDAS_OBJETIVO,
        CELDA_INICIO,
        BATERIA_MAX,
        devolver_nodos=True,
    )

    camino = []
    for i, ruta in enumerate(rutas):
        if not ruta:
            continue
        camino.extend(ruta if i == 0 else ruta[1:])
    return camino, nodos, rutas


def _texto_modo_algoritmo():
    _nombres_alg = {
        "dijkstra": "Dijkstra",
        "astar": "A*",
        "greedy": "Greedy",
        "ara_star": "ARA*",
    }
    if ALGORITMO == "dijkstra":
        modo = _nombres_alg["dijkstra"]
    else:
        modo = f"{_nombres_alg.get(ALGORITMO, ALGORITMO)} + {HEURISTICA.capitalize()}"
    if ALGORITMO == "ara_star":
        if MODO_ARA == "anytime_simple":
            modo += f" | anytime ({PASOS_POR_FASE_ARA} pasos/fase)"
        else:
            modo += " | offline"
    modo += f" | costes zona={COSTE_ZONA_1:g}/{COSTE_ZONA_2:g}/{COSTE_ZONA_3:g}"
    return modo


def _leyenda_ruta_mapa(
    dibujar_ida,
    dibujar_vuelta,
    ida_vuelta_comun,
    color_ruta,
    etiqueta_ruta,
    informe_anytime,
    rutas_intermedias,
):
    if informe_anytime and dibujar_ida and not dibujar_vuelta:
        return _leyenda_rutas_anytime(rutas_intermedias)
    if dibujar_ida and dibujar_vuelta and ida_vuelta_comun:
        return [_marcador_leyenda_ida("Ruta común ida/vuelta")]
    if dibujar_ida and dibujar_vuelta:
        return [_marcador_leyenda_ida(), _marcador_leyenda_vuelta()]
    if dibujar_ida:
        return [_marcador_leyenda_ida("Ruta ida")]
    if dibujar_vuelta:
        return [_marcador_leyenda_vuelta()]
    return [
        Line2D(
            [0], [0], marker="o", color="w", markerfacecolor=color_ruta,
            markersize=12, linestyle="None", label=etiqueta_ruta,
        ),
    ]


def _dibujar_rutas_en_mapa(
    ax,
    ruta_ida,
    ruta_vuelta,
    dibujar_ida,
    dibujar_vuelta,
    color_ruta,
    informe_anytime,
    rutas_anytime,
):
    ida_vuelta_comun = son_la_misma_ruta_ida_vuelta(ruta_ida, ruta_vuelta)

    if informe_anytime and dibujar_ida and not dibujar_vuelta:
        ruta_inicial, rutas_intermedias, ruta_final = rutas_anytime
        _dibujar_circulo_ruta(
            ax, ruta_inicial, COLOR_RUTA_INICIAL, MARKER_SIZE_IDA, hueco=False, zorder=8,
        )
        for ruta in rutas_intermedias:
            _dibujar_circulo_ruta(
                ax, ruta, COLOR_RUTA_INTERMEDIA, MARKER_SIZE_IDA, hueco=False, zorder=9,
            )
        _dibujar_circulo_ruta(
            ax, ruta_final, COLOR_IDA_COMBINADO, MARKER_SIZE_IDA, hueco=False, zorder=10,
        )
        return

    if dibujar_ida and dibujar_vuelta:
        _dibujar_ruta_combinada_ida_vuelta(ax, ruta_ida, ruta_vuelta, ida_vuelta_comun)
        return

    if dibujar_ida:
        _dibujar_circulo_ruta(
            ax, ruta_ida, COLOR_IDA_COMBINADO, MARKER_SIZE_IDA, hueco=False, zorder=10,
        )
    if dibujar_vuelta:
        _dibujar_circulo_ruta(
            ax, ruta_vuelta, COLOR_VUELTA_COMBINADO, MARKER_SIZE_VUELTA, hueco=True, zorder=10,
        )


def guardar_mapa(
    capa_terreno,
    ruta_ida,
    ruta_vuelta,
    dibujar_ida,
    dibujar_vuelta,
    nombre_archivo,
    titulo_tramo,
    modo_texto,
    coste_g,
    nodos,
    len_camino,
    color_ruta,
    etiqueta_ruta,
    informe_anytime=None,
    rutas_anytime=([], [], []),
):
    """Genera un PNG; la leyenda queda fuera del mapa (margen derecho)."""
    ida_vuelta_comun = son_la_misma_ruta_ida_vuelta(ruta_ida, ruta_vuelta)
    leyenda_ruta = _leyenda_ruta_mapa(
        dibujar_ida,
        dibujar_vuelta,
        ida_vuelta_comun,
        color_ruta,
        etiqueta_ruta,
        informe_anytime,
        rutas_anytime[1],
    )

    fig, ax = plt.subplots(figsize=(11, 10))
    fig.subplots_adjust(right=0.72)

    ax.imshow(capa_terreno, origin="lower", interpolation="nearest")
    dibujar_zonas_coste(ax)
    ax.set_xticks(np.arange(-0.5, COLUMNAS_MAPA, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, FILAS_MAPA, 1), minor=True)
    ax.grid(which="minor", color="lightgray", linestyle="-", linewidth=0.25)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    dibujar_contorno_exterior(ax)

    ax.legend(
        handles=[
            Patch(facecolor=COLOR_MURO, edgecolor="none", label="Muro físico"),
            Patch(facecolor=COLOR_MARGEN, edgecolor="none", label="Margen de seguridad"),
            Line2D(
                [0], [0], color="red", linestyle="--", linewidth=1.2,
                label="Zona no transitable (muro + margen)",
            ),
            *_leyenda_zonas_coste(),
            *leyenda_ruta,
        ],
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        fontsize=8,
        framealpha=0.9,
    )

    ax.text(
        CELDA_INICIO[1], CELDA_INICIO[0], "S",
        ha="center", va="center", color="green", fontsize=20, fontweight="bold", zorder=10,
    )
    for i, (fila, columna) in enumerate(CELDAS_OBJETIVO, start=1):
        ax.text(
            columna, fila, f"G{i}",
            ha="center", va="center", color="red", fontsize=14, fontweight="bold", zorder=10,
        )

    _dibujar_rutas_en_mapa(
        ax, ruta_ida, ruta_vuelta, dibujar_ida, dibujar_vuelta,
        color_ruta, informe_anytime, rutas_anytime,
    )

    ax.set_title(
        f"{titulo_tramo} | Mapa {FILAS_MAPA}x{COLUMNAS_MAPA} | {modo_texto} | "
        f"longitud={len_camino} celdas | coste_g={coste_g:.1f} | nodos={nodos} | "
        f"objetivos={len(CELDAS_OBJETIVO)}"
    )

    plt.savefig(nombre_archivo, dpi=150, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    print(f"Mapa guardado en {nombre_archivo}")
def main():
    usar_anytime = ALGORITMO == "ara_star" and MODO_ARA == "anytime_simple"
    color_ruta, etiqueta_ruta = _estilo_ruta_mapa()
    imprimir_configuracion_planificacion()
    camino, nodos, rutas = construir_camino_mision()
    coste_g = coste_camino(camino)
    ruta_ida, ruta_vuelta = _rutas_ida_vuelta(rutas)

    informe_anytime = _informe_anytime_principal() if usar_anytime else None
    rutas_anytime = ([], [], [])
    if informe_anytime:
        rutas_anytime = _seleccionar_rutas_anytime(informe_anytime)

    if ALGORITMO == "ara_star":
        print(f"Modo ARA*: {MODO_ARA}")
        for informe in algoritmos.INFORME_ARA_MISION:
            imprimir_detalle_informe_ara(informe)

    if not camino:
        print("No se ha encontrado ruta.")

    capa_terreno = construir_capa_terreno()
    modo_texto = _texto_modo_algoritmo()
    carpeta = os.path.dirname(os.path.abspath(__file__))

    mapas = [
        ("map_ida.png", True, False, "Ruta de ida"),
        ("map_vuelta.png", False, True, "Ruta de vuelta"),
        ("map_ida_vuelta.png", True, True, "Ruta ida y vuelta"),
    ]

    for archivo, dibujar_ida, dibujar_vuelta, titulo in mapas:
        guardar_mapa(
            capa_terreno,
            ruta_ida,
            ruta_vuelta,
            dibujar_ida,
            dibujar_vuelta,
            os.path.join(carpeta, archivo),
            titulo,
            modo_texto,
            coste_g,
            nodos,
            len(camino),
            color_ruta,
            etiqueta_ruta,
            informe_anytime=informe_anytime if dibujar_ida and not dibujar_vuelta else None,
            rutas_anytime=rutas_anytime,
        )

    # Compatibilidad con nombre anterior
    origen = os.path.join(carpeta, "map_ida_vuelta.png")
    destino = os.path.join(carpeta, "map_visualization_simple.png")
    shutil.copy2(origen, destino)

    print(
        f"Resumen | longitud={len(camino)} | coste_g={coste_g:.1f} | nodos={nodos}"
    )


if __name__ == "__main__":
    main()
