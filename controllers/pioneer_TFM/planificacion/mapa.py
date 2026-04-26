from configuracion.config import (
    CELL_SIZE,
    CENTRO_CELDA,
    GRID,
    ORIGEN_MAPA_X,
    ORIGEN_MAPA_Y,
    COLUMNAS_MAPA,
    FILAS_MAPA,
)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def mundo_a_celda(x, y):
    col = int((x - ORIGEN_MAPA_X) / CELL_SIZE)
    row = int((y - ORIGEN_MAPA_Y) / CELL_SIZE)

    col = max(0, min(COLUMNAS_MAPA - 1, col))
    row = max(0, min(FILAS_MAPA - 1, row))
    return row, col


def centro_celda(row, col):
    x = ORIGEN_MAPA_X + col * CELL_SIZE + CENTRO_CELDA
    y = ORIGEN_MAPA_Y + row * CELL_SIZE + CENTRO_CELDA
    return x, y


def es_libre(fila, col):
    if fila < 0 or fila >= len(GRID):
        return False
    if col < 0 or col >= len(GRID[0]):
        return False
    return GRID[fila][col]

def celda_a_mundo(celda):
    fila, col = celda
    x = ORIGEN_MAPA_X + col * CELL_SIZE + CENTRO_CELDA
    y = ORIGEN_MAPA_Y + fila * CELL_SIZE + CENTRO_CELDA
    return x, y