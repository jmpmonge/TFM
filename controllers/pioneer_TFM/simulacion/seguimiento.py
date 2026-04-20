import math

from configuracion.config import VELOCIDAD_AVANCE, VELOCIDAD_GIRO


def seguir_camino(estado, puntos, indice_objetivo):
    if not puntos or indice_objetivo >= len(puntos):
        return 0.0, 0.0, indice_objetivo

    rx = estado["x"]
    ry = estado["y"]

    px, py = puntos[indice_objetivo]
    dx = px - rx
    dy = py - ry
    distancia = math.hypot(dx, dy)

    if distancia < 0.3:
        indice_objetivo += 1
        if indice_objetivo >= len(puntos):
            return 0.0, 0.0, indice_objetivo
        return 0.0, 0.0, indice_objetivo

    angulo_deseado = math.atan2(dy, dx)
    error = angulo_deseado - estado["orientacion"]
    error = math.atan2(math.sin(error), math.cos(error))

    avance = max(0.0, 1.0 - abs(error))
    giro = max(-1.0, min(1.0, error))
    return avance, giro, indice_objetivo


def decidir(estado, puntos, indice_objetivo):
    avance, giro, nuevo_indice = seguir_camino(estado, puntos, indice_objetivo)
    velocidad_izquierda = avance * VELOCIDAD_AVANCE - giro * VELOCIDAD_GIRO
    velocidad_derecha = avance * VELOCIDAD_AVANCE + giro * VELOCIDAD_GIRO
    return velocidad_izquierda, velocidad_derecha, nuevo_indice
