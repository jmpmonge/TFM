import math
import sys
from pathlib import Path

from planificacion.grid import actualizar_costes_zonas as _actualizar_costes_zonas
from planificacion.grid import celda_bloqueada as _celda_bloqueada
from planificacion.grid import construir_grid

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

_cargado = False


def cargar_entorno():
    global _cargado
    if _cargado:
        return

    from configuracion import config

    aqui = Path(__file__).parent
    controller_dir = aqui.parent
    if str(controller_dir) not in sys.path:
        sys.path.insert(0, str(controller_dir))

    root_dir = controller_dir.parent.parent
    wbt_mapa = root_dir / "worlds" / "pioneer3at.wbt"
    json_mapa = aqui / "generated_map.json"

    from herramientas.extract_wbt_to_json import cargar_mapa_desde_wbt

    mapa = cargar_mapa_desde_wbt(
        wbt_path=str(wbt_mapa),
        json_path=str(json_mapa),
        verbose=False,
    )

    cell_size = mapa.get("cell_size", 0.5)
    x_limits = mapa["x_limits"]
    y_limits = mapa["y_limits"]
    radio_obstaculo = mapa["obstacle_radius"]
    obstaculos = mapa["obstacles"]
    goals = mapa.get("goals", [])
    start = mapa.get("start")

    if start:
        inicio_mundo = (start["x"], start["y"])
    else:
        inicio_mundo = config.INICIO_MUNDO_POR_DEFECTO

    if goals:
        objetivos_mundo = [(goal["x"], goal["y"]) for goal in goals]
    else:
        objetivos_mundo = list(config.OBJETIVOS_MUNDO_POR_DEFECTO)

    origen_mapa_x = x_limits[0]
    origen_mapa_y = y_limits[0]
    ancho_mapa = x_limits[1] - x_limits[0]
    alto_mapa = y_limits[1] - y_limits[0]

    if "grid_cols" in mapa and "grid_rows" in mapa:
        columnas_mapa = mapa["grid_cols"]
        filas_mapa = mapa["grid_rows"]
    else:
        columnas_mapa = int(ancho_mapa / cell_size)
        filas_mapa = int(alto_mapa / cell_size)

    centro_celda_offset = cell_size / 2

    def mundo_a_rejilla(x, y):
        col = int((x - origen_mapa_x) / cell_size)
        row = int(((origen_mapa_y + filas_mapa * cell_size) - y) / cell_size)
        col = max(0, min(columnas_mapa - 1, col))
        row = max(0, min(filas_mapa - 1, row))
        return row, col

    def centro_celda(row, col):
        x = origen_mapa_x + col * cell_size + centro_celda_offset
        y = origen_mapa_y + (filas_mapa - 1 - row) * cell_size + centro_celda_offset
        return x, y

    zonas_coste = mapa.get("cost_zones", [])

    grid_base, grid, celdas_por_zona, celdas_coste = construir_grid(
        obstaculos,
        zonas_coste,
        filas_mapa,
        columnas_mapa,
        config.MARGEN_SEGURIDAD,
        config.COSTE_ZONA_1,
        config.COSTE_ZONA_2,
        config.COSTE_ZONA_3,
        centro_celda,
        cell_size,
        radio_obstaculo,
    )

    def celda_bloqueada(row, col):
        return _celda_bloqueada(row, col, grid_base, grid, celdas_coste)

    def aplicar_costes_zonas(zona1=None, zona2=None, zona3=None):
        if zona1 is not None:
            config.COSTE_ZONA_1 = float(zona1)
        if zona2 is not None:
            config.COSTE_ZONA_2 = float(zona2)
        if zona3 is not None:
            config.COSTE_ZONA_3 = float(zona3)
        _actualizar_costes_zonas(
            grid,
            celdas_por_zona,
            config.COSTE_ZONA_1,
            config.COSTE_ZONA_2,
            config.COSTE_ZONA_3,
        )

    def distancia_a_obstaculo(x, y, obs):
        if obs.get("type") == "box":
            dx = max(0.0, abs(x - obs["x"]) - obs["size_x"] / 2.0)
            dy = max(0.0, abs(y - obs["y"]) - obs["size_y"] / 2.0)
            return math.hypot(dx, dy)
        radio = obs.get("radius", radio_obstaculo)
        return max(0.0, math.hypot(x - obs["x"], y - obs["y"]) - radio)

    def distancia_al_contorno(x, y):
        if not obstaculos:
            return float("inf")
        return min(distancia_a_obstaculo(x, y, obs) for obs in obstaculos)

    def imprimir_configuracion_planificacion():
        print()
        print("=" * 45)
        print("CONFIGURACION DE PLANIFICACION")
        print("=" * 45)
        print("Algoritmo:", _ETIQUETAS_ALGORITMO.get(config.ALGORITMO, config.ALGORITMO))
        if config.ALGORITMO != "dijkstra":
            print("Heuristica:", _ETIQUETAS_HEURISTICA.get(config.HEURISTICA, config.HEURISTICA))
        print("Coste zona 1 (azul)  :", config.COSTE_ZONA_1)
        print("Coste zona 2 (verde):", config.COSTE_ZONA_2)
        print("Coste zona 3 (amar.) :", config.COSTE_ZONA_3)
        print("Suelo cambiante      :", config.SUELO_CAMBIANTE)
        if config.ALGORITMO == "ara_star":
            print("Modo ARA:", config.MODO_ARA)
            if config.MODO_ARA == "anytime_simple":
                print("Pasos por fase:", config.PASOS_POR_FASE_ARA)
        print("=" * 45)
        print()

    celda_inicio = mundo_a_rejilla(inicio_mundo[0], inicio_mundo[1])
    objetivo_mundo = objetivos_mundo[0]
    celda_objetivo = mundo_a_rejilla(objetivo_mundo[0], objetivo_mundo[1])
    celdas_objetivo = [mundo_a_rejilla(x, y) for x, y in objetivos_mundo]

    if celda_bloqueada(*celda_inicio):
        cx, cy = centro_celda(*celda_inicio)
        d = distancia_al_contorno(cx, cy)
        raise ValueError(
            f"INICIO_MUNDO no válido con margen {config.MARGEN_SEGURIDAD} m: {inicio_mundo} -> {celda_inicio} "
            f"(distancia al muro más cercano: {d:.2f} m)"
        )

    if celda_bloqueada(*celda_objetivo):
        cx, cy = centro_celda(*celda_objetivo)
        d = distancia_al_contorno(cx, cy)
        raise ValueError(
            f"OBJETIVO_MUNDO no válido con margen {config.MARGEN_SEGURIDAD} m: {objetivo_mundo} -> {celda_objetivo} "
            f"(distancia al muro más cercano: {d:.2f} m)"
        )

    for obj_mundo, celda_obj in zip(objetivos_mundo, celdas_objetivo):
        if celda_bloqueada(*celda_obj):
            cx, cy = centro_celda(*celda_obj)
            d = distancia_al_contorno(cx, cy)
            raise ValueError(
                f"Objetivo no válido con margen {config.MARGEN_SEGURIDAD} m: {obj_mundo} -> {celda_obj} "
                f"(distancia al muro más cercano: {d:.2f} m)"
            )

    config.mapa = mapa
    config.CELL_SIZE = cell_size
    config.CENTRO_CELDA = centro_celda_offset
    config.X_LIMITS = x_limits
    config.Y_LIMITS = y_limits
    config.RADIO_OBSTACULO = radio_obstaculo
    config.OBSTACULOS = obstaculos
    config.GOALS = goals
    config.START = start
    config.INICIO_MUNDO = inicio_mundo
    config.OBJETIVOS_MUNDO = objetivos_mundo
    config.OBJETIVO_MUNDO = objetivo_mundo
    config.ORIGEN_MAPA_X = origen_mapa_x
    config.ORIGEN_MAPA_Y = origen_mapa_y
    config.ANCHO_MAPA = ancho_mapa
    config.ALTO_MAPA = alto_mapa
    config.COLUMNAS_MAPA = columnas_mapa
    config.FILAS_MAPA = filas_mapa
    config.ZONAS_COSTE = zonas_coste
    config._GRID_BASE = grid_base
    config.GRID = grid
    config.CELDAS_POR_ZONA = celdas_por_zona
    config.CELDAS_COSTE = celdas_coste
    config.CELDA_INICIO = celda_inicio
    config.CELDA_OBJETIVO = celda_objetivo
    config.CELDAS_OBJETIVO = celdas_objetivo
    config.mundo_a_rejilla = mundo_a_rejilla
    config.centro_celda = centro_celda
    config.celda_bloqueada = celda_bloqueada
    config.aplicar_costes_zonas = aplicar_costes_zonas
    config.distancia_a_obstaculo = distancia_a_obstaculo
    config.distancia_al_contorno = distancia_al_contorno
    config.imprimir_configuracion_planificacion = imprimir_configuracion_planificacion

    _cargado = True
