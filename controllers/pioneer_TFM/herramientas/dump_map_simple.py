"""
Visualizacion sencilla de la rejilla del mapa.

Genera 'map_visualization_simple.png' con:
  - toda la cuadricula del mapa,
  - columna real en negro,
  - area de proteccion en gris muy claro,
  - linea roja de margen de seguridad,
  - camino con '*',
  - salida con 'S',
  - objetivos del JSON como 'G1', 'G2', ...

Uso:
    python dump_map_simple.py
"""

import math
import os
import sys

MPLCONFIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mpl-cache")
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", MPLCONFIGDIR)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algoritmos import planificar_mision
from config import (
    BATERIA_MAX,
    CELL_SIZE,
    CELDA_INICIO,
    CELDAS_OBJETIVO,
    COLUMNAS_MAPA,
    FILAS_MAPA,
    GRID,
    MARGEN_SEGURIDAD,
    OBSTACULOS,
    ORIGEN_MAPA_X,
    ORIGEN_MAPA_Y,
    RADIO_OBSTACULO,
)
from mapa import centro_celda


def construir_matriz():
    # Reutilizamos GRID para heredar exactamente la misma zona protegida
    # que usa la planificacion. Luego solo oscurecemos las celdas que caen
    # dentro de la columna real.
    grid_arr = np.array([[0.08 if not libre else 0.0 for libre in fila] for fila in GRID], dtype=float)

    for fila in range(FILAS_MAPA):
        for columna in range(COLUMNAS_MAPA):
            x, y = centro_celda(fila, columna)

            for obs in OBSTACULOS:
                if math.hypot(x - obs["x"], y - obs["y"]) <= RADIO_OBSTACULO:
                    grid_arr[fila, columna] = 1.0
                    break

    return grid_arr


def dibujar_texto(ax, fila, columna, texto, color, tam=6, peso="normal"):
    ax.text(
        columna,
        fila,
        texto,
        ha="center",
        va="center",
        color=color,
        fontsize=tam,
        fontweight=peso,
    )


def mundo_a_ejes(x, y):
    x_grid = (x - ORIGEN_MAPA_X) / CELL_SIZE - 0.5
    y_grid = (y - ORIGEN_MAPA_Y) / CELL_SIZE - 0.5
    return x_grid, y_grid


def dibujar_obstaculos_reales(ax):
    radio_real_grid = RADIO_OBSTACULO / CELL_SIZE
    radio_seguridad_grid = (RADIO_OBSTACULO + MARGEN_SEGURIDAD) / CELL_SIZE

    for obs in OBSTACULOS:
        x_grid, y_grid = mundo_a_ejes(obs["x"], obs["y"])

        ax.add_patch(
            Circle(
                (x_grid, y_grid),
                radio_real_grid,
                facecolor="black",
                edgecolor="black",
                linewidth=0.8,
                alpha=0.9,
                zorder=4,
            )
        )
        ax.add_patch(
            Circle(
                (x_grid, y_grid),
                radio_seguridad_grid,
                fill=False,
                edgecolor="red",
                linewidth=1.0,
                linestyle="--",
                alpha=0.9,
                zorder=5,
            )
        )


def construir_camino_mision():
    rutas = planificar_mision(CELDA_INICIO, CELDAS_OBJETIVO, CELDA_INICIO, BATERIA_MAX)
    camino = []

    for i, ruta in enumerate(rutas):
        if not ruta:
            continue
        if i == 0:
            camino.extend(ruta)
        else:
            camino.extend(ruta[1:])

    return camino


def main():
    camino_celdas = construir_camino_mision()
    grid_arr = construir_matriz()

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(grid_arr, cmap="gray_r", origin="lower", interpolation="nearest", vmin=0.0, vmax=1.0)

    ax.set_xticks(np.arange(-0.5, COLUMNAS_MAPA, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, FILAS_MAPA, 1), minor=True)
    ax.grid(which="minor", color="lightgray", linestyle="-", linewidth=0.25)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    dibujar_obstaculos_reales(ax)

    for fila, columna in camino_celdas:
        if (fila, columna) != CELDA_INICIO and (fila, columna) not in CELDAS_OBJETIVO:
            dibujar_texto(ax, fila, columna, "*", "royalblue", tam=5, peso="bold")

    dibujar_texto(ax, CELDA_INICIO[0], CELDA_INICIO[1], "S", "green", tam=25, peso="bold")
    for i, celda_objetivo in enumerate(CELDAS_OBJETIVO, start=1):
        dibujar_texto(ax, celda_objetivo[0], celda_objetivo[1], f"G{i}", "red", tam=15, peso="bold")

    if not camino_celdas:
        print("No se ha encontrado ruta para la mision.")

    ax.set_title(
        f"Mapa simple {FILAS_MAPA}x{COLUMNAS_MAPA} | cell={CELL_SIZE} m | "
        f"objetivos={len(CELDAS_OBJETIVO)} | ruta={len(camino_celdas)} celdas"
    )

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_visualization_simple.png")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close(fig)
    print("Mapa guardado en", out)


if __name__ == "__main__":
    main()
