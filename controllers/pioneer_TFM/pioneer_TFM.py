from simulacion import menu_heuristica
from configuracion import config

# Menú antes de planificacion: si algo falla al importar algoritmos,
# el usuario ya habrá podido elegir modo (y ver el error después).
menu_heuristica.elegir_configuracion()

from planificacion.algoritmos import planificar_mision, aplanar_mision, imprimir_resumen_planificacion
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

colocar_inicio(config.INICIO_MUNDO[0], config.INICIO_MUNDO[1], orientacion=0.0)

imprimir_resumen_planificacion(
    config.CELDA_INICIO,
    objetivos_celda,
    CAMINO_CELDAS,
    NODOS_EXPLORADOS,
)

bateria_actual = config.BATERIA_MAX
dibujar_bateria(bateria_actual, config.BATERIA_MAX)

fijar_velocidad_ruedas(0.0, 0.0)

while paso():
    state = leer_estado()
    left_speed, right_speed, INDICE_OBJETIVO = decidir(state, PUNTOS, INDICE_OBJETIVO)
    bateria_actual = max(0, config.BATERIA_MAX - max(0, INDICE_OBJETIVO - 1))
    dibujar_bateria(bateria_actual, config.BATERIA_MAX)
    fijar_velocidad_ruedas(left_speed, right_speed)