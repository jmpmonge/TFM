from configuracion import config

# ============================================================================
# FUNCIONES AUXILIARES MAPA / WEBOTS
# ============================================================================

def mundo_a_rejilla(x, y):
    """
    Convierte coordenadas del mundo Webots (x, y) a celda de la rejilla (fila, col).

    Importante:
    - En Webots, y positivo está arriba.
    - En la matriz GRID, fila 0 representa la parte superior del mapa.
    - Por eso la conversión de y debe invertirse.
    """

    col = int((x - config.ORIGEN_MAPA_X) / config.CELL_SIZE)

    # y se invierte porque fila 0 es arriba
    row = int(
        ((config.ORIGEN_MAPA_Y + config.FILAS_MAPA * config.CELL_SIZE) - y) / config.CELL_SIZE
    )

    col = max(0, min(config.COLUMNAS_MAPA - 1, col))
    row = max(0, min(config.FILAS_MAPA - 1, row))

    return row, col


def centro_celda(row, col):
    """
    Devuelve el centro en coordenadas mundo de una celda (fila, col).

    fila 0 -> parte superior del mapa
    fila 6 -> parte inferior del mapa
    """

    x = config.ORIGEN_MAPA_X + col * config.CELL_SIZE + config.CENTRO_CELDA

    # Invertimos y para que fila 0 sea arriba
    y = config.ORIGEN_MAPA_Y + (config.FILAS_MAPA - 1 - row) * config.CELL_SIZE + config.CENTRO_CELDA

    return x, y


def celda_a_mundo(celda):
    """
    Alias práctico para convertir una celda (fila, col) a coordenadas Webots.
    """

    fila, col = celda
    return centro_celda(fila, col)


def es_libre(fila, col):
    """
    Devuelve True si la celda es transitable y False si es obstáculo o está fuera del mapa.
    """

    if fila < 0 or fila >= config.FILAS_MAPA:
        return False

    if col < 0 or col >= config.COLUMNAS_MAPA:
        return False

    return config.GRID[fila][col] != 1