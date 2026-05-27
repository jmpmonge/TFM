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
if _CONTROLADOR_DIR not in sys.path:
    sys.path.insert(0, _CONTROLADOR_DIR)
_ROOT_DIR = os.path.dirname(os.path.dirname(_CONTROLADOR_DIR))

WBT_PATH = os.path.join(_ROOT_DIR, "worlds", "pioneer3at.wbt")
JSON_PATH = os.path.join(_CONTROLADOR_DIR, "configuracion", "generated_map.json")


# ============================================================================
# VALORES POR DEFECTO
# ============================================================================
# Si un cilindro no indica radio, usamos este valor.
# Esto mantiene compatibilidad con los obstáculos antiguos.
# ============================================================================


# Tamaño de celda lógica (1 m). El número de celdas se infiere del comentario
# "Mapa lógico NxN" del .wbt; si no aparece, se usa floorSize de la arena.


def _parametros_mapa():
    """
    Lee CELL_SIZE y OBSTACLE_RADIUS del config activo (config.py o config2 renombrado).

    Importación diferida: config.py importa este módulo al cargarse; un import
    al inicio del archivo provocaría importación circular.
    """
    from configuracion import config
    return config.CELL_SIZE, config.OBSTACLE_RADIUS


# ============================================================================
# FUNCIONES BÁSICAS
# ============================================================================

def leer_lineas(ruta):
    """Lee el archivo .wbt y devuelve sus líneas."""
    with open(ruta, "r", encoding="utf-8") as f:
        return f.readlines()


def extraer_floor_size(lineas):
    """
    Busca el tamaño del suelo dentro de RectangleArena.

    Ejemplo:
    RectangleArena {
      floorSize 60 60
    }
    """

    dentro_arena = False

    for linea in lineas:
        texto = linea.strip()

        if texto.startswith("RectangleArena"):
            dentro_arena = True
            continue

        if dentro_arena and texto.startswith("floorSize"):
            partes = texto.split()
            return float(partes[1]), float(partes[2])

        if dentro_arena and texto == "}":
            break

    return None, None


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


def inferir_grid_celdas(lineas, floor_x):
    """
    Lee "Mapa lógico NxN" del .wbt; si no hay comentario, usa floorSize.
    """
    for linea in lineas:
        coincidencia = re.search(r"Mapa lógico (\d+)x(\d+)", linea, re.IGNORECASE)
        if coincidencia:
            filas = int(coincidencia.group(1))
            columnas = int(coincidencia.group(2))
            if filas == columnas:
                return filas
    return int(floor_x)


# ============================================================================
# EXTRAER OBSTÁCULOS Y MUROS
# ============================================================================

def extraer_obstaculos_y_muros(lineas, obstacle_radius=0.0):
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
            radius = cylinder_radius if cylinder_radius is not None else obstacle_radius

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


def generar_mapa_json(wbt_path=WBT_PATH, json_path=JSON_PATH, verbose=False):
    """Lee el .wbt y escribe generated_map.json. Devuelve el dict generado."""
    lineas = leer_lineas(wbt_path)

    floor_x, floor_y = extraer_floor_size(lineas)

    if floor_x is None or floor_y is None:
        raise ValueError("No se ha encontrado floorSize en RectangleArena.")

    cell_size, obstacle_radius = _parametros_mapa()

    grid_celdas = inferir_grid_celdas(lineas, floor_x)
    obstaculos = extraer_obstaculos_y_muros(lineas, obstacle_radius=obstacle_radius)
    objetivos = extraer_objetivos(lineas)
    inicio = extraer_inicio(lineas)

    medio = grid_celdas * cell_size / 2.0

    datos = {
        "x_limits": [-medio, medio],
        "y_limits": [-medio, medio],
        "grid_cells": grid_celdas,
        "cell_size": cell_size,

        # Se mantiene esta clave por compatibilidad.
        # Para cilindros antiguos se usa radius.
        # Para muros nuevos se usan size_x y size_y.
        "obstacle_radius": obstacle_radius,

        "obstacles": obstaculos,
        "goals": objetivos,
    }

    if inicio is not None:
        datos["start"] = inicio

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    if verbose:
        print("Hecho.")
        print("JSON creado:", json_path)
        print("Arena Webots:", floor_x, "x", floor_y, "m")
        print("Grid lógico:", grid_celdas, "x", grid_celdas,
              "| límites", datos["x_limits"], datos["y_limits"])
        print("Obstáculos/muros:", len(obstaculos))
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


# ============================================================================
# PROGRAMA PRINCIPAL
# ============================================================================

def main():
    generar_mapa_json(verbose=True)


if __name__ == "__main__":
    main()