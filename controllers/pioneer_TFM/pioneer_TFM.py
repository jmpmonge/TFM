import menu_heuristica
from config import ALGORITMO, BATERIA_MAX, CELDA_INICIO, HEURISTICA, INICIO_MUNDO, OBJETIVOS_MUNDO, mundo_a_celda
from algoritmos import planificar_mision
from mapa import celda_a_mundo
from robot_io import colocar_inicio, dibujar_bateria, fijar_velocidad_ruedas, leer_estado, paso
from seguimiento import decidir

CAMINO_CELDAS = []
PUNTOS = []
INDICE_OBJETIVO = 0
NODOS_EXPLORADOS = 0

objetivos_celda = [mundo_a_celda(x, y) for x, y in OBJETIVOS_MUNDO]
rutas = planificar_mision(CELDA_INICIO, objetivos_celda, CELDA_INICIO, BATERIA_MAX)

for i, ruta in enumerate(rutas):
    if i == 0:
        CAMINO_CELDAS.extend(ruta)
    else:
        CAMINO_CELDAS.extend(ruta[1:])

PUNTOS = [celda_a_mundo(celda) for celda in CAMINO_CELDAS]
INDICE_OBJETIVO = 1 if len(PUNTOS) > 1 else 0

colocar_inicio(INICIO_MUNDO[0], INICIO_MUNDO[1], orientacion=0.0)

print("=========================================")
print("PRUEBA PIONEER ROUTE CONTROLLER")
print("Algoritmo  :", ALGORITMO.upper())
print("Heurística :", HEURISTICA.upper())
print("Inicio     =", INICIO_MUNDO)
print("Objetivos  =", OBJETIVOS_MUNDO)
print("Ruta       :", len(CAMINO_CELDAS), "celdas")
print("Nodos expl.:", NODOS_EXPLORADOS)
print("=========================================")

bateria_actual = BATERIA_MAX
dibujar_bateria(bateria_actual, BATERIA_MAX)

fijar_velocidad_ruedas(0.0, 0.0)

while paso():
    state = leer_estado()
    left_speed, right_speed, INDICE_OBJETIVO = decidir(state, PUNTOS, INDICE_OBJETIVO)
    bateria_actual = max(0, BATERIA_MAX - max(0, INDICE_OBJETIVO - 1))
    dibujar_bateria(bateria_actual, BATERIA_MAX)
    fijar_velocidad_ruedas(left_speed, right_speed)