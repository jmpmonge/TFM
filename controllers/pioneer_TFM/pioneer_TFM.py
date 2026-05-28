import math

# menu_heuristica importa robot_io antes que config para que getWorldPath()
# apunte al .wbt que Webots tiene realmente abierto.
from configuracion import preset

if preset.USAR_PRESET:
    preset.aplicar()
else:
    from simulacion import menu_heuristica
    menu_heuristica.elegir_configuracion()

from configuracion import config

from planificacion.algoritmos import (
    coste_base_celda,
    coste_bateria_camino,
    coste_bateria_movimiento,
    log_consumo_bateria_celda,
    planificar_mision,
    aplanar_mision,
    imprimir_resumen_planificacion,
)
from planificacion.mapa import celda_a_mundo
from simulacion.robot_io import colocar_inicio, dibujar_bateria, fijar_velocidad_ruedas, leer_estado, paso
from simulacion.seguimiento import decidir

CAMINO_CELDAS = []
PUNTOS = []
INDICE_OBJETIVO = 0
NODOS_EXPLORADOS = 0

objetivos_celda = [config.mundo_a_rejilla(x, y) for x, y in config.OBJETIVOS_MUNDO]
rutas, NODOS_EXPLORADOS = planificar_mision(
    config.CELDA_INICIO,
    objetivos_celda,
    config.CELDA_INICIO,
    config.BATERIA_MAX,
    devolver_nodos=True,
)

CAMINO_CELDAS = aplanar_mision(rutas)
PUNTOS = [celda_a_mundo(celda) for celda in CAMINO_CELDAS]
INDICE_OBJETIVO = 1 if len(PUNTOS) > 1 else 0

if len(PUNTOS) > 1:
    orientacion_inicial = math.atan2(
        PUNTOS[1][1] - PUNTOS[0][1],
        PUNTOS[1][0] - PUNTOS[0][0],
    )
else:
    orientacion_inicial = 0.0

colocar_inicio(
    config.INICIO_MUNDO[0],
    config.INICIO_MUNDO[1],
    orientacion=orientacion_inicial,
)

imprimir_resumen_planificacion(
    config.CELDA_INICIO,
    objetivos_celda,
    CAMINO_CELDAS,
    NODOS_EXPLORADOS,
)

bateria_actual = config.BATERIA_MAX
_celda_inicio = config.CELDA_INICIO
_valor_grid_inicio = config.GRID[_celda_inicio[0]][_celda_inicio[1]]
dibujar_bateria(
    bateria_actual,
    config.BATERIA_MAX,
    valor_grid=_valor_grid_inicio,
    consumo_celda=coste_base_celda(_celda_inicio),
)

ULTIMO_INDICE_BATERIA = INDICE_OBJETIVO

fijar_velocidad_ruedas(0.0, 0.0)

while paso():
    state = leer_estado()
    left_speed, right_speed, INDICE_OBJETIVO = decidir(state, PUNTOS, INDICE_OBJETIVO)

    if config.LOG_BATERIA_CELDAS and INDICE_OBJETIVO > ULTIMO_INDICE_BATERIA:
        for k in range(ULTIMO_INDICE_BATERIA + 1, INDICE_OBJETIVO + 1):
            if k >= 2:
                origen = CAMINO_CELDAS[k - 2]
                celda = CAMINO_CELDAS[k - 1]
                consumo_tramo = coste_bateria_movimiento(origen, celda)
                consumo_acum = coste_bateria_camino(CAMINO_CELDAS[:k])
                bateria_restante = max(0.0, config.BATERIA_MAX - consumo_acum)
                log_consumo_bateria_celda(
                    celda, origen, consumo_tramo, consumo_acum, bateria_restante
                )
        ULTIMO_INDICE_BATERIA = INDICE_OBJETIVO

    consumo = coste_bateria_camino(CAMINO_CELDAS[:INDICE_OBJETIVO])
    bateria_actual = max(0.0, config.BATERIA_MAX - consumo)

    celda_actual = config.mundo_a_rejilla(state["x"], state["y"])
    valor_grid = config.GRID[celda_actual[0]][celda_actual[1]]
    consumo_celda = coste_base_celda(celda_actual)

    dibujar_bateria(
        bateria_actual,
        config.BATERIA_MAX,
        valor_grid=valor_grid,
        consumo_celda=consumo_celda,
    )
    fijar_velocidad_ruedas(left_speed, right_speed)