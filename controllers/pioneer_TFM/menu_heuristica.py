import config
from robot_io import TIEMPO_PASO, supervisor

# ==============================
# MAPEO TECLAS
# ==============================

TECLAS_ALGORITMO = {
    49: "dijkstra",  # 1
    50: "astar",     # 2
    51: "greedy",    # 3
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


def etiqueta_modo_busqueda(algoritmo, heuristica=None):
    clave_heuristica = heuristica or ""

    if algoritmo == "dijkstra":
        return "Dijkstra"

    if algoritmo == "astar":
        etiquetas = {
            "nula": "A* con heurística nula (equivale a Dijkstra)",
            "manhattan": "A* con heurística Manhattan",
            "euclidiana": "A* con heurística Euclidiana",
        }
        return etiquetas.get(clave_heuristica, f"A* con heurística {heuristica}")

    if algoritmo == "greedy":
        etiquetas = {
            "manhattan": "Greedy con heurística Manhattan",
            "euclidiana": "Greedy con heurística Euclidiana",
        }
        return etiquetas.get(clave_heuristica, f"Greedy con heurística {heuristica}")

    return str(algoritmo)


def _esperar_liberacion_teclas(teclado):
    while supervisor.step(TIEMPO_PASO) != -1:
        if teclado.getKey() == -1:
            return


# ==============================
# SELECCIÓN ALGORITMO
# ==============================

def elegir_algoritmo():
    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)
    _esperar_liberacion_teclas(teclado)

    print("\nSelecciona un algoritmo de búsqueda")
    print("=========================================")
    print("ELIGE ALGORITMO")
    print("  1) Dijkstra")
    print("  2) A*")
    print("  3) Greedy")
    print("=========================================")

    while supervisor.step(TIEMPO_PASO) != -1:
        tecla = teclado.getKey()

        if tecla in TECLAS_ALGORITMO:
            elegido = TECLAS_ALGORITMO[tecla]

            while teclado.getKey() != -1:
                pass

            _esperar_liberacion_teclas(teclado)
            return elegido

    return config.ALGORITMO


# ==============================
# SELECCIÓN HEURÍSTICA
# ==============================

def elegir_heuristica(algoritmo):
    # Dijkstra no necesita heurística
    if algoritmo == "dijkstra":
        return "nula"

    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)
    _esperar_liberacion_teclas(teclado)

    if algoritmo == "astar":
        print("\nSelecciona una heurística para el algoritmo A*")
        print("=========================================")
        print("  1) Heurística nula (algoritmo Dijkstra)")
        print("  2) Heurística Manhattan")
        print("  3) Heurística Euclidiana")
        print("=========================================")
        teclas_heuristica = TECLAS_HEURISTICA_ASTAR

    elif algoritmo == "greedy":
        print("\nSelecciona una heurística para el algoritmo Greedy")
        print("=========================================")
        print("  1) Heurística Manhattan")
        print("  2) Heurística Euclidiana")
        print("=========================================")
        teclas_heuristica = TECLAS_HEURISTICA_GREEDY

    else:
        return config.HEURISTICA

    while supervisor.step(TIEMPO_PASO) != -1:
        tecla = teclado.getKey()

        if tecla in teclas_heuristica:
            elegida = teclas_heuristica[tecla]

            while teclado.getKey() != -1:
                pass

            _esperar_liberacion_teclas(teclado)
            return elegida

    return config.HEURISTICA


# ==============================
# EJECUCIÓN FINAL
# ==============================

def elegir_configuracion():
    algoritmo = elegir_algoritmo()
    heuristica = elegir_heuristica(algoritmo)

    config.ALGORITMO = algoritmo
    config.HEURISTICA = heuristica

    print("-> Modo elegido:", etiqueta_modo_busqueda(algoritmo, heuristica))
    return algoritmo, heuristica


elegir_configuracion()