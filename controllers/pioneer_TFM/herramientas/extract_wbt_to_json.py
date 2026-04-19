import json
import os

_AQUI = os.path.dirname(os.path.abspath(__file__))
_CONTROLADOR_DIR = os.path.dirname(_AQUI)
_ROOT_DIR = os.path.dirname(os.path.dirname(_CONTROLADOR_DIR))

WBT_PATH = os.path.join(_ROOT_DIR, "worlds", "pioneer3at.wbt")
JSON_PATH = os.path.join(_CONTROLADOR_DIR, "generated_map.json")

OBSTACLE_RADIUS = 0.4 # Radio de los obstáculos en metros


def leer_lineas(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.readlines()


def extraer_floor_size(lineas):
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


def extraer_translation_cercana(lineas, indice_inicio, max_busqueda=12):
    fin = min(len(lineas), indice_inicio + max_busqueda)

    for j in range(indice_inicio + 1, fin):
        texto = lineas[j].strip()
        if texto.startswith("translation"):
            partes = texto.split()
            return float(partes[1]), float(partes[2]), float(partes[3])

    return None


def extraer_obstaculos(lineas):
    obstaculos = []

    for i, linea in enumerate(lineas):
        texto = linea.strip()

        if texto.startswith("DEF OBSTACLE_") and "Solid" in texto:
            nombre = texto.split()[1]
            pos = extraer_translation_cercana(lineas, i)

            if pos is not None:
                x, y, z = pos
                obstaculos.append({
                    "name": nombre,
                    "x": x,
                    "y": y
                })

    return obstaculos


def extraer_objetivos(lineas):
    objetivos = []

    for i, linea in enumerate(lineas):
        texto = linea.strip()

        if texto.startswith("DEF GOAL_") and "Solid" in texto:
            nombre = texto.split()[1]
            pos = extraer_translation_cercana(lineas, i)

            if pos is not None:
                x, y, z = pos
                objetivos.append({
                    "name": nombre,
                    "x": x,
                    "y": y
                })

    return objetivos


def main():
    lineas = leer_lineas(WBT_PATH)

    floor_x, floor_y = extraer_floor_size(lineas)
    obstaculos = extraer_obstaculos(lineas)
    objetivos = extraer_objetivos(lineas)

    datos = {
        "x_limits": [-floor_x / 2.0 if floor_x is not None else None, floor_x / 2.0 if floor_x is not None else None],
        "y_limits": [-floor_y / 2.0 if floor_y is not None else None, floor_y / 2.0 if floor_y is not None else None],
        "obstacle_radius": OBSTACLE_RADIUS,
        "obstacles": obstaculos,
        "goals": objetivos
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    print("Hecho.")
    print("JSON creado:", JSON_PATH)
    print("Obstáculos:", len(obstaculos))
    print("Objetivos:", len(objetivos))
    print("Límites X:", datos["x_limits"])
    print("Límites Y:", datos["y_limits"])


if __name__ == "__main__":
    main()