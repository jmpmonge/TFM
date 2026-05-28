import math
from controller import Supervisor  # type: ignore[import-not-found]


supervisor = Supervisor()
TIEMPO_PASO = 32

try:
    display = supervisor.getDevice("display")
except Exception:
    display = None

# Nodo del robot para leer la pose real en cada paso
nodo_robot = supervisor.getFromDef("PIONEER_3AT")
if nodo_robot is None:
    raise RuntimeError("No se encontró el DEF 'PIONEER_3AT' en el mundo de Webots.")

# Ruedas del lado izquierdo
ruedas_izquierdas = [
    supervisor.getDevice("front left wheel"),
    supervisor.getDevice("back left wheel"),
]

# Ruedas del lado derecho
ruedas_derechas = [
    supervisor.getDevice("front right wheel"),
    supervisor.getDevice("back right wheel"),
]

for rueda in ruedas_izquierdas + ruedas_derechas:
    rueda.setPosition(float("inf"))
    rueda.setVelocity(0.0)

# Velocidad máxima declarada por el motor (Pioneer 3-AT: 6.4 rad/s).
# Saturamos contra ella en `fijar_velocidad_ruedas` para evitar warnings
# "exceeds maxVelocity" cuando avance y giro se combinan al máximo.
# Restamos un epsilon pequeño porque Webots compara estrictamente.
_VELOCIDAD_MAX_RUEDA = min(
    rueda.getMaxVelocity() for rueda in ruedas_izquierdas + ruedas_derechas
) - 1e-6


def _saturar(velocidad):
    if velocidad > _VELOCIDAD_MAX_RUEDA:
        return _VELOCIDAD_MAX_RUEDA
    if velocidad < -_VELOCIDAD_MAX_RUEDA:
        return -_VELOCIDAD_MAX_RUEDA
    return velocidad


def colocar_inicio(x, y, z=0.0, orientacion=0.0):
    nodo = supervisor.getFromDef("PIONEER_3AT")
    if nodo is not None:
        nodo.getField("translation").setSFVec3f([float(x), float(y), float(z)])
        nodo.getField("rotation").setSFRotation([0.0, 0.0, 1.0, float(orientacion)])
        nodo.resetPhysics()


def colocar_meta(x, y, z=1.0, goal_def="GOAL_1"):
    nodo = supervisor.getFromDef(goal_def)
    if nodo is None and goal_def != "GOAL":
        nodo = supervisor.getFromDef("GOAL")
    if nodo is not None:
        nodo.getField("translation").setSFVec3f([float(x), float(y), float(z)])


def dibujar_bateria(bateria_actual, bateria_max, valor_grid=0, consumo_celda=None):
    """Display de batería; opcionalmente avisa si el robot está en zona de coste."""
    if display is None:
        return

    if consumo_celda is None:
        consumo_celda = 1.0 if valor_grid == 0 else float(valor_grid)

    ancho_display = display.getWidth()
    alto_display = display.getHeight()
    margen = 8
    ancho_barra = max(12, ancho_display - 2 * margen)
    alto_barra = max(8, min(12, alto_display - 28))

    if bateria_max <= 0:
        proporcion = 0.0
    else:
        proporcion = max(0.0, min(1.0, bateria_actual / bateria_max))

    ancho_relleno = int(ancho_barra * proporcion)
    en_zona = valor_grid > 0
    zona_cara = valor_grid >= 10
    zona_muy_cara = valor_grid >= 30

    if en_zona:
        if zona_muy_cara:
            color_barra = 0xFF2200
        elif zona_cara:
            color_barra = 0xFF6600
        else:
            color_barra = 0xFFAA00
    elif proporcion > 0.5:
        color_barra = 0x00FF00
    elif proporcion > 0.2:
        color_barra = 0xFFFF00
    else:
        color_barra = 0xFF0000

    if en_zona:
        if zona_muy_cara:
            color_texto = 0xFF4400
        elif zona_cara:
            color_texto = 0xFF8800
        else:
            color_texto = 0xFFCC00
    else:
        color_texto = 0xFFFFFF

    display.setColor(0x000000)
    display.fillRectangle(0, 0, ancho_display, alto_display)

    display.setColor(color_texto)
    display.drawText(f"Bateria: {int(bateria_actual)}/{int(bateria_max)}", margen, 0)

    y_barra = 14
    if en_zona:
        borde = 0xFF0000 if zona_muy_cara else (0xFF6600 if zona_cara else 0xFFAA00)
        display.setColor(borde)
        display.drawRectangle(margen - 1, y_barra - 1, ancho_barra + 2, alto_barra + 2)

    display.setColor(0xFFFFFF)
    display.drawRectangle(margen, y_barra, ancho_barra, alto_barra)
    display.setColor(color_barra)
    display.fillRectangle(margen + 1, y_barra + 1, max(0, ancho_relleno - 2), max(0, alto_barra - 2))

    if en_zona:
        etiqueta = "ZONA CARA" if zona_cara else "ZONA COSTE"
        texto_zona = f"{etiqueta}: {int(consumo_celda)}"
        y_aviso = y_barra + alto_barra + 4
        if y_aviso + 10 <= alto_display:
            if zona_muy_cara:
                display.setColor(0x550000)
            elif zona_cara:
                display.setColor(0x663300)
            else:
                display.setColor(0x554400)
            display.fillRectangle(margen, y_aviso, ancho_barra, 10)
            display.setColor(0xFFAA00 if not zona_cara else 0xFF4400)
            display.drawText(texto_zona, margen + 1, y_aviso + 1)


def fijar_velocidad_ruedas(velocidad_izquierda, velocidad_derecha):
    v_izq = _saturar(float(velocidad_izquierda))
    v_der = _saturar(float(velocidad_derecha))

    for rueda in ruedas_izquierdas:
        rueda.setVelocity(v_izq)

    for rueda in ruedas_derechas:
        rueda.setVelocity(v_der)


def detener():
    fijar_velocidad_ruedas(0.0, 0.0)


def paso():
    return supervisor.step(TIEMPO_PASO) != -1


def obtener_pose_real():
    """Devuelve la pose real del robot desde Supervisor."""
    posicion = nodo_robot.getPosition()       # [x, y, z]
    matriz_orientacion = nodo_robot.getOrientation()  # 9 floats

    # Ángulo yaw alrededor del eje Z
    orientacion = math.atan2(matriz_orientacion[3], matriz_orientacion[0])

    return posicion[0], posicion[1], orientacion


def leer_estado():
    x, y, orientacion = obtener_pose_real()

    return {
        "tiempo_s": supervisor.getTime(),
        "x": x,
        "y": y,
        "orientacion": orientacion,
    }
