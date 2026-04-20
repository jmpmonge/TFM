import config
from robot_io import TIEMPO_PASO, supervisor

# ==============================
# MAPEO TECLAS
# ==============================

TECLAS_ALGORITMO = {
    49: "astar",          # 1
    50: "astar_weighted", # 2
    51: "astar_multi",    # 3
}

TECLAS_HEURISTICA = {
    49: "manhattan",
    50: "euclidiana",
    51: "energia",
    52: "ponderada",
}

ETIQUETAS_HEURISTICA = {
    "manhattan": "Distancia Manhattan",
    "euclidiana": "Distancia Euclidiana",
    "energia": "Estimación de coste energético",
    "ponderada": "Heurística ponderada",
}


def _esperar_liberacion_teclas(teclado):
    """Espera hasta que no quede ninguna tecla pulsada/arrastrada."""
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
    print("\n")
    print("Pulsa dentro de la imagen y después \nselecciona el algoritmo")
    print("=========================================")
    print("ELIGE ALGORITMO")
    print("  1) A* clásico")
    print("  2) Weighted A*")
    print("  3) Multiheurística")
    print("=========================================")

    while supervisor.step(TIEMPO_PASO) != -1:
        tecla = teclado.getKey()
        if tecla in TECLAS_ALGORITMO:
            elegido = TECLAS_ALGORITMO[tecla]
            while teclado.getKey() != -1:
                pass
            print("-> Algoritmo elegido:", elegido)
            _esperar_liberacion_teclas(teclado)
            return elegido

    return config.ALGORITMO


# ==============================
# SELECCIÓN HEURÍSTICA
# ==============================

def elegir_heuristica():
    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)
    _esperar_liberacion_teclas(teclado)
    print("=========================================")
    print("ELIGE HEURISTICA")
    print("  1) Distancia Manhattan")
    print("  2) Distancia Euclidiana")
    print("  3) Estimación de coste energético")
    print("  4) Heurística ponderada: (f(n) = g(n) + w·h(n), w > 1)")
    print("=========================================")

    while supervisor.step(TIEMPO_PASO) != -1:
        tecla = teclado.getKey()
        if tecla in TECLAS_HEURISTICA:
            elegida = TECLAS_HEURISTICA[tecla]
            while teclado.getKey() != -1:
                pass
            print("-> Heuristica elegida:", ETIQUETAS_HEURISTICA[elegida])
            _esperar_liberacion_teclas(teclado)
            return elegida

    return config.HEURISTICA


# ==============================
# EJECUCIÓN FINAL
# ==============================

def elegir_configuracion():
    algoritmo = elegir_algoritmo()
    heuristica = elegir_heuristica()

    config.ALGORITMO = algoritmo
    config.HEURISTICA = heuristica

    print("=========================================")
    print("CONFIGURACIÓN FINAL:")
    print(" Algoritmo:", algoritmo)
    print(" Heurística:", ETIQUETAS_HEURISTICA.get(heuristica, heuristica))
    print("=========================================")


elegir_configuracion()