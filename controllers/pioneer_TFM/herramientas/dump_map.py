"""
Volcado visual del mapa que ve A*.

Genera 'map_visualization.png' con:
  - Celdas LIBRES en blanco, BLOQUEADAS en negro (paredes + cilindros + margen).
  - Cilindros originales como circunferencias rojas (referencia).
  - START en verde, GOAL en rojo.
  - Ruta A* superpuesta en azul.

Uso (desde el directorio del controlador):
    python dump_map.py
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

# El script vive en herramientas/, los módulos del controlador están en el dir padre.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuracion.config import HEURISTICA, CELL_SIZE, MARGEN_SEGURIDAD, INICIO_MUNDO, OBJETIVO_MUNDO, X_LIMITS, Y_LIMITS, OBSTACULOS, RADIO_OBSTACULO, FILAS_MAPA, COLUMNAS_MAPA, CELDA_INICIO, CELDA_OBJETIVO
from planificacion.algoritmos import preparar_ruta_desde_config
from planificacion.mapa import celda_a_mundo
from configuracion.config import GRID

def main():
    camino_celdas, _, _, _ = preparar_ruta_desde_config(HEURISTICA)

    grid_arr = np.array(
        [[0 if libre else 1 for libre in fila] for fila in GRID],
        dtype=np.uint8,
    )

    fig, ax = plt.subplots(figsize=(10, 10))

    ax.imshow(
        grid_arr,
        cmap="gray_r",
        extent=(X_LIMITS[0], X_LIMITS[1], Y_LIMITS[0], Y_LIMITS[1]),
        origin="lower",
        interpolation="nearest",
        alpha=0.85,
    )

    # cilindros originales (sin inflar) como círculos rojos
    for obs in OBSTACULOS:
        c = Circle(
            (obs["x"], obs["y"]),
            RADIO_OBSTACULO,
            fill=False,
            edgecolor="red",
            linewidth=1.0,
        )
        ax.add_patch(c)

    # mismos cilindros pero con margen, en rojo claro discontinuo
    for obs in OBSTACULOS:
        c = Circle(
            (obs["x"], obs["y"]),
            RADIO_OBSTACULO + MARGEN_SEGURIDAD,
            fill=False,
            edgecolor="red",
            linewidth=0.6,
            linestyle="--",
            alpha=0.5,
        )
        ax.add_patch(c)

    # ruta A*
    if camino_celdas:
        xs, ys = zip(*[celda_a_mundo(celda) for celda in camino_celdas])
        ax.plot(xs, ys, color="blue", linewidth=1.5, label=f"Ruta A* ({len(camino_celdas)} celdas)")
    else:
        ax.text(
            (X_LIMITS[0] + X_LIMITS[1]) / 2,
            (Y_LIMITS[0] + Y_LIMITS[1]) / 2,
            "SIN RUTA",
            color="red", ha="center", va="center", fontsize=20,
        )

    ax.scatter([INICIO_MUNDO[0]],   [INICIO_MUNDO[1]],   c="green", s=120, marker="o", label="START", zorder=5)
    ax.scatter([OBJETIVO_MUNDO[0]], [OBJETIVO_MUNDO[1]], c="red",   s=120, marker="*", label="GOAL",  zorder=5)

    ax.set_xlim(X_LIMITS)
    ax.set_ylim(Y_LIMITS)
    ax.set_aspect("equal")
    ax.set_title(
        f"Grid {FILAS_MAPA}x{COLUMNAS_MAPA}  |  cell={CELL_SIZE} m  |  margen={MARGEN_SEGURIDAD} m\n"
        f"Obstáculos: {len(OBSTACULOS)}   Bloqueadas: {int(grid_arr.sum())}/{grid_arr.size} celdas"
    )
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.legend(loc="lower left")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_visualization.png")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    print("Mapa guardado en", out)
    print("CELDA_INICIO   =", CELDA_INICIO)
    print("CELDA_OBJETIVO =", CELDA_OBJETIVO)
    print("Ruta A*        =", len(camino_celdas), "celdas")


if __name__ == "__main__":
    main()
