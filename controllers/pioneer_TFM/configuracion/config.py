import json
import math
import os

# Ruta del directorio donde vive este propio config.py. Usándola siempre como
# base hacemos que los ficheros de datos (generated_map.json, etc.) se
# encuentren independientemente del CWD desde el que se lance Python.
_AQUI = os.path.dirname(os.path.abspath(__file__))

# ============================================================================
# PARAMETROS GENERALES
# ============================================================================

TIEMPO_PASO = 32 # 32ms (velocidad de lectura de cada paso)  
VELOCIDAD_AVANCE = 6.4 # Velocidad de avance en m/s, máxima 6.4 m/s
VELOCIDAD_GIRO = 2.0 # Velocidad de giro en rad/s, máxima 12.4 rad/s    
RADIO_RUEDA = 0.0975 # Radio de las ruedas en m
DISTANCIA_EJES = 0.325 # Distancia entre las ruedas en m


# Algoritmo de planificacion activo.
ALGORITMO = "astar"

# Heurística que usa A* para estimar lo que falta hasta el goal.
# Opciones: "manhattan" | "euclidiana" | "cero" (Dijkstra) | "agresiva" (greedy)
HEURISTICA = "manhattan"

# ============================================================================
# AJUSTES DEL MAPA
# ============================================================================
# Tamaño de cada celda en metros.
# El robot es ~0.5 m y queremos que ocupe 3x3 celdas → 0.5 / 3 ≈ 0.17 m
CELL_SIZE = 0.17
CENTRO_CELDA = CELL_SIZE / 2


# Margen extra para no rozar columnas en metros
MARGEN_SEGURIDAD = 0.6 

# Punto inicial en coordenadas del mundo (plano X-Y)
INICIO_MUNDO = (15.16, -2.61) # Coordenadas del punto inicial en metros
OBJETIVOS_MUNDO_POR_DEFECTO = [
    (25.0, 25.0),
    (-25.0, 25.0),
    (25.0, -25.0),
    (-25.0, -25.0),
] # Fallback por si el JSON aún no incluye los objetivos
BATERIA_MAX = 800 # NÚMERO DE UNIDADES DE BATERÍA, 1 UNIDAD = PASO DE 32ms


# ============================================================================
# LEER JSON MINIMO
# ============================================================================
with open(os.path.join(_AQUI, "generated_map.json"), "r", encoding="utf-8") as f: # Abre el archivo JSON
    mapa = json.load(f) # Carga el mapa desde el archivo JSON

X_LIMITS = mapa["x_limits"]          # por ejemplo [-30.0, 30.0]
Y_LIMITS = mapa["y_limits"]          # por ejemplo [-30.0, 30.0]
RADIO_OBSTACULO = mapa["obstacle_radius"] # Radio de los obstáculos en metros
OBSTACULOS = mapa["obstacles"]        # lista de {"name": ..., "x": ..., "y": ...}
GOALS = mapa.get("goals", [])

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
# ============================================================================

def mundo_a_celda(x, y):
    col = int((x - ORIGEN_MAPA_X) / CELL_SIZE) # Convierte la coordenada X del mundo a la columna del mapa
    row = int((y - ORIGEN_MAPA_Y) / CELL_SIZE) # Convierte la coordenada Y del mundo a la fila del mapa

    col = max(0, min(COLUMNAS_MAPA - 1, col)) # Asegura que la columna esté dentro del rango del mapa
    row = max(0, min(FILAS_MAPA - 1, row)) # Asegura que la columna y la fila estén dentro del rango del mapa
    return row, col # Devuelve la fila y la columna en el mapa


def centro_celda(row, col):
    x = ORIGEN_MAPA_X + (col + 0.5) * CELL_SIZE # Convierte la columna del mapa a la coordenada X del mundo
    y = ORIGEN_MAPA_Y + (row + 0.5) * CELL_SIZE # Convierte la fila del mapa a la coordenada Y del mundo
    return x, y # Devuelve la coordenada X y Y del mundo


# ============================================================================
# CREAR REJILLA
# True = celda libre, False = celda ocupada (obstáculo o pared)
# ============================================================================
GRID = [[True for _ in range(COLUMNAS_MAPA)] for _ in range(FILAS_MAPA)]

# ============================================================================
# MARCAR PAREDES EXTERIORES
# ============================================================================
for c in range(COLUMNAS_MAPA):
    GRID[0][c] = False
    GRID[FILAS_MAPA - 1][c] = False

for r in range(FILAS_MAPA):
    GRID[r][0] = False
    GRID[r][COLUMNAS_MAPA - 1] = False

# ============================================================================
# MARCAR OBSTACULOS
# ============================================================================
radio_total = RADIO_OBSTACULO + MARGEN_SEGURIDAD

for row in range(FILAS_MAPA):
    for col in range(COLUMNAS_MAPA):
        x, y = centro_celda(row, col)

        for obs in OBSTACULOS:
            dx = x - obs["x"]
            dy = y - obs["y"]
            dist = math.sqrt(dx * dx + dy * dy)

            if dist <= radio_total:
                GRID[row][col] = False
                break

# ============================================================================
# COMPROBAR START Y GOAL
# ============================================================================
CELDA_INICIO = mundo_a_celda(INICIO_MUNDO[0], INICIO_MUNDO[1])
CELDA_OBJETIVO = mundo_a_celda(OBJETIVO_MUNDO[0], OBJETIVO_MUNDO[1])
CELDAS_OBJETIVO = [mundo_a_celda(x, y) for x, y in OBJETIVOS_MUNDO]

if not GRID[CELDA_INICIO[0]][CELDA_INICIO[1]]:
    raise ValueError(f"INICIO_MUNDO cae dentro de obstáculo: {INICIO_MUNDO} -> {CELDA_INICIO}")

if not GRID[CELDA_OBJETIVO[0]][CELDA_OBJETIVO[1]]:
    raise ValueError(f"OBJETIVO_MUNDO cae dentro de obstáculo: {OBJETIVO_MUNDO} -> {CELDA_OBJETIVO}")

for objetivo_mundo, celda_objetivo in zip(OBJETIVOS_MUNDO, CELDAS_OBJETIVO):
    if not GRID[celda_objetivo[0]][celda_objetivo[1]]:
        raise ValueError(f"Objetivo cae dentro de obstáculo: {objetivo_mundo} -> {celda_objetivo}")