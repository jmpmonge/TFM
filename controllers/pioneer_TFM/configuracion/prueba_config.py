import os
import sys

# Al ejecutar este script directamente, Python no incluye la raíz del
# controlador en sys.path. Sin esto falla: No module named 'configuracion'.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuracion.config import (
    CELL_SIZE,
    FILAS_MAPA,
    COLUMNAS_MAPA,
    CELDA_INICIO,
    CELDA_OBJETIVO,
    GRID,
)

print("CELL_SIZE:", CELL_SIZE)
print("FILAS_MAPA:", FILAS_MAPA)
print("COLUMNAS_MAPA:", COLUMNAS_MAPA)
print("CELDA_INICIO:", CELDA_INICIO)
print("CELDA_OBJETIVO:", CELDA_OBJETIVO)
print("inicio libre:", GRID[CELDA_INICIO[0]][CELDA_INICIO[1]] == 0)
print("objetivo libre:", GRID[CELDA_OBJETIVO[0]][CELDA_OBJETIVO[1]] == 0)