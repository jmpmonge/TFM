# ============================================================================
#  EXPLICACION FINAL (para presentacion)
# ----------------------------------------------------------------------------
#
#  Arquitectura del proyecto
#  -------------------------
#    config.py       -> parametros (velocidades, umbral, sensores)
#    robot_io.py     -> comunicacion con el robot (motores y sensores)
#    heuristic.py    -> decision: que hacer segun el estado
#    pioneer_route_controller.py -> bucle principal (este archivo)
#
#  Flujo de datos en cada ciclo
#  ----------------------------
#        +----------------+
#        |   robot_io     |   read_state() -> {time, max_front, values}
#        +----------------+
#                 |
#                 v
#        +----------------+
#        |   heuristic    |   decide(state) -> (left, right)
#        +----------------+
#                 |
#                 v
#        +----------------+
#        |   robot_io     |   set_wheels(left, right)
#        +----------------+
#
#  Como funciona el comportamiento actual
#  --------------------------------------
#    - Mientras todos los sensores frontales leen por debajo del umbral,
#      las dos ruedas van a FORWARD_SPEED => el robot avanza recto.
#    - Cuando un sensor frontal supera OBSTACLE_THRESHOLD, la rueda
#      izquierda va hacia atras y la derecha hacia adelante
#      => el robot gira sobre su eje hasta que deja de ver obstaculo.
#    - Cuando vuelve a ver despejado, retoma el avance recto.
#
#  Como ampliarlo (siguiente paso: seguimiento de ruta)
#  ----------------------------------------------------
#    1. Anade en robot_io.py la lectura de nuevos sensores
#       (laterales, GPS, brujula, camara, etc.) dentro de read_state().
#    2. En heuristic.py escribe tu logica nueva dentro de decide(state).
#       Por ejemplo:
#         - calcular error respecto a una trayectoria
#         - combinar "ir al objetivo" + "evitar obstaculo"
#         - usar una maquina de estados (AVANZAR / EVITAR / REORIENTAR)
#    3. No hace falta tocar pioneer_route_controller.py.
#
#  Por que esta separado asi
#  -------------------------
#    - Cada archivo tiene UNA responsabilidad (mas facil de entender).
#    - La heuristica se puede cambiar sin romper la parte de hardware.
#    - Todos los parametros estan en config.py (facil de ajustar en clase).
# ============================================================================
