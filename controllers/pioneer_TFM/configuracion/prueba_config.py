import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuracion.config import (
    CELL_SIZE,
    FILAS_MAPA,
    COLUMNAS_MAPA,
    CELDA_INICIO,
    CELDA_OBJETIVO,
    GRID,
    INICIO_MUNDO,
    OBJETIVO_MUNDO,
    X_LIMITS,
    Y_LIMITS,
    centro_celda,
)

print("CELL_SIZE:", CELL_SIZE)
print("FILAS_MAPA:", FILAS_MAPA, "COLUMNAS_MAPA:", COLUMNAS_MAPA)
print("LIMITS X:", X_LIMITS, "Y:", Y_LIMITS)
print("INICIO mundo:", INICIO_MUNDO, "celda:", CELDA_INICIO)
print("OBJETIVO mundo:", OBJETIVO_MUNDO, "celda:", CELDA_OBJETIVO)
print("centro celda inicio:", centro_celda(*CELDA_INICIO))
print("inicio libre:", GRID[CELDA_INICIO[0]][CELDA_INICIO[1]] == 0)
print("objetivo libre:", GRID[CELDA_OBJETIVO[0]][CELDA_OBJETIVO[1]] == 0)
