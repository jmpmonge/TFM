from configuracion import config


def h_nula(a, b):
    return 0

def h_manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def h_euclidiana(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


HEURISTICAS_DISPONIBLES = {
    "nula": h_nula,
    "manhattan": h_manhattan,
    "euclidiana": h_euclidiana,
}


def resolver_heuristica(nombre=None):
    return HEURISTICAS_DISPONIBLES[nombre or config.HEURISTICA]