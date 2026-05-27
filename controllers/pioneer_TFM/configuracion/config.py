import json
import math
import os
import pathlib

# Ruta del directorio donde vive este propio config.py. Usándola siempre como
# base hacemos que los ficheros de datos (generated_map.json, etc.) se
# encuentren independientemente del CWD desde el que se lance Python.
_AQUI = pathlib.Path(__file__).parent

# ============================================================================
# PARAMETROS GENERALES
# ============================================================================

TIEMPO_PASO = 32 # 32ms (velocidad de lectura de cada paso)  
VELOCIDAD_AVANCE = 6.4 # Velocidad de avance en m/s, máxima 6.4 m/s
VELOCIDAD_GIRO = 6.0 # Velocidad de giro en rad/s, máxima 6.4 rad/s    
RUEDAS = 0.0975 # Radio de las ruedas en m
DISTANCIA_EJES = 0.325 # Distancia entre las ruedas en m

# Algoritmo de planificacion activo.
ALGORITMO = "astar"

# Heurística que usa A* para estimar lo que falta hasta el goal.
# Opciones: "manhattan" | "euclidiana" | "cero" (Dijkstra) | "agresiva" (greedy)
HEURISTICA = "manhattan"

# Parámetros de ARA* (ε = peso de la heurística en cada iteración)
# ε alto  → ruta más rápida de calcular
# ε = 1.0 → mismo criterio que A* normal
EPSILON_INICIAL_ARA = 2.5
EPSILON_FINAL_ARA = 1.0
EPSILON_PASO_ARA = 0.5

# Peso fijo del A* ponderado en comparativas: f(n) = g(n) + epsilon * h(n)
PESO_ASTAR_PONDERADO = 1.5

# ============================================================================
# AJUSTES DEL MAPA
# ============================================================================
# Tamaño de cada celda en metros.

# En terreno de 7x7 metros, cada celda es de 1 metro de lado.
CELL_SIZE = 1

# El robot es ~0.5 m y queremos que ocupe 3x3 celdas → 0.5 / 3 ≈ 0.17 m
# CELL_SIZE = 0.17
CENTRO_CELDA = CELL_SIZE / 2

# para mapa 7x7
OBSTACLE_RADIUS = 0.0 # Radio de los obstáculos en metros∫
MARGEN_SEGURIDAD = 0.0
# para mapa amplio
# OBSTACLE_RADIUS = 0.4 # Radio de los obstáculos en metros∫
# MARGEN_SEGURIDAD = 0.6 # Margen extra para no rozar columnas en metros

# Valores por defecto si el JSON no trae start/goals (mapa ARA* 7×7 clásico).
INICIO_MUNDO_POR_DEFECTO = (3.0, -3.0)
OBJETIVOS_MUNDO_POR_DEFECTO = [
    (-3.0, 3.0),
]
BATERIA_MAX = 800 # NÚMERO DE UNIDADES DE BATERÍA, 1 UNIDAD = PASO DE 32ms

# ============================================================================
# SINCRONIZAR Y LEER MAPA DESDE JSON
# Si pioneer3at.wbt cambió, se regenera generated_map.json al importar config.
# ============================================================================
import sys

_CONTROLLER_DIR = _AQUI.parent
if str(_CONTROLLER_DIR) not in sys.path:
    sys.path.insert(0, str(_CONTROLLER_DIR))

from herramientas.extract_wbt_to_json import sincronizar_si_necesario

_JSON_MAPA = _AQUI / "generated_map.json"
if sincronizar_si_necesario(verbose=False):
    print("[config] Mapa actualizado desde worlds/pioneer3at.wbt")

with open(_JSON_MAPA, "r", encoding="utf-8") as f:
    mapa = json.load(f)

X_LIMITS = mapa["x_limits"]          # por ejemplo [-30.0, 30.0]
Y_LIMITS = mapa["y_limits"]          # por ejemplo [-30.0, 30.0]
RADIO_OBSTACULO = mapa["obstacle_radius"] # Radio de los obstáculos en metros
OBSTACULOS = mapa["obstacles"]        # diccionario de {"name": ..., "x": ..., "y": ...}
GOALS = mapa.get("goals", [])
START = mapa.get("start")

if START:
    INICIO_MUNDO = (START["x"], START["y"])
else:
    INICIO_MUNDO = INICIO_MUNDO_POR_DEFECTO

if GOALS:
    OBJETIVOS_MUNDO = [(goal["x"], goal["y"]) for goal in GOALS]
else:
    OBJETIVOS_MUNDO = OBJETIVOS_MUNDO_POR_DEFECTO

OBJETIVO_MUNDO = OBJETIVOS_MUNDO[0] # Compatibilidad con código que aún usa un único objetivo

ORIGEN_MAPA_X = X_LIMITS[0] # Coordenada X del origen del mapa
ORIGEN_MAPA_Y = Y_LIMITS[0] # Coordenada Y del origen del mapa

ANCHO_MAPA = X_LIMITS[1] - X_LIMITS[0] # Ancho del mapa en metros
ALTO_MAPA = Y_LIMITS[1] - Y_LIMITS[0] # Alto del mapa en metros

COLUMNAS_MAPA = int(ANCHO_MAPA / CELL_SIZE) # Número de columnas del mapa
FILAS_MAPA = int(ALTO_MAPA / CELL_SIZE) # Número de filas del mapa


# ============================================================================
# FUNCIONES AUXILIARES
# Definidas aquí (y no en planificacion/mapa.py) para evitar import circular:
# config.py las usa internamente al construir la rejilla y al calcular las
# celdas de inicio/objetivo. mapa.py replica las mismas funciones para que el
# resto del proyecto las consuma desde la capa de planificación.
# ============================================================================

def mundo_a_rejilla(x, y):
    """Misma convención que planificacion/mapa.py (fila 0 = parte superior)."""
    col = int((x - ORIGEN_MAPA_X) / CELL_SIZE)
    row = int(((ORIGEN_MAPA_Y + FILAS_MAPA * CELL_SIZE) - y) / CELL_SIZE)
    col = max(0, min(COLUMNAS_MAPA - 1, col))
    row = max(0, min(FILAS_MAPA - 1, row))
    return row, col


def centro_celda(row, col):
    x = ORIGEN_MAPA_X + col * CELL_SIZE + CENTRO_CELDA
    y = ORIGEN_MAPA_Y + (FILAS_MAPA - 1 - row) * CELL_SIZE + CENTRO_CELDA
    return x, y


# ============================================================================
# CREAR REJILLA
# 0 = celda libre, 1 = celda ocupada (muro del laberinto)
# ============================================================================
GRID = [[0 for _ in range(COLUMNAS_MAPA)] for _ in range(FILAS_MAPA)]

# No se marca borde exterior: el mapa lógico es 7×7 y los muros vienen del JSON.
# La arena Webots 8×8 es solo margen visual fuera de este grid.

for row in range(FILAS_MAPA):
    for col in range(COLUMNAS_MAPA):
        x, y = centro_celda(row, col)

        for obs in OBSTACULOS:

            tipo = obs.get("type", "cylinder")

            # ------------------------------------------------------------
            # CASO 1: MURO RECTANGULAR / BOX
            # ------------------------------------------------------------
            if tipo == "box":
                margen = MARGEN_SEGURIDAD

                mitad_x = obs["size_x"] / 2.0
                mitad_y = obs["size_y"] / 2.0

                dentro_x = abs(x - obs["x"]) <= (mitad_x + margen)
                dentro_y = abs(y - obs["y"]) <= (mitad_y + margen)

                if dentro_x and dentro_y:
                    GRID[row][col] = 1
                    break

            # ------------------------------------------------------------
            # CASO 2: OBSTÁCULO CIRCULAR / CYLINDER
            # ------------------------------------------------------------
            else:
                radio = obs.get("radius", RADIO_OBSTACULO)
                radio_total = radio + MARGEN_SEGURIDAD

                dx = x - obs["x"]
                dy = y - obs["y"]
                dist = math.sqrt(dx * dx + dy * dy)

                if dist <= radio_total:
                    GRID[row][col] = 1
                    break

# ============================================================================
# COMPROBAR START Y GOAL
# ============================================================================
CELDA_INICIO = mundo_a_rejilla(INICIO_MUNDO[0], INICIO_MUNDO[1])
CELDA_OBJETIVO = mundo_a_rejilla(OBJETIVO_MUNDO[0], OBJETIVO_MUNDO[1])
CELDAS_OBJETIVO = [mundo_a_rejilla(x, y) for x, y in OBJETIVOS_MUNDO]

if GRID[CELDA_INICIO[0]][CELDA_INICIO[1]] != 0:
    raise ValueError(f"INICIO_MUNDO cae dentro de obstáculo: {INICIO_MUNDO} -> {CELDA_INICIO}")

if GRID[CELDA_OBJETIVO[0]][CELDA_OBJETIVO[1]] != 0:
    raise ValueError(f"OBJETIVO_MUNDO cae dentro de obstáculo: {OBJETIVO_MUNDO} -> {CELDA_OBJETIVO}")

for objetivo_mundo, celda_objetivo in zip(OBJETIVOS_MUNDO, CELDAS_OBJETIVO):
    if GRID[celda_objetivo[0]][celda_objetivo[1]] != 0:
        raise ValueError(f"Objetivo cae dentro de obstáculo: {objetivo_mundo} -> {celda_objetivo}")