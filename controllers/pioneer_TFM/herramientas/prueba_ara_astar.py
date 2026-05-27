"""
Comparacion A* vs ARA* en el mapa actual.

Uso:
    python3 controllers/pioneer_TFM/herramientas/prueba_ara_astar.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuracion import config
from planificacion import algoritmos
from planificacion.algoritmos import (
    ara_star,
    astar,
    coste_camino,
    imprimir_tabla_iteraciones_ara,
)
from planificacion.heuristicas import resolver_heuristica


def main():
    inicio = config.CELDA_INICIO
    objetivo = config.CELDA_OBJETIVO
    heuristica = resolver_heuristica("manhattan")

    print()
    print("=" * 45)
    print("PRUEBA: A* vs ARA*")
    print("=" * 45)
    print("Mapa     :", f"{config.FILAS_MAPA} x {config.COLUMNAS_MAPA}")
    print("Inicio   :", inicio)
    print("Objetivo :", objetivo)
    print("Heuristica: 📐 Manhattan")
    print()

    t0 = time.perf_counter()
    ruta_astar, nodos_astar = astar(inicio, objetivo, heuristica)
    tiempo_astar = time.perf_counter() - t0

    print("A* (epsilon = 1)")
    print("  pasos :", coste_camino(ruta_astar))
    print("  nodos :", nodos_astar)
    print("  tiempo:", f"{tiempo_astar:.4f} s")
    print("  celdas:", len(ruta_astar))
    print()

    ruta_ara, nodos_ara = ara_star(inicio, objetivo, heuristica)

    print("ARA*")
    print(
        f"  epsilon: {config.EPSILON_INICIAL_ARA} -> {config.EPSILON_FINAL_ARA} "
        f"(paso {config.EPSILON_PASO_ARA})"
    )
    print()

    informe = algoritmos.ULTIMO_INFORME_ARA
    if informe:
        imprimir_tabla_iteraciones_ara(informe)
        iters = informe["iteraciones"]
        pasos_ini = coste_camino(iters[0]["ruta"]) if iters else 0
        pasos_fin = coste_camino(informe["ruta_final"])
        print()
        print("  pasos primera iteracion:", pasos_ini)
        print("  pasos ruta final       :", pasos_fin)
        print("  nodos totales          :", nodos_ara)
        print("  celdas finales         :", len(ruta_ara))

    print()
    print("Comparacion")
    print("  delta pasos (ARA* - A*):", coste_camino(ruta_ara) - coste_camino(ruta_astar))
    print("  delta nodos (ARA* - A*):", nodos_ara - nodos_astar)
    print("=" * 45)
    print()


if __name__ == "__main__":
    main()
