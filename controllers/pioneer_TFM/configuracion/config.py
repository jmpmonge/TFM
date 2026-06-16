import json
import pathlib

_AQUI = pathlib.Path(__file__).parent

with open(_AQUI / "experimento.json", encoding="utf-8") as _f:
    _experimento = json.load(_f)

# ============================================================================
# EXPERIMENTO (experimento.json — única fuente de verdad)
# ============================================================================

COSTE_ZONA_1 = _experimento["COSTE_ZONA_1"]
COSTE_ZONA_2 = _experimento["COSTE_ZONA_2"]
COSTE_ZONA_3 = _experimento["COSTE_ZONA_3"]

PASOS_POR_FASE_ARA = _experimento["PASOS_POR_FASE_ARA"]
PESO_ASTAR_PONDERADO = _experimento["PESO_ASTAR_PONDERADO"]

EPSILON_INICIAL_ARA = _experimento["EPSILON_INICIAL_ARA"]
EPSILON_FINAL_ARA = _experimento["EPSILON_FINAL_ARA"]
EPSILON_PASO_ARA = _experimento["EPSILON_PASO_ARA"]

BATERIA_MAX = _experimento["BATERIA_MAX"]

INICIO_MUNDO_POR_DEFECTO = tuple(_experimento["INICIO_MUNDO_POR_DEFECTO"])
OBJETIVOS_MUNDO_POR_DEFECTO = [
    tuple(p) for p in _experimento["OBJETIVOS_MUNDO_POR_DEFECTO"]
]

SUELO_CAMBIANTE = _experimento["SUELO_CAMBIANTE"]

# ============================================================================
# CONTROLADOR (solo config.py — no van en experimento.json)
# ============================================================================

TIEMPO_PASO = 32
VELOCIDAD_AVANCE = 6.4
VELOCIDAD_GIRO = 6.0
RUEDAS = 0.0975
DISTANCIA_EJES = 0.325

ALGORITMO = "ara_star"
HEURISTICA = "octil"
MODO_ARA = "anytime_simple"

MARGEN_SEGURIDAD = 0.3

USAR_FACTOR_DIAGONAL_BATERIA = True
LOG_BATERIA_CELDAS = False
LOG_BATERIA_OBJETIVOS = True

# ============================================================================
# Carga mapa, rejilla y funciones auxiliares (entorno.py)
# ============================================================================

from configuracion.entorno import cargar_entorno

cargar_entorno()
