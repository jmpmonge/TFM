from configuracion import config
import sys

from simulacion.robot_io import TIEMPO_PASO, supervisor

# ============================================================================
# MENÚ DE PLANIFICACIÓN
# ============================================================================
# Muestra opciones en la consola de Webots. El usuario pulsa 1, 2, 3 o 4
# con el foco en la ventana 3D (no en la consola).
# ============================================================================

TECLAS_ALGORITMO = {
    49: "dijkstra",  # 1
    50: "astar",     # 2
    51: "greedy",    # 3
    52: "ara_star",  # 4
}

TECLAS_HEURISTICA_ASTAR = {
    49: "nula",       # 1
    50: "manhattan",  # 2
    51: "euclidiana", # 3
}

TECLAS_HEURISTICA_GREEDY = {
    49: "manhattan",  # 1
    50: "euclidiana", # 2
}

INFO_ALGORITMOS = {
    "dijkstra": {
        "nombre": "Dijkstra",
        "texto": "Explora por coste real. No usa estimación.",
    },
    "astar": {
        "nombre": "A*",
        "texto": "Suma coste real y estimación al objetivo.",
    },
    "greedy": {
        "nombre": "Greedy",
        "texto": "Sigue la estimación. Rápido, no siempre óptimo.",
    },
    "ara_star": {
        "nombre": "ARA*",
        "texto": "Varias búsquedas con epsilon decreciente hasta 1.0.",
    },
}

INFO_HEURISTICAS = {
    "nula": {
        "nombre": "Nula",
        "texto": "Sin estimación. En A* equivale a Dijkstra.",
    },
    "manhattan": {
        "nombre": "Manhattan",
        "texto": "Distancia en filas y columnas (como un tablero).",
    },
    "euclidiana": {
        "nombre": "Euclidiana",
        "texto": "Distancia en línea recta.",
    },
}

ORDEN_MENU_ALGORITMOS = ["dijkstra", "astar", "greedy", "ara_star"]


def _linea_separadora():
    return "=" * 45


def etiqueta_modo_busqueda(algoritmo, heuristica=None):
    info_alg = INFO_ALGORITMOS.get(algoritmo, {"nombre": algoritmo})
    nombre_alg = info_alg["nombre"]

    if algoritmo == "dijkstra":
        return nombre_alg

    info_h = INFO_HEURISTICAS.get(heuristica or "", {"nombre": heuristica})
    return f"{nombre_alg} + {info_h.get('nombre', heuristica)}"


def _esperar_liberacion_teclas(teclado):
    while supervisor.step(TIEMPO_PASO) != -1:
        if teclado.getKey() == -1:
            return


def _imprimir_menu_algoritmos():
    print()
    print(_linea_separadora())
    print("ELIGE EL ALGORITMO DE RUTA")
    print(_linea_separadora())

    for i, clave in enumerate(ORDEN_MENU_ALGORITMOS, start=1):
        info = INFO_ALGORITMOS[clave]
        print(f"  {i}) {info['nombre']}")
        print(f"     {info['texto']}")
        print()

    print("Pulsa un numero en la ventana 3D de Webots.")
    print(_linea_separadora())


def _imprimir_menu_heuristica(algoritmo):
    es_ara = algoritmo == "ara_star"
    titulo = "ARA*" if es_ara else "A*"

    print()
    print(_linea_separadora())
    print(f"ELIGE LA HEURISTICA PARA {titulo}")
    print(_linea_separadora())
    print("La heuristica estima cuanto falta hasta el objetivo.")
    print()

    if es_ara:
        print("ARA* repite la busqueda reduciendo epsilon en cada paso.")
        print(f"  epsilon inicio: {config.EPSILON_INICIAL_ARA}")
        print(f"  epsilon final : {config.EPSILON_FINAL_ARA}")
        print()

    if algoritmo == "greedy":
        opciones = ["manhattan", "euclidiana"]
    else:
        opciones = ["nula", "manhattan", "euclidiana"]

    for i, clave in enumerate(opciones, start=1):
        info = INFO_HEURISTICAS[clave]
        print(f"  {i}) {info['nombre']}")
        print(f"     {info['texto']}")
        print()

    print("Pulsa un numero en la ventana 3D de Webots.")
    print(_linea_separadora())


def elegir_algoritmo():
    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)

    _imprimir_menu_algoritmos()
    sys.stdout.flush()

    _esperar_liberacion_teclas(teclado)

    while supervisor.step(TIEMPO_PASO) != -1:
        tecla = teclado.getKey()

        if tecla in TECLAS_ALGORITMO:
            elegido = TECLAS_ALGORITMO[tecla]

            while teclado.getKey() != -1:
                pass

            _esperar_liberacion_teclas(teclado)
            return elegido

    return config.ALGORITMO


def elegir_heuristica(algoritmo):
    if algoritmo == "dijkstra":
        return "nula"

    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)

    if algoritmo in ("astar", "ara_star", "greedy"):
        _imprimir_menu_heuristica(algoritmo)
        teclas_heuristica = (
            TECLAS_HEURISTICA_ASTAR
            if algoritmo in ("astar", "ara_star")
            else TECLAS_HEURISTICA_GREEDY
        )
    else:
        return config.HEURISTICA

    sys.stdout.flush()
    _esperar_liberacion_teclas(teclado)

    while supervisor.step(TIEMPO_PASO) != -1:
        tecla = teclado.getKey()

        if tecla in teclas_heuristica:
            elegida = teclas_heuristica[tecla]

            while teclado.getKey() != -1:
                pass

            _esperar_liberacion_teclas(teclado)
            return elegida

    return config.HEURISTICA


def elegir_configuracion():
    algoritmo = elegir_algoritmo()
    heuristica = elegir_heuristica(algoritmo)

    config.ALGORITMO = algoritmo
    config.HEURISTICA = heuristica

    print()
    print("Modo elegido:", etiqueta_modo_busqueda(algoritmo, heuristica))
    print()
    sys.stdout.flush()
    return algoritmo, heuristica
