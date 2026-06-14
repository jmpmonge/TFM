# Construcción y consulta de la rejilla de planificación.
# No importa config.py: recibe los valores necesarios como parámetros.

import math
import re


def celda_ocupada(row, col, obs, centro_celda, cell_size, radio_obstaculo):
    """True si el centro de la celda cae dentro del obstáculo (sin margen)."""
    cx, cy = centro_celda(row, col)
    h = cell_size / 2.0

    if obs.get("type") == "box":
        ox0 = obs["x"] - obs["size_x"] / 2.0
        ox1 = obs["x"] + obs["size_x"] / 2.0
        oy0 = obs["y"] - obs["size_y"] / 2.0
        oy1 = obs["y"] + obs["size_y"] / 2.0
        return cx - h < ox1 and cx + h > ox0 and cy - h < oy1 and cy + h > oy0

    radio = obs.get("radius", radio_obstaculo)
    dx = cx - obs["x"]
    dy = cy - obs["y"]
    return math.sqrt(dx * dx + dy * dy) <= radio + h


def aplicar_margen_contorno(grid_base, filas, columnas, margen_seguridad):
    """
    Expande el muro físico una celda en rejilla (8 vecinos).
    Si margen_seguridad <= 0, no se aplica margen.
    """
    if margen_seguridad <= 0.0:
        return grid_base

    grid = [fila[:] for fila in grid_base]
    for row in range(filas):
        for col in range(columnas):
            if grid_base[row][col]:
                continue
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < filas and 0 <= nc < columnas and grid_base[nr][nc]:
                        grid[row][col] = 1
                        break
                else:
                    continue
                break
    return grid


def coste_de_zona(nombre, coste_zona_1, coste_zona_2, coste_zona_3):
    """Devuelve el coste g configurado para COST_ZONE_1, _2 o _3."""
    coincidencia = re.match(r"^COST_ZONE_(\d+)$", nombre)
    if not coincidencia:
        return 1.0
    indice = int(coincidencia.group(1))
    return {1: coste_zona_1, 2: coste_zona_2, 3: coste_zona_3}.get(indice, 1.0)


def celda_bloqueada(row, col, grid_base, grid, celdas_coste):
    """True si muro físico o margen; False si libre o zona de coste."""
    if grid_base[row][col] == 1:
        return True
    if (row, col) in celdas_coste:
        return False
    return grid[row][col] == 1


def actualizar_costes_zonas(grid, celdas_por_zona, coste_zona_1, coste_zona_2, coste_zona_3):
    """Reescribe el GRID de cada zona con los costes actuales."""
    for nombre, celdas in celdas_por_zona.items():
        coste = coste_de_zona(nombre, coste_zona_1, coste_zona_2, coste_zona_3)
        for row, col in celdas:
            grid[row][col] = coste


def construir_grid(
    obstaculos,
    zonas_coste,
    filas,
    columnas,
    margen_seguridad,
    coste_zona_1,
    coste_zona_2,
    coste_zona_3,
    centro_celda,
    cell_size,
    radio_obstaculo,
):
    # 1. Rejilla base: 0 = libre, 1 = muro físico
    grid_base = [[0 for _ in range(columnas)] for _ in range(filas)]

    # 2. Marcar celdas ocupadas por obstáculos del .wbt
    for row in range(filas):
        for col in range(columnas):
            for obs in obstaculos:
                if celda_ocupada(row, col, obs, centro_celda, cell_size, radio_obstaculo):
                    grid_base[row][col] = 1
                    break

    # 3. Margen de seguridad (dilatación 8-vecinos)
    grid = aplicar_margen_contorno(grid_base, filas, columnas, margen_seguridad)

    # 4. Zonas de coste sobre celdas libres
    celdas_por_zona = {}
    for zona in zonas_coste:
        nombre = zona["name"]
        coste = coste_de_zona(nombre, coste_zona_1, coste_zona_2, coste_zona_3)
        celdas = []
        for row, col in zona.get("grid", {}).get("cells", []):
            if grid[row][col] == 0:
                grid[row][col] = coste
                celdas.append((row, col))
        celdas_por_zona[nombre] = celdas

    celdas_coste = {
        celda
        for celdas in celdas_por_zona.values()
        for celda in celdas
    }

    return grid_base, grid, celdas_por_zona, celdas_coste
