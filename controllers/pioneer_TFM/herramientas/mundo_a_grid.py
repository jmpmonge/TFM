"""
Visualiza la rejilla GRID y la ruta planificada.

Genera map_visualization_simple.png con muros (gris oscuro), margen de
seguridad (gris claro), contorno rojo (zona no transitable: muro + margen),
S, G y camino.

Si ALGORITMO == "ara_star", el camino depende de MODO_ARA en config.py:
  - offline: ruta final (azul)
  - anytime_simple: ruta ejecutada por fases (naranja)

Uso:
    python3 controllers/pioneer_TFM/herramientas/mundo_a_grid.py
"""

import os
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
    COSTE_ZONA_AZUL,
    ZONAS_COSTE,
    _GRID_BASE,
)

COLOR_LIBRE = (1.0, 1.0, 1.0)
COLOR_MARGEN = (0.82, 0.82, 0.82)
COLOR_MURO = (0.15, 0.15, 0.15)
COLOR_ZONA_COSTE = (0.12, 0.45, 0.95)
COLOR_RUTA_OFFLINE = "royalblue"
COLOR_RUTA_ANYTIME = "darkorange"


def _estilo_ruta_mapa():
    """Color y leyenda del camino segun algoritmo y MODO_ARA."""
    if ALGORITMO == "ara_star" and MODO_ARA == "anytime_simple":
        return COLOR_RUTA_ANYTIME, "Ruta ejecutada (anytime)"
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
    """Pinta el rectángulo lógico de cada COST_ZONE_* y resalta celdas transitables con coste."""
    for zona in ZONAS_COSTE:
        grid_info = zona.get("grid", {})
        row_ini = grid_info.get("row_ini")
        row_fin = grid_info.get("row_fin")
        col_ini = grid_info.get("col_ini")
        col_fin = grid_info.get("col_fin")
        if None in (row_ini, row_fin, col_ini, col_fin):
            continue

        ancho = col_fin - col_ini + 1
        alto = row_fin - row_ini + 1
        ax.add_patch(
            Rectangle(
                (col_ini - 0.5, row_ini - 0.5),
                ancho,
                alto,
                facecolor=COLOR_ZONA_COSTE,
                edgecolor=COLOR_ZONA_COSTE,
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
                    facecolor=COLOR_ZONA_COSTE,
                    edgecolor=COLOR_ZONA_COSTE,
                    alpha=0.72,
                    linewidth=0.8,
                    zorder=4,
                )
            )


def _leyenda_zonas_coste():
    """Coste de la zona azul: lee COSTE_ZONA_AZUL de config.py."""
    if not ZONAS_COSTE:
        return []

    return [
        Patch(
            facecolor=COLOR_ZONA_COSTE,
            edgecolor=COLOR_ZONA_COSTE,
            alpha=0.55,
            label=f"Zona de coste (azul): coste = {COSTE_ZONA_AZUL:g}",
        )
    ]


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
    return camino, nodos


def main():
    color_ruta, etiqueta_ruta = _estilo_ruta_mapa()
    camino, nodos = construir_camino_mision()
    coste_g = coste_camino(camino)

    if ALGORITMO == "ara_star":
        print(f"Modo ARA*: {MODO_ARA}")
        for informe in algoritmos.INFORME_ARA_MISION:
            imprimir_detalle_informe_ara(informe)

    capa_terreno = construir_capa_terreno()

    fig, ax = plt.subplots(figsize=(10, 10))

    ax.imshow(
        capa_terreno,
        origin="lower",
        interpolation="nearest",
    )

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
                [0],
                [0],
                color="red",
                linestyle="--",
                linewidth=1.2,
                label="Zona no transitable (muro + margen)",
            ),
            *_leyenda_zonas_coste(),
            Line2D(
                [0],
                [0],
                marker="*",
                color="w",
                markerfacecolor=color_ruta,
                markersize=12,
                linestyle="None",
                label=etiqueta_ruta,
            ),
        ],
        loc="upper right",
        fontsize=8,
        framealpha=0.9,
    )

    for fila, columna in camino:
        if (fila, columna) != CELDA_INICIO and (fila, columna) not in CELDAS_OBJETIVO:
            ax.text(columna, fila, "*", ha="center", va="center", color=color_ruta,
                    fontsize=20, fontweight="bold", zorder=10)

    ax.text(CELDA_INICIO[1], CELDA_INICIO[0], "S", ha="center", va="center",
            color="green", fontsize=20, fontweight="bold", zorder=10)

    for i, (fila, columna) in enumerate(CELDAS_OBJETIVO, start=1):
        ax.text(columna, fila, f"G{i}", ha="center", va="center",
                color="red", fontsize=14, fontweight="bold", zorder=10)

    if not camino:
        print("No se ha encontrado ruta.")

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
            modo += " | ruta ejecutada (anytime)"
        else:
            modo += " | ruta final (offline)"

    ax.set_title(
        f"Mapa {FILAS_MAPA}x{COLUMNAS_MAPA} | {modo} | "
        f"longitud={len(camino)} celdas | coste_g={coste_g:.1f} | nodos={nodos} | "
        f"objetivos={len(CELDAS_OBJETIVO)}"
    )

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_visualization_simple.png")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close(fig)
    print(
        f"Mapa guardado en {out} | longitud={len(camino)} | coste_g={coste_g:.1f} | nodos={nodos}"
    )


if __name__ == "__main__":
    main()
