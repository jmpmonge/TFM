# heuristicas.py

from config import HEURISTICA

def h_manhattan(a, b): 
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) 


def h_euclidiana(a, b):
    return ((a[0] - b[0])**2 + (a[1] - b[1])**2) ** 0.5



def h_nula(a, b):
    return 0


def heuristica_energia(a, b):
    distancia = abs(a[0] - b[0]) + abs(a[1] - b[1])
    return 0.3 * distancia  # peso energético


def heuristica_ponderada(a, b):
    return h_manhattan(a, b)



HEURISTICAS_DISPONIBLES = {
    "manhattan": h_manhattan,
    "euclidiana": h_euclidiana,
    "nula": h_nula,
    "energia": heuristica_energia,
    "ponderada": heuristica_ponderada,
}
