import os
import sys
import time

# El script vive en herramientas/, pero los módulos del controlador
# (algoritmo.py, config.py, heuristicas.py) están en el directorio padre.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algoritmos import astar, dijkstra, greedy
from config import CELDA_INICIO, CELDA_OBJETIVO
from heuristicas import h_manhattan, h_euclidiana, h_nula


heuristicas = {
    "nula": h_nula,
    "manhattan": h_manhattan,
    "euclidiana": h_euclidiana,
}


# =========================
# EXPERIMENTO
# =========================
for nombre, h in heuristicas.items():

    inicio_t = time.time()

    camino, nodos = astar(CELDA_INICIO, CELDA_OBJETIVO, h)

    fin_t = time.time()

    longitud = len(camino)
    tiempo = fin_t - inicio_t

    print(f"{nombre:10} | longitud={longitud:3} | nodos={nodos:4} | tiempo={tiempo:.5f}")


algoritmos = {
    "Dijkstra": lambda: dijkstra(CELDA_INICIO, CELDA_OBJETIVO),
    "A*": lambda: astar(CELDA_INICIO, CELDA_OBJETIVO, h_manhattan),
    "Greedy": lambda: greedy(CELDA_INICIO, CELDA_OBJETIVO, h_manhattan),
}

for nombre, funcion in algoritmos.items():

    t0 = time.time()
    camino, nodos = funcion()
    t1 = time.time()

    print(f"{nombre:10} | len={len(camino)} | nodos={nodos} | tiempo={t1-t0:.5f}")