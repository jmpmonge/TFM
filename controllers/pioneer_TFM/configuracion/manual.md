# ============================================================================
# ESCALA DEL MAPA
# ============================================================================
# El escenario tiene dos representaciones:
#
# - Webots (.wbt): mundo visual en metros.
# - Planificación: grid generado con GRID_CELLS y CELL_SIZE.
#
# Configuración actual:
#   GRID_CELLS = 100
#   CELL_SIZE = 0.2
#   Tamaño del mundo = 100 * 0.2 = 20 x 20 m
#
# Por eso en worlds/pioneer3at.wbt debe aparecer:
#   RectangleArena { floorSize 20 20 }
#
# Si se cambia la escala, hay que modificar de forma coherente:
#   1) config.py: GRID_CELLS / CELL_SIZE
#   2) worlds/pioneer3at.wbt: floorSize, muros, START, GOAL y robot
#   3) generated_map.json: mapa de planificación generado desde el mundo
#
# Obstáculos:
# Cada obstáculo rectangular tiene centro (x, z) y tamaño (size_x, size_z).
# Al escalar el mundo, se multiplican tanto las coordenadas del centro
# como el tamaño del obstáculo.
#
# Ejemplo:
#   de 8x8 m a 20x20 m → factor = 20/8 = 2.5
#   centro (2,1), tamaño (1,2) → centro (5,2.5), tamaño (2.5,5)
#
# Comprobar con:
#   python configuracion/prueba_config.py
# ============================================================================