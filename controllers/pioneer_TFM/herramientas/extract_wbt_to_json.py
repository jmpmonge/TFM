import json
import os
import re
import sys

# ============================================================================
# RUTAS
# ============================================================================
# Este archivo está dentro de algo como:
# controllers/pioneer_TFM/extract_wbt_to_json.py
#
# Desde aquí buscamos:
# - el mundo Webots: worlds/pioneer3at.wbt
# - el JSON de salida: configuracion/generated_map.json
# ============================================================================

_AQUI = os.path.dirname(os.path.abspath(__file__))
_CONTROLADOR_DIR = os.path.dirname(_AQUI)
_ROOT_DIR = os.path.dirname(os.path.dirname(_CONTROLADOR_DIR))

WBT_PATH = os.path.join(_ROOT_DIR, "worlds", "pioneer3at.wbt")
JSON_PATH = os.path.join(_CONTROLADOR_DIR, "configuracion", "generated_map.json")


# ============================================================================
# VALORES POR DEFECTO
# ============================================================================
# Si un cilindro no indica radio, usamos este valor.
# Esto mantiene compatibilidad con los obstáculos antiguos.
# ============================================================================

DEFAULT_OBSTACLE_RADIUS = 0.4
DEFAULT_COST_ZONE = 2.0

# Tamaño de celda lógica (1 m). El número de celdas se infiere del comentario
# "Mapa lógico NxN" del .wbt; si no aparece, se usa floorSize de la arena.
LOGICAL_CELL_SIZE = 1.0


# ============================================================================
# FUNCIONES BÁSICAS
# ============================================================================

def leer_lineas(ruta):
    """Lee el archivo .wbt y devuelve sus líneas."""
    with open(ruta, "r", encoding="utf-8") as f:
        return f.readlines()


def _leer_par_valores(lineas, clave):
    """Busca clave dentro del bloque RectangleArena y devuelve dos floats."""
    dentro_arena = False

    for linea in lineas:
        texto = linea.strip()

        if texto.startswith("RectangleArena"):
            dentro_arena = True
            continue

        if dentro_arena and texto.startswith(clave):
            partes = texto.split()
            return float(partes[1]), float(partes[2])

        if dentro_arena and texto == "}":
            break

    return None, None


def extraer_floor_size(lineas):
    """
    Busca el tamaño del suelo dentro de RectangleArena.

    Ejemplo:
    RectangleArena {
      floorSize 60 60
    }
    """
    return _leer_par_valores(lineas, "floorSize")


def extraer_floor_tile_size(lineas):
    """
    Busca floorTileSize dentro de RectangleArena.

    Ejemplo:
      floorTileSize 1 1
      floorTileSize 0.17 0.17
    """
    return _leer_par_valores(lineas, "floorTileSize")


def extraer_translation_cercana(lineas, indice_inicio, max_busqueda=20):
    """
    Busca la línea translation cerca de un DEF.

    Ejemplo:
    DEF WALL_1 Solid {
      translation 0 2 0.25
    }
    """

    fin = min(len(lineas), indice_inicio + max_busqueda)

    for j in range(indice_inicio + 1, fin):
        texto = lineas[j].strip()

        if texto.startswith("translation"):
            partes = texto.split()
            return float(partes[1]), float(partes[2]), float(partes[3])

    return None


def extraer_box_size_cercano(lineas, indice_inicio, max_busqueda=80):
    """
    Busca un Box cerca del DEF y extrae su size.

    Funciona con estas dos formas:

    geometry Box {
      size 1 1 0.5
    }

    geometry Box { size 1 1 0.5 }
    """

    fin = min(len(lineas), indice_inicio + max_busqueda)
    dentro_box = False

    for j in range(indice_inicio + 1, fin):
        texto = lineas[j].strip()

        # Caso 1: todo en una línea
        if "Box" in texto and "size" in texto:
            partes = texto.replace("{", " ").replace("}", " ").split()
            if "size" in partes:
                i = partes.index("size")
                return float(partes[i + 1]), float(partes[i + 2]), float(partes[i + 3])

        # Caso 2: Box abre bloque
        if "Box" in texto:
            dentro_box = True
            continue

        # Caso 3: size dentro del bloque Box
        if dentro_box and texto.startswith("size"):
            partes = texto.split()
            return float(partes[1]), float(partes[2]), float(partes[3])

        if dentro_box and texto == "}":
            dentro_box = False

    return None


def extraer_cylinder_radius_cercano(lineas, indice_inicio, max_busqueda=80):
    """
    Busca un Cylinder cerca del DEF y extrae su radius.

    Ejemplo:
    geometry Cylinder {
      radius 0.4
    }
    """

    fin = min(len(lineas), indice_inicio + max_busqueda)
    dentro_cylinder = False

    for j in range(indice_inicio + 1, fin):
        texto = lineas[j].strip()

        if texto.startswith("geometry Cylinder") or texto.startswith("Cylinder"):
            dentro_cylinder = True
            continue

        if dentro_cylinder and texto.startswith("radius"):
            partes = texto.split()
            return float(partes[1])

        if dentro_cylinder and texto == "}":
            dentro_cylinder = False

    return None


def inferir_grid_celdas(floor_x, floor_y, tile_x, tile_y):
    """
    Calcula columnas y filas lógicas a partir de la arena y el tamaño de baldosa.
    """
    if tile_x <= 0 or tile_y <= 0:
        raise ValueError("floorTileSize debe ser mayor que cero.")

    columnas = int(round(floor_x / tile_x))
    filas = int(round(floor_y / tile_y))
    return columnas, filas


# ============================================================================
# EXTRAER OBSTÁCULOS Y MUROS
# ============================================================================

def extraer_obstaculos_y_muros(lineas):
    """
    Extrae obstáculos del mundo Webots.

    Detecta dos tipos:

    1. Obstáculos antiguos:
       DEF OBSTACLE_1 Solid { ... }

    2. Muros nuevos:
       DEF WALL_1 Solid { ... }

    Si el objeto tiene Box, se guarda como tipo "box".
    Si el objeto tiene Cylinder, se guarda como tipo "cylinder".
    """

    obstaculos = []

    for i, linea in enumerate(lineas):
        texto = linea.strip()

        es_obstaculo = texto.startswith("DEF OBSTACLE_") and "Solid" in texto
        es_muro = texto.startswith("DEF WALL_") and "Solid" in texto

        if not es_obstaculo and not es_muro:
            continue

        nombre = texto.split()[1]
        pos = extraer_translation_cercana(lineas, i)

        if pos is None:
            continue

        x, y, z = pos

        box_size = extraer_box_size_cercano(lineas, i)
        cylinder_radius = extraer_cylinder_radius_cercano(lineas, i)

        if box_size is not None:
            size_x, size_y, size_z = box_size

            obstaculos.append({
                "name": nombre,
                "type": "box",
                "x": x,
                "y": y,
                "z": z,
                "size_x": size_x,
                "size_y": size_y,
                "size_z": size_z
            })

        else:
            radius = cylinder_radius if cylinder_radius is not None else DEFAULT_OBSTACLE_RADIUS

            obstaculos.append({
                "name": nombre,
                "type": "cylinder",
                "x": x,
                "y": y,
                "z": z,
                "radius": radius
            })

    return obstaculos


# ============================================================================
# EXTRAER ZONAS DE COSTE (superficies COST_ZONE_* del .wbt)
# ============================================================================

def _coste_desde_nombre_zona(nombre):
    """COST_ZONE_5 → 5.0; COST_ZONE_SURFACE u otros → DEFAULT_COST_ZONE."""
    coincidencia = re.match(r"^COST_ZONE_(\d+(?:\.\d+)?)$", nombre)
    if coincidencia:
        return float(coincidencia.group(1))
    return DEFAULT_COST_ZONE


def _centro_celda_json(row, col, origen_x, origen_y, filas, cell_size):
    x = origen_x + col * cell_size + cell_size / 2.0
    y = origen_y + (filas - 1 - row) * cell_size + cell_size / 2.0
    return x, y


def _celda_dentro_caja(row, col, caja, origen_x, origen_y, filas, cell_size):
    cx, cy = _centro_celda_json(row, col, origen_x, origen_y, filas, cell_size)
    h = cell_size / 2.0
    ox0 = caja["x"] - caja["size_x"] / 2.0
    ox1 = caja["x"] + caja["size_x"] / 2.0
    oy0 = caja["y"] - caja["size_y"] / 2.0
    oy1 = caja["y"] + caja["size_y"] / 2.0
    return cx - h < ox1 and cx + h > ox0 and cy - h < oy1 and cy + h > oy0


def zona_coste_a_rejilla(zona, origen_x, origen_y, filas, columnas, cell_size):
    """Convierte la caja Webots de una zona de coste a celdas lógicas."""
    celdas = []
    for row in range(filas):
        for col in range(columnas):
            if _celda_dentro_caja(row, col, zona, origen_x, origen_y, filas, cell_size):
                celdas.append([row, col])

    if not celdas:
        return {
            "row_ini": None,
            "row_fin": None,
            "col_ini": None,
            "col_fin": None,
            "cells": [],
        }

    filas_c = [c[0] for c in celdas]
    cols_c = [c[1] for c in celdas]
    return {
        "row_ini": min(filas_c),
        "row_fin": max(filas_c),
        "col_ini": min(cols_c),
        "col_fin": max(cols_c),
        "cells": celdas,
    }


def extraer_zonas_coste(lineas):
    """
    Extrae superficies DEF COST_ZONE_* (no son obstáculos ni muros).

    El coste se lee del nombre: COST_ZONE_5 → 5; otro nombre → DEFAULT_COST_ZONE.
    """
    zonas = []

    for i, linea in enumerate(lineas):
        texto = linea.strip()

        if not texto.startswith("DEF COST_ZONE_") or "Solid" not in texto:
            continue

        nombre = texto.split()[1]
        pos = extraer_translation_cercana(lineas, i)
        box_size = extraer_box_size_cercano(lineas, i)

        if pos is None or box_size is None:
            continue

        x, y, z = pos
        size_x, size_y, size_z = box_size

        zonas.append({
            "name": nombre,
            "type": "box",
            "cost": _coste_desde_nombre_zona(nombre),
            "x": x,
            "y": y,
            "z": z,
            "size_x": size_x,
            "size_y": size_y,
            "size_z": size_z,
        })

    return zonas


# ============================================================================
# EXTRAER OBJETIVOS
# ============================================================================

def extraer_objetivos(lineas):
    """
    Extrae solo objetivos reales del mundo Webots.

    Se ignoran marcadores visuales como GOAL_MARKER.
    """

    objetivos = []

    for i, linea in enumerate(lineas):
        texto = linea.strip()

        if texto.startswith("DEF GOAL_") and "Solid" in texto:
            nombre = texto.split()[1]

            # Evitar duplicar marcadores visuales
            if nombre == "GOAL_MARKER":
                continue

            pos = extraer_translation_cercana(lineas, i)

            if pos is not None:
                x, y, z = pos

                objetivos.append({
                    "name": nombre,
                    "x": x,
                    "y": y,
                    "z": z
                })

    return objetivos


# ============================================================================
# EXTRAER INICIO
# ============================================================================

def extraer_inicio(lineas):
    """
    Posición inicial: START_MARKER o, si no existe, translation del Pioneer3at.
    """
    for i, linea in enumerate(lineas):
        texto = linea.strip()

        if texto.startswith("DEF START_MARKER") and "Solid" in texto:
            pos = extraer_translation_cercana(lineas, i)
            if pos is not None:
                x, y, z = pos
                return {"name": "START", "x": x, "y": y, "z": z}

    for i, linea in enumerate(lineas):
        if "Pioneer3at" in linea:
            pos = extraer_translation_cercana(lineas, i)
            if pos is not None:
                x, y, z = pos
                return {"name": "PIONEER_3AT", "x": x, "y": y, "z": z}

    return None


# ============================================================================
# GENERAR / SINCRONIZAR JSON
# ============================================================================

def necesita_regenerar(wbt_path=WBT_PATH, json_path=JSON_PATH):
    """True si falta el JSON o el .wbt es más reciente."""
    if not os.path.isfile(json_path):
        return True
    if not os.path.isfile(wbt_path):
        raise FileNotFoundError(f"No se encuentra el mundo Webots: {wbt_path}")
    return os.path.getmtime(wbt_path) > os.path.getmtime(json_path)


def generar_mapa_json(wbt_path=WBT_PATH, json_path=JSON_PATH, verbose=False, escribir_json=True):
    """Lee el .wbt y devuelve el dict del mapa. Opcionalmente escribe generated_map.json."""
    lineas = leer_lineas(wbt_path)

    floor_x, floor_y = extraer_floor_size(lineas)

    if floor_x is None or floor_y is None:
        raise ValueError("No se ha encontrado floorSize en RectangleArena.")

    tile_x, tile_y = extraer_floor_tile_size(lineas)
    if tile_x is None or tile_y is None:
        tile_x = tile_y = LOGICAL_CELL_SIZE

    cell_size = tile_x
    grid_cols, grid_rows = inferir_grid_celdas(floor_x, floor_y, tile_x, tile_y)
    obstaculos = extraer_obstaculos_y_muros(lineas)
    zonas_coste = extraer_zonas_coste(lineas)
    objetivos = extraer_objetivos(lineas)
    inicio = extraer_inicio(lineas)

    origen_x = -floor_x / 2.0
    origen_y = -floor_y / 2.0

    for zona in zonas_coste:
        zona["grid"] = zona_coste_a_rejilla(
            zona, origen_x, origen_y, grid_rows, grid_cols, cell_size
        )

    datos = {
        "x_limits": [origen_x, floor_x / 2.0],
        "y_limits": [origen_y, floor_y / 2.0],
        "grid_cols": grid_cols,
        "grid_rows": grid_rows,
        "grid_cells": max(grid_cols, grid_rows),
        "cell_size": cell_size,

        # Se mantiene esta clave por compatibilidad.
        # Para cilindros antiguos se usa radius.
        # Para muros nuevos se usan size_x y size_y.
        "obstacle_radius": DEFAULT_OBSTACLE_RADIUS,

        "obstacles": obstaculos,
        "cost_zones": zonas_coste,
        "goals": objetivos,
    }

    if inicio is not None:
        datos["start"] = inicio

    if escribir_json:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)

    if verbose:
        print("Hecho.")
        if escribir_json:
            print("JSON creado:", json_path)
        print("Arena Webots:", floor_x, "x", floor_y, "m")
        print("Grid lógico:", grid_cols, "x", grid_rows,
              "| cell_size", cell_size,
              "| límites X", datos["x_limits"], "Y", datos["y_limits"])
        print("Obstáculos/muros:", len(obstaculos))
        print("Zonas de coste:", len(zonas_coste))
        for zona in zonas_coste:
            g = zona.get("grid", {})
            print(
                f"  {zona['name']} cost={zona['cost']} "
                f"filas {g.get('row_ini')}..{g.get('row_fin')} "
                f"cols {g.get('col_ini')}..{g.get('col_fin')}"
            )
        print("Objetivos:", len(objetivos))
        if inicio is not None:
            print("Inicio:", inicio)

        print("\nPrimeros obstáculos detectados:")
        for obs in obstaculos[:5]:
            print(obs)

        print("\nObjetivos detectados:")
        for goal in objetivos:
            print(goal)

    return datos


def sincronizar_si_necesario(wbt_path=WBT_PATH, json_path=JSON_PATH, verbose=False):
    """Regenera el JSON solo si el .wbt cambió. Devuelve True si escribió."""
    if not necesita_regenerar(wbt_path, json_path):
        return False
    generar_mapa_json(wbt_path, json_path, verbose=verbose)
    return True


def resolver_wbt_activo(default_path=WBT_PATH):
    """
    Devuelve la ruta del .wbt que debe usarse para el mapa.

    - En Webots: el mundo abierto (supervisor.getWorldPath()).
    - Fuera de Webots (scripts, pruebas): default_path (pioneer3at.wbt).
    """
    mod = sys.modules.get("simulacion.robot_io")
    if mod is not None and hasattr(mod, "supervisor"):
        try:
            path = mod.supervisor.getWorldPath()
            if path and os.path.isfile(path):
                return os.path.abspath(path)
        except Exception:
            pass
    return os.path.abspath(default_path)


def cargar_mapa_desde_wbt(wbt_path=None, json_path=JSON_PATH, verbose=False):
    """Lee el .wbt activo y actualiza generated_map.json."""
    if wbt_path is None:
        wbt_path = resolver_wbt_activo()
    return generar_mapa_json(wbt_path, json_path, verbose=verbose, escribir_json=True)


# ============================================================================
# PROGRAMA PRINCIPAL
# ============================================================================

def main():
    generar_mapa_json(verbose=True)


if __name__ == "__main__":
    main()