import os
import sys
import time

# El script vive en herramientas/, pero los módulos del controlador
# (algoritmo.py, config.py, heuristicas.py) están en el directorio padre.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algoritmos import a_estrella
from config import CELDA_INICIO, CELDA_OBJETIVO
from mapa import celda_a_mundo
from heuristicas import h_manhattan, h_euclidiana, heuristica_ponderada, heuristica_energia


heuristicas = {
    "manhattan": h_manhattan,
    "euclidiana": h_euclidiana,
    "energia": heuristica_energia,
    "ponderada": heuristica_ponderada
}


# =========================
# EXPERIMENTO
# =========================
for nombre, h in heuristicas.items():

    inicio_t = time.time()

    camino, nodos = a_estrella(celda_a_mundo(CELDA_INICIO), celda_a_mundo(CELDA_OBJETIVO), h)

    fin_t = time.time()

    longitud = len(camino)
    tiempo = fin_t - inicio_t

    print(f"{nombre:10} | longitud={longitud:3} | nodos={nodos:4} | tiempo={tiempo:.5f}")


algoritmos = {
    "A*": lambda: a_estrella(celda_a_mundo(CELDA_INICIO), celda_a_mundo(CELDA_OBJETIVO), h_manhattan),
}

for nombre, funcion in algoritmos.items():

    t0 = time.time()
    camino, nodos = funcion()
    t1 = time.time()

    print(f"{nombre:10} | len={len(camino)} | nodos={nodos} | tiempo={t1-t0:.5f}")