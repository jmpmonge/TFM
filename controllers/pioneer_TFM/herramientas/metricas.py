import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planificacion.algoritmos import ara_star, astar, dijkstra, greedy
from configuracion.config import CELDA_INICIO, CELDA_OBJETIVO
from planificacion.heuristicas import h_manhattan, h_euclidiana, h_octil, h_nula


heuristicas = {
    "nula": h_nula,
    "manhattan": h_manhattan,
    "euclidiana": h_euclidiana,
    "octil": h_octil,
}


print("A* por heuristica (inicio -> objetivo)")
for nombre, h in heuristicas.items():
    camino, nodos = astar(CELDA_INICIO, CELDA_OBJETIVO, h)
    print(f"{nombre:10} | celdas={len(camino):3} | nodos={nodos:4}")

print()
print("Comparacion de algoritmos (Manhattan)")

algoritmos = {
    "Dijkstra": lambda: dijkstra(CELDA_INICIO, CELDA_OBJETIVO),
    "A*": lambda: astar(CELDA_INICIO, CELDA_OBJETIVO, h_manhattan),
    "Greedy": lambda: greedy(CELDA_INICIO, CELDA_OBJETIVO, h_manhattan),
    "ARA*": lambda: ara_star(CELDA_INICIO, CELDA_OBJETIVO, h_manhattan),
}

for nombre, funcion in algoritmos.items():
    camino, nodos = funcion()
    print(f"{nombre:10} | celdas={len(camino):3} | nodos={nodos:4}")
