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
ALGORITMO = "ara_star" # "ara_star" | "astar" | "greedy" | "dijkstra"

# Heurística que usa A* para estimar lo que falta hasta el goal.
# Opciones: "manhattan" | "euclidiana" | "octil" | "cero" (Dijkstra) | "agresiva" (greedy)
HEURISTICA = "octil" # "manhattan" | "euclidiana" | "octil"

# Parámetros de ARA* (ε = peso de la heurística en cada iteración)
# ε alto  → ruta más rápida de calcular
# ε = 1.0 → mismo criterio que A* normal
EPSILON_INICIAL_ARA = 2.5
EPSILON_FINAL_ARA = 1.0
EPSILON_PASO_ARA = 0.5

# Modo ARA*: "offline" (planifica todo y luego mueve) | "anytime_simple" (simulacion por fases)
MODO_ARA = "offline"

# Pasos simulados por fase en modo anytime_simple (celdas avanzadas entre recalculos)
PASOS_POR_FASE_ARA = 10

# Peso fijo del A* ponderado en comparativas: f(n) = g(n) + epsilon * h(n)
PESO_ASTAR_PONDERADO = 1.5

# Coste g de la zona especifica (geometria COST_ZONE_* en el .wbt). Cambiar solo aqui.
COSTE_ZONA_ESPECIFICA = 2

# Alias interno (misma variable)
COSTE_ZONA_AZUL = COSTE_ZONA_ESPECIFICA

# ============================================================================
# MAPA — laberinto (worlds/pioneer3at.wbt)
# En cada arranque se lee el .wbt, se actualiza generated_map.json y se construye GRID.
# ============================================================================

# Valores por defecto si el JSON no trae start/goals.
INICIO_MUNDO_POR_DEFECTO = (-4.25, 10.25)
OBJETIVOS_MUNDO_POR_DEFECTO = [
    (-4.25, 7.25),
]
BATERIA_MAX = 800 # NÚMERO DE UNIDADES DE BATERÍA, 1 UNIDAD = PASO DE 32ms

# ============================================================================
# CARGAR MAPA DESDE WBT (siempre al importar config / arrancar controlador)
# ============================================================================
import sys

_CONTROLLER_DIR = _AQUI.parent
if str(_CONTROLLER_DIR) not in sys.path:
    sys.path.insert(0, str(_CONTROLLER_DIR))

_ROOT_DIR = _CONTROLLER_DIR.parent.parent
_WBT_MAPA = _ROOT_DIR / "worlds" / "pioneer3at.wbt"
_JSON_MAPA = _AQUI / "generated_map.json"

from herramientas.extract_wbt_to_json import cargar_mapa_desde_wbt

mapa = cargar_mapa_desde_wbt(
    wbt_path=str(_WBT_MAPA),
    json_path=str(_JSON_MAPA),
    verbose=False,
)

CELL_SIZE = mapa.get("cell_size", 1.0)
CENTRO_CELDA = CELL_SIZE / 2

MARGEN_SEGURIDAD = 0.3

X_LIMITS = mapa["x_limits"]
Y_LIMITS = mapa["y_limits"]
RADIO_OBSTACULO = mapa["obstacle_radius"]
OBSTACULOS = mapa["obstacles"]
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

ANCHO_MAPA = X_LIMITS[1] - X_LIMITS[0]
ALTO_MAPA = Y_LIMITS[1] - Y_LIMITS[0]

if "grid_cols" in mapa and "grid_rows" in mapa:
    COLUMNAS_MAPA = mapa["grid_cols"]
    FILAS_MAPA = mapa["grid_rows"]
else:
    COLUMNAS_MAPA = int(ANCHO_MAPA / CELL_SIZE)
    FILAS_MAPA = int(ALTO_MAPA / CELL_SIZE)


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


def celda_ocupada(row, col, obs):
    """True si el centro de la celda cae dentro del obstáculo (sin margen)."""
    cx, cy = centro_celda(row, col)
    h = CELL_SIZE / 2.0

    if obs.get("type") == "box":
        ox0 = obs["x"] - obs["size_x"] / 2.0
        ox1 = obs["x"] + obs["size_x"] / 2.0
        oy0 = obs["y"] - obs["size_y"] / 2.0
        oy1 = obs["y"] + obs["size_y"] / 2.0
        return cx - h < ox1 and cx + h > ox0 and cy - h < oy1 and cy + h > oy0

    radio = obs.get("radius", RADIO_OBSTACULO)
    dx = cx - obs["x"]
    dy = cy - obs["y"]
    return math.sqrt(dx * dx + dy * dy) <= radio + h


def distancia_a_obstaculo(x, y, obs):
    """Distancia euclídea del punto (x, y) al contorno del obstáculo."""
    if obs.get("type") == "box":
        dx = max(0.0, abs(x - obs["x"]) - obs["size_x"] / 2.0)
        dy = max(0.0, abs(y - obs["y"]) - obs["size_y"] / 2.0)
        return math.hypot(dx, dy)

    radio = obs.get("radius", RADIO_OBSTACULO)
    return max(0.0, math.hypot(x - obs["x"], y - obs["y"]) - radio)


def distancia_al_contorno(x, y):
    """Distancia mínima al contorno de cualquier obstáculo del mapa."""
    if not OBSTACULOS:
        return float("inf")
    return min(distancia_a_obstaculo(x, y, obs) for obs in OBSTACULOS)


def aplicar_margen_contorno(grid_base):
    """
    Expande el obstáculo solo hacia el espacio libre (contorno unificado).

    A diferencia de inflar cada caja por separado, la distancia se mide al
    contorno más cercano de todos los muros; las junturas interiores no suman
    margen dos veces.
    """
    if MARGEN_SEGURIDAD <= 0.0:
        return grid_base

    grid = [fila[:] for fila in grid_base]
    for row in range(FILAS_MAPA):
        for col in range(COLUMNAS_MAPA):
            if grid_base[row][col]:
                continue
            cx, cy = centro_celda(row, col)
            if distancia_al_contorno(cx, cy) < MARGEN_SEGURIDAD:
                grid[row][col] = 1
    return grid


# ============================================================================
# CREAR REJILLA desde obstáculos del .wbt
# 0 = celda libre, 1 = celda ocupada (muro del laberinto)
# ============================================================================
_GRID_BASE = [[0 for _ in range(COLUMNAS_MAPA)] for _ in range(FILAS_MAPA)]

for row in range(FILAS_MAPA):
    for col in range(COLUMNAS_MAPA):
        for obs in OBSTACULOS:
            if celda_ocupada(row, col, obs):
                _GRID_BASE[row][col] = 1
                break

GRID = aplicar_margen_contorno(_GRID_BASE)

# Zonas de coste: geometria del .wbt; el coste g lo define COSTE_ZONA_ESPECIFICA arriba.
ZONAS_COSTE = mapa.get("cost_zones", [])

CELDAS_ZONA_ESPECIFICA = []
for _zona in ZONAS_COSTE:
    for _row, _col in _zona.get("grid", {}).get("cells", []):
        if GRID[_row][_col] == 0:
            CELDAS_ZONA_ESPECIFICA.append((_row, _col))
            GRID[_row][_col] = COSTE_ZONA_ESPECIFICA


def aplicar_coste_zona_especifica(coste=None):
    """Actualiza COSTE_ZONA_ESPECIFICA y lo escribe en las celdas de la zona."""
    global COSTE_ZONA_ESPECIFICA, COSTE_ZONA_AZUL
    if coste is not None:
        COSTE_ZONA_ESPECIFICA = float(coste)
        COSTE_ZONA_AZUL = COSTE_ZONA_ESPECIFICA
    for _row, _col in CELDAS_ZONA_ESPECIFICA:
        GRID[_row][_col] = COSTE_ZONA_ESPECIFICA

if ZONAS_COSTE:
    _g0 = ZONAS_COSTE[0].get("grid", {})
    ZONA_COSTE_FILA_INI = _g0.get("row_ini")
    ZONA_COSTE_FILA_FIN = (_g0.get("row_fin") + 1) if _g0.get("row_fin") is not None else None
    ZONA_COSTE_COL_INI = _g0.get("col_ini")
    ZONA_COSTE_COL_FIN = (_g0.get("col_fin") + 1) if _g0.get("col_fin") is not None else None
else:
    ZONA_COSTE_FILA_INI = ZONA_COSTE_FILA_FIN = ZONA_COSTE_COL_INI = ZONA_COSTE_COL_FIN = None

# ============================================================================
# COMPROBAR START Y GOAL
# ============================================================================
CELDA_INICIO = mundo_a_rejilla(INICIO_MUNDO[0], INICIO_MUNDO[1])
CELDA_OBJETIVO = mundo_a_rejilla(OBJETIVO_MUNDO[0], OBJETIVO_MUNDO[1])
CELDAS_OBJETIVO = [mundo_a_rejilla(x, y) for x, y in OBJETIVOS_MUNDO]

if GRID[CELDA_INICIO[0]][CELDA_INICIO[1]] == 1:
    cx, cy = centro_celda(*CELDA_INICIO)
    d = distancia_al_contorno(cx, cy)
    raise ValueError(
        f"INICIO_MUNDO no válido con margen {MARGEN_SEGURIDAD} m: {INICIO_MUNDO} -> {CELDA_INICIO} "
        f"(distancia al muro más cercano: {d:.2f} m)"
    )

if GRID[CELDA_OBJETIVO[0]][CELDA_OBJETIVO[1]] == 1:
    cx, cy = centro_celda(*CELDA_OBJETIVO)
    d = distancia_al_contorno(cx, cy)
    raise ValueError(
        f"OBJETIVO_MUNDO no válido con margen {MARGEN_SEGURIDAD} m: {OBJETIVO_MUNDO} -> {CELDA_OBJETIVO} "
        f"(distancia al muro más cercano: {d:.2f} m)"
    )

for objetivo_mundo, celda_objetivo in zip(OBJETIVOS_MUNDO, CELDAS_OBJETIVO):
    if GRID[celda_objetivo[0]][celda_objetivo[1]] == 1:
        cx, cy = centro_celda(*celda_objetivo)
        d = distancia_al_contorno(cx, cy)
        raise ValueError(
            f"Objetivo no válido con margen {MARGEN_SEGURIDAD} m: {objetivo_mundo} -> {celda_objetivo} "
            f"(distancia al muro más cercano: {d:.2f} m)"
        )


# ============================================================================
# RESUMEN DE CONFIGURACION (consola / mapa)
# ============================================================================

_ETIQUETAS_ALGORITMO = {
    "dijkstra": "Dijkstra",
    "astar": "A*",
    "greedy": "Greedy",
    "ara_star": "ARA*",
}

_ETIQUETAS_HEURISTICA = {
    "nula": "Nula",
    "manhattan": "Manhattan",
    "euclidiana": "Euclídea",
    "octil": "Octil",
}


def imprimir_configuracion_planificacion():
    """Confirma en consola los parametros activos de planificacion."""
    print()
    print("=" * 45)
    print("CONFIGURACION DE PLANIFICACION")
    print("=" * 45)
    print("Algoritmo:", _ETIQUETAS_ALGORITMO.get(ALGORITMO, ALGORITMO))
    if ALGORITMO != "dijkstra":
        print("Heuristica:", _ETIQUETAS_HEURISTICA.get(HEURISTICA, HEURISTICA))
    print("Coste zona especifica:", COSTE_ZONA_ESPECIFICA)
    if ALGORITMO == "ara_star":
        print("Modo ARA:", MODO_ARA)
        if MODO_ARA == "anytime_simple":
            print("Pasos por fase:", PASOS_POR_FASE_ARA)
    print("=" * 45)
    print()