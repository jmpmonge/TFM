# ============================================================================
# GUÍA RÁPIDA PARA CAMBIAR LA ESCALA
# ============================================================================
# Para cambiar el tamaño de celda:
#
# 1) Cambiar CELL_SIZE en:
#    controllers/pioneer_TFM/configuracion/config.py
#
# 2) Ajustar el mundo visual en:
#    worlds/pioneer3at.wbt
#    - floorTileSize = CELL_SIZE CELL_SIZE
#    - comentario del mapa lógico NxN
#    - START, GOAL y robot si se quiere alinearlos al centro de celda
#
# 3) Regenerar generated_map.json:
#    cd controllers/pioneer_TFM
#    python3 herramientas/extract_wbt_to_json.py
#
# 4) Comprobar:
#    python3 configuracion/prueba_config.py
#
# Fórmula:
#    N = int(floorSize / CELL_SIZE)
# ============================================================================