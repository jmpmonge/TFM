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
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle
from matplotlib.transforms import ScaledTranslation
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planificacion import algoritmos
from planificacion.algoritmos import coste_camino, imprimir_detalle_informe_ara, planificar_mision
from configuracion import config
from configuracion import config_menu
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
    "COST_ZONE_1": (0.12, 0.45, 0.95),  # azul
    "COST_ZONE_2": (0.18, 0.72, 0.28),  # verde
    "COST_ZONE_3": (0.95, 0.55, 0.12),  # amarillo
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


def _coste_zona_en_grid(nombre):
    """Coste g de la leyenda: valor real del GRID (experimento.json + suelo cambiante)."""
    for row, col in config.CELDAS_POR_ZONA.get(nombre, []):
        valor = config.GRID[row][col]
        if valor > 1:
            return float(valor)
    return config.coste_de_zona(nombre)


def _leyenda_zonas_coste():
    """Una entrada por zona con su color del .wbt y coste g del GRID actual."""
    if not ZONAS_COSTE:
        return []

    _etiquetas = {
        "COST_ZONE_1": "Zona 1 azul (arriba)",
        "COST_ZONE_2": "Zona 2 verde (izquierda)",
        "COST_ZONE_3": "Zona 3 amarilla (centro)",
    }
    entradas = []
    for zona in ZONAS_COSTE:
        nombre = zona["name"]
        color = _color_zona_mundo(zona)
        coste = _coste_zona_en_grid(nombre)
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


_ESTILO_MARCO_PANEL = dict(
    facecolor="white",
    edgecolor="0.8",
    alpha=0.9,
    linewidth=0.8,
)
_FONT_PANEL = 9
_X_PANEL_IZQ = 0.0
_Y_TOPE_LEYENDA = 1.0
_SEP_MARCOS_PT = 10
_OFFSET_TEXTO_RESUMEN_PT = 4


def _eje_y_desde_puntos(puntos, ax_panel, renderer):
    """Convierte puntos tipograficos a fraccion del eje Y del panel."""
    altura_px = ax_panel.get_window_extent(renderer).height
    if altura_px <= 0:
        return puntos / 500.0
    return (puntos / 72.0) * renderer.dpi / altura_px


def _alinear_panel_con_mapa(ax, ax_panel, fig, ancho_panel=0.24, separacion=0.015):
    """Iguala altura y base del panel derecho con el eje del mapa."""
    fig.canvas.draw()
    pos_mapa = ax.get_position()
    ax_panel.set_position([
        pos_mapa.x1 + separacion,
        pos_mapa.y0,
        ancho_panel,
        pos_mapa.height,
    ])


def _lineas_resumen_mapa(titulo_tramo, len_camino, coste_g, nodos):
    """Texto del resumen: una linea por concepto."""
    _nombres_alg = {
        "dijkstra": "Dijkstra",
        "astar": "A*",
        "greedy": "Greedy",
        "ara_star": "ARA*",
    }
    if ALGORITMO == "dijkstra":
        algoritmo_txt = _nombres_alg["dijkstra"]
    else:
        algoritmo_txt = f"{_nombres_alg.get(ALGORITMO, ALGORITMO)} + {HEURISTICA.capitalize()}"

    lineas = [
        f"Tramo: {titulo_tramo}",
        f"Mapa: {FILAS_MAPA} x {COLUMNAS_MAPA}",
        f"Algoritmo: {algoritmo_txt}",
    ]

    if ALGORITMO == "ara_star":
        if MODO_ARA == "anytime_simple":
            lineas.append(f"Modo ARA*: anytime ({PASOS_POR_FASE_ARA} pasos/fase)")
        else:
            lineas.append("Modo ARA*: offline")

    lineas.extend([
        f"Costes zona: {config.COSTE_ZONA_1:g} / {config.COSTE_ZONA_2:g} / {config.COSTE_ZONA_3:g}",
        f"Longitud: {len_camino} celdas",
        f"Coste g: {coste_g:.1f}",
        f"Nodos: {nodos}",
        f"Objetivos: {len(CELDAS_OBJETIVO)}",
    ])
    return lineas


def _bbox_marco_leyenda(leyenda, ax_panel, renderer):
    return leyenda.get_frame().get_window_extent(renderer).transformed(
        ax_panel.transAxes.inverted()
    )


def _insets_verticales_leyenda(leyenda, bbox_marco, ax_panel, renderer):
    """Margenes superior e inferior del marco de leyenda."""
    textos = leyenda.get_texts()
    if not textos:
        return 0.03, 0.03

    bbox_etq = textos[0].get_window_extent(renderer).transformed(
        ax_panel.transAxes.inverted()
    )
    bbox_ult = textos[-1].get_window_extent(renderer).transformed(
        ax_panel.transAxes.inverted()
    )
    inset_sup = bbox_marco.y1 - bbox_etq.y1
    inset_inf = bbox_ult.y0 - bbox_marco.y0
    return inset_sup, inset_inf


def _x_inicio_iconos_leyenda(leyenda, bbox_marco, ax_panel, renderer):
    """X donde empiezan los dibujos de la leyenda (iconos/colores), no las etiquetas."""
    handles = getattr(leyenda, "legend_handles", None) or getattr(
        leyenda, "legendHandles", []
    )
    x_min = None
    for handle in handles:
        bbox = handle.get_window_extent(renderer).transformed(
            ax_panel.transAxes.inverted()
        )
        if x_min is None or bbox.x0 < x_min:
            x_min = bbox.x0
    if x_min is not None:
        return x_min
    return bbox_marco.x0 + 0.03


def _dibujar_panel_derecho(ax_panel, fig, handles_leyenda, lineas_resumen):
    """Leyenda y resumen con el mismo borde izquierdo y ancho de marco."""
    ax_panel.set_xlim(0, 1)
    ax_panel.set_ylim(0, 1)
    ax_panel.axis("off")

    leyenda = ax_panel.legend(
        handles=handles_leyenda,
        loc="upper left",
        bbox_to_anchor=(_X_PANEL_IZQ, _Y_TOPE_LEYENDA),
        fontsize=_FONT_PANEL,
        framealpha=_ESTILO_MARCO_PANEL["alpha"],
        edgecolor=_ESTILO_MARCO_PANEL["edgecolor"],
        facecolor=_ESTILO_MARCO_PANEL["facecolor"],
        fancybox=True,
        borderpad=0.5,
        borderaxespad=0,
        labelspacing=0.35,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox_marco = _bbox_marco_leyenda(leyenda, ax_panel, renderer)
    inset_sup, inset_inf = _insets_verticales_leyenda(
        leyenda, bbox_marco, ax_panel, renderer
    )

    sep_marcos = _eje_y_desde_puntos(_SEP_MARCOS_PT, ax_panel, renderer)
    y_tope_texto = max(0.02, bbox_marco.y0 - sep_marcos - inset_sup)
    x_texto = _x_inicio_iconos_leyenda(leyenda, bbox_marco, ax_panel, renderer)
    texto = "\n".join(lineas_resumen)
    offset_x = ScaledTranslation(_OFFSET_TEXTO_RESUMEN_PT / 72.0, 0, fig.dpi_scale_trans)

    resumen = ax_panel.text(
        x_texto,
        y_tope_texto,
        texto,
        transform=ax_panel.transAxes + offset_x,
        fontsize=_FONT_PANEL,
        va="top",
        ha="left",
        linespacing=1.35,
        zorder=3,
    )

    fig.canvas.draw()
    bbox_texto = resumen.get_window_extent(renderer).transformed(
        ax_panel.transAxes.inverted()
    )
    y_marco = bbox_texto.y0 - inset_inf
    alto_marco = (y_tope_texto + inset_sup) - y_marco

    marco_resumen = FancyBboxPatch(
        (bbox_marco.x0, y_marco),
        bbox_marco.width,
        alto_marco,
        boxstyle="round,pad=0,rounding_size=0.015",
        transform=ax_panel.transAxes,
        zorder=2,
        **_ESTILO_MARCO_PANEL,
    )
    ax_panel.add_patch(marco_resumen)


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
    coste_g,
    nodos,
    len_camino,
    color_ruta,
    etiqueta_ruta,
    informe_anytime=None,
    rutas_anytime=([], [], []),
):
    """Genera un PNG; leyenda y resumen a la derecha, alineados con el mapa."""
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

    fig, (ax, ax_panel) = plt.subplots(
        1,
        2,
        figsize=(12, 10),
        gridspec_kw={"width_ratios": [2.75, 1.2], "wspace": 0.06},
    )
    ax_panel.axis("off")

    ax.imshow(capa_terreno, origin="lower", interpolation="nearest")
    dibujar_zonas_coste(ax)
    ax.set_xticks(np.arange(-0.5, COLUMNAS_MAPA, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, FILAS_MAPA, 1), minor=True)
    ax.grid(which="minor", color="lightgray", linestyle="-", linewidth=0.25)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    dibujar_contorno_exterior(ax)

    handles_leyenda = [
        Patch(facecolor=COLOR_MURO, edgecolor="none", label="Muro físico"),
        Patch(facecolor=COLOR_MARGEN, edgecolor="none", label="Margen de seguridad"),
        Line2D(
            [0], [0], color="red", linestyle="--", linewidth=1.2,
            label="Zona no transitable (muro + margen)",
        ),
        *_leyenda_zonas_coste(),
        *leyenda_ruta,
    ]
    lineas_resumen = _lineas_resumen_mapa(titulo_tramo, len_camino, coste_g, nodos)
    _alinear_panel_con_mapa(ax, ax_panel, fig)
    _dibujar_panel_derecho(ax_panel, fig, handles_leyenda, lineas_resumen)

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

    plt.savefig(nombre_archivo, dpi=150, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    print(f"Mapa guardado en {nombre_archivo}")
def main():
    config_menu.cargar_desde_archivo(config)

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
