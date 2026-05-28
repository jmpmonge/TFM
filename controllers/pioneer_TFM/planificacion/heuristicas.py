import math

from configuracion import config


def h_nula(a, b):
    return 0

def h_manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def h_euclidiana(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def h_octil(a, b):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


HEURISTICAS_DISPONIBLES = {
    "nula": h_nula,
    "manhattan": h_manhattan,
    "euclidiana": h_euclidiana,
    "octil": h_octil,
}


def resolver_heuristica(nombre=None):
    return HEURISTICAS_DISPONIBLES[nombre or config.HEURISTICA]