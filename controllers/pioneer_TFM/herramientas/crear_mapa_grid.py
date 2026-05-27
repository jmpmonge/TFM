"""
Visualiza la rejilla GRID y la ruta planificada.

Genera map_visualization_simple.png con muros, contorno rojo, S, G y camino.

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
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planificacion.algoritmos import planificar_mision
from configuracion.config import (
    BATERIA_MAX,
    CELDA_INICIO,
    CELDAS_OBJETIVO,
    COLUMNAS_MAPA,
    FILAS_MAPA,
    GRID,
)


def celda_libre(fila, columna):
    """True si la celda es transitable o esta fuera del mapa."""
    if fila < 0 or fila >= FILAS_MAPA or columna < 0 or columna >= COLUMNAS_MAPA:
        return True
    return GRID[fila][columna] == 0


def dibujar_contorno_exterior(ax):
    """
    Dibuja solo el borde exterior de la zona no transitable.

    Cada lado de una celda bloqueada se pinta solo si el vecino de ese lado
    es libre. Asi no aparecen lineas rojas en las juntas entre muros.
    """
    segmentos = []

    for fila in range(FILAS_MAPA):
        for columna in range(COLUMNAS_MAPA):
            if GRID[fila][columna] == 0:
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


def construir_camino_mision():
    rutas = planificar_mision(
        CELDA_INICIO,
        CELDAS_OBJETIVO,
        CELDA_INICIO,
        BATERIA_MAX,
    )

    camino = []
    for i, ruta in enumerate(rutas):
        if not ruta:
            continue
        camino.extend(ruta if i == 0 else ruta[1:])
    return camino


def main():
    camino = construir_camino_mision()
    grid_arr = np.array(GRID, dtype=float)

    fig, ax = plt.subplots(figsize=(10, 10))

    ax.imshow(
        grid_arr,
        cmap="gray_r",
        origin="lower",
        interpolation="nearest",
        vmin=0.0,
        vmax=1.0,
    )

    ax.set_xticks(np.arange(-0.5, COLUMNAS_MAPA, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, FILAS_MAPA, 1), minor=True)
    ax.grid(which="minor", color="lightgray", linestyle="-", linewidth=0.25)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)

    dibujar_contorno_exterior(ax)

    for fila, columna in camino:
        if (fila, columna) != CELDA_INICIO and (fila, columna) not in CELDAS_OBJETIVO:
            ax.text(columna, fila, "*", ha="center", va="center", color="royalblue",
                    fontsize=20, fontweight="bold", zorder=10)

    ax.text(CELDA_INICIO[1], CELDA_INICIO[0], "S", ha="center", va="center",
            color="green", fontsize=20, fontweight="bold", zorder=10)

    for i, (fila, columna) in enumerate(CELDAS_OBJETIVO, start=1):
        ax.text(columna, fila, f"G{i}", ha="center", va="center",
                color="red", fontsize=14, fontweight="bold", zorder=10)

    if not camino:
        print("No se ha encontrado ruta.")

    ax.set_title(
        f"Mapa {FILAS_MAPA}x{COLUMNAS_MAPA} | ruta={len(camino)} celdas | "
        f"objetivos={len(CELDAS_OBJETIVO)}"
    )

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_visualization_simple.png")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close(fig)
    print("Mapa guardado en", out)


if __name__ == "__main__":
    main()
