from config import (
    CELL_SIZE,
    CENTRO_CELDA,
    CELDA_INICIO,
    CELDA_OBJETIVO,
    COLUMNAS_MAPA,
    FILAS_MAPA,
    GRID,
    INICIO_MUNDO,
    MARGEN_SEGURIDAD,
    OBJETIVO_MUNDO,
    OBSTACULOS,
    ORIGEN_MAPA_X,
    ORIGEN_MAPA_Y,
    RADIO_OBSTACULO,
    X_LIMITS,
    Y_LIMITS,
    centro_celda as _centro_celda,
    mundo_a_celda as _mundo_a_celda,
)


def es_libre(fila, col):
    if fila < 0 or fila >= len(GRID):
        return False
    if col < 0 or col >= len(GRID[0]):
        return False
    return GRID[fila][col]


def mundo_a_celda(x, y):
    return _mundo_a_celda(x, y)


def centro_celda(fila, col):
    return _centro_celda(fila, col)


def celda_a_mundo(celda):
    fila, col = celda
    x = ORIGEN_MAPA_X + col * CELL_SIZE + CENTRO_CELDA
    y = ORIGEN_MAPA_Y + fila * CELL_SIZE + CENTRO_CELDA
    return x, y
