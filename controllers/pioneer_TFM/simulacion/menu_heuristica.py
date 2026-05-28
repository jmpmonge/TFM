from configuracion import config
import sys

from simulacion.robot_io import TIEMPO_PASO, supervisor

# ============================================================================
# MENÚ DE PLANIFICACIÓN
# ============================================================================
# Muestra opciones en la consola de Webots. El usuario pulsa números
# con el foco en la ventana 3D (no en la consola).
# ============================================================================

TECLAS_ALGORITMO = {
    49: "dijkstra",  # 1
    50: "astar",     # 2
    51: "greedy",    # 3
    52: "ara_star",  # 4
}

TECLAS_HEURISTICA = {
    49: "manhattan",  # 1
    50: "euclidiana", # 2
    51: "octil",      # 3
}

TECLAS_MODO_ARA = {
    49: "offline",         # 1
    50: "anytime_simple",  # 2
}

# Opciones numericas: tecla A/B/C (no 1/2/3, para no confundir con otros menus).
ZONAS_COSTE_MENU = (
    ("Zona 1 azul - arriba (COST_ZONE_2)", "COSTE_ZONA_1"),
    ("Zona 2 marron - izquierda (COST_ZONE_3)", "COSTE_ZONA_2"),
    ("Zona 3 amarilla - centro (COST_ZONE_4)", "COSTE_ZONA_3"),
)

OPCIONES_COSTE_ZONA = (
    ("A", 2),
    ("B", 5),
    ("C", 10),
)

OPCIONES_PASOS_FASE = (
    ("A", 5),
    ("B", 10),
    ("C", 20),
)


def _teclas_opciones_abc(opciones):
    """Mapea A/a, B/b, C/c al valor de cada opcion."""
    teclas = {}
    for letra, valor in opciones:
        teclas[ord(letra.upper())] = valor
        teclas[ord(letra.lower())] = valor
    return teclas


TECLAS_COSTE_ZONA = _teclas_opciones_abc(OPCIONES_COSTE_ZONA)
TECLAS_PASOS_FASE = _teclas_opciones_abc(OPCIONES_PASOS_FASE)

INFO_MODO_ARA = {
    "offline": {
        "nombre": "offline",
        "texto": "Calcula todos los epsilon y devuelve la ruta final.",
    },
    "anytime_simple": {
        "nombre": "anytime_simple",
        "texto": "Avanza por fases y recalcula desde la posicion alcanzada.",
    },
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
    "manhattan": {
        "nombre": "Manhattan",
        "texto": "Distancia en filas y columnas (como un tablero).",
    },
    "euclidiana": {
        "nombre": "Euclídea",
        "texto": "Distancia en línea recta.",
    },
    "octil": {
        "nombre": "Octil",
        "texto": "Distancia con diagonales a coste sqrt(2).",
    },
}

ORDEN_MENU_ALGORITMOS = ["dijkstra", "astar", "greedy", "ara_star"]
OPCIONES_HEURISTICA = ["manhattan", "euclidiana", "octil"]


def _linea_separadora():
    return "=" * 45


def etiqueta_modo_busqueda(algoritmo, heuristica=None):
    info_alg = INFO_ALGORITMOS.get(algoritmo, {"nombre": algoritmo})
    nombre_alg = info_alg["nombre"]

    if algoritmo == "dijkstra":
        return nombre_alg

    info_h = INFO_HEURISTICAS.get(heuristica or "", {"nombre": heuristica})
    return f"{nombre_alg} + {info_h.get('nombre', heuristica)}"


def _vaciar_teclado(teclado, pasos=12):
    """Descarta pulsaciones en cola (p. ej. el '3' de greedy antes del submenú)."""
    for _ in range(pasos):
        if supervisor.step(TIEMPO_PASO) == -1:
            return
        teclado.getKey()


def _esperar_liberacion_teclas(teclado):
    while supervisor.step(TIEMPO_PASO) != -1:
        if teclado.getKey() == -1:
            _vaciar_teclado(teclado, pasos=4)
            return


def _esperar_tecla(teclado, teclas_validas):
    _esperar_liberacion_teclas(teclado)
    while supervisor.step(TIEMPO_PASO) != -1:
        tecla = teclado.getKey()
        if tecla in teclas_validas:
            _esperar_liberacion_teclas(teclado)
            return teclas_validas[tecla]
    return None


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

    print("Pulsa un numero del 1 al 4 en la ventana 3D de Webots.")
    print(_linea_separadora())


def _imprimir_menu_heuristica(algoritmo):
    titulo = INFO_ALGORITMOS.get(algoritmo, {"nombre": algoritmo})["nombre"]

    print()
    print(_linea_separadora())
    print(f"ELIGE LA HEURISTICA PARA {titulo}")
    print(_linea_separadora())
    print("La heuristica estima cuanto falta hasta el objetivo.")
    print()

    for i, clave in enumerate(OPCIONES_HEURISTICA, start=1):
        info = INFO_HEURISTICAS[clave]
        print(f"  {i}) {info['nombre']}")
        print(f"     {info['texto']}")
        print()

    print("Pulsa un numero del 1 al 3 en la ventana 3D de Webots.")
    print(_linea_separadora())


def _imprimir_menu_coste_zona(titulo, valor_actual):
    print()
    print(_linea_separadora())
    print(titulo)
    print(_linea_separadora())
    print(f"  Valor actual: {valor_actual}")
    print()

    for letra, coste in OPCIONES_COSTE_ZONA:
        print(f"  {letra}) coste = {coste}")
    print()

    print("Pulsa A, B o C en la ventana 3D de Webots (no uses numeros).")
    print(_linea_separadora())


def _imprimir_menu_modo_ara():
    print()
    print(_linea_separadora())
    print("ELIGE EL MODO ARA*")
    print(_linea_separadora())

    for i, clave in enumerate(("offline", "anytime_simple"), start=1):
        info = INFO_MODO_ARA[clave]
        print(f"  {i}) {info['nombre']}")
        print(f"     {info['texto']}")
        print()

    print("Pulsa 1 (offline) o 2 (anytime_simple) en la ventana 3D de Webots.")
    print(_linea_separadora())


def _imprimir_menu_pasos_fase():
    print()
    print(_linea_separadora())
    print("ELIGE LOS PASOS POR FASE (ANYTIME_SIMPLE)")
    print(_linea_separadora())
    print(f"  Valor actual: {config.PASOS_POR_FASE_ARA}")
    print()

    for letra, pasos in OPCIONES_PASOS_FASE:
        print(f"  {letra}) pasos por fase = {pasos}")
    print()

    print("Pulsa A, B o C en la ventana 3D de Webots (no uses numeros).")
    print(_linea_separadora())


def elegir_algoritmo():
    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)

    _imprimir_menu_algoritmos()
    sys.stdout.flush()

    elegido = _esperar_tecla(teclado, TECLAS_ALGORITMO)
    return elegido or config.ALGORITMO


def elegir_heuristica(algoritmo):
    if algoritmo == "dijkstra":
        return "nula"

    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)

    _imprimir_menu_heuristica(algoritmo)
    sys.stdout.flush()

    elegida = _esperar_tecla(teclado, TECLAS_HEURISTICA)
    return elegida or config.HEURISTICA


def elegir_costes_zonas():
    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)

    valores = [
        config.COSTE_ZONA_1,
        config.COSTE_ZONA_2,
        config.COSTE_ZONA_3,
    ]

    for i, (titulo, _attr) in enumerate(ZONAS_COSTE_MENU):
        _imprimir_menu_coste_zona(titulo, valores[i])
        sys.stdout.flush()
        coste = _esperar_tecla(teclado, TECLAS_COSTE_ZONA)
        if coste is not None:
            valores[i] = coste
            print(f"  -> {titulo}: coste = {coste}")
            sys.stdout.flush()

    config.aplicar_costes_zonas(*valores)
    return valores


def elegir_modo_ara():
    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)

    _imprimir_menu_modo_ara()
    sys.stdout.flush()

    elegido = _esperar_tecla(teclado, TECLAS_MODO_ARA)
    if elegido is not None:
        config.MODO_ARA = elegido
    return config.MODO_ARA


def elegir_pasos_por_fase():
    teclado = supervisor.getKeyboard()
    teclado.enable(TIEMPO_PASO)

    _imprimir_menu_pasos_fase()
    sys.stdout.flush()

    pasos = _esperar_tecla(teclado, TECLAS_PASOS_FASE)
    if pasos is not None:
        config.PASOS_POR_FASE_ARA = pasos
        print(f"  -> pasos por fase = {pasos}")
        sys.stdout.flush()
    return config.PASOS_POR_FASE_ARA


def elegir_configuracion():
    algoritmo = elegir_algoritmo()
    heuristica = elegir_heuristica(algoritmo)
    elegir_costes_zonas()

    config.ALGORITMO = algoritmo
    config.HEURISTICA = heuristica

    if algoritmo == "ara_star":
        elegir_modo_ara()
        if config.MODO_ARA == "anytime_simple":
            elegir_pasos_por_fase()

    config.imprimir_configuracion_planificacion()
    sys.stdout.flush()
    return algoritmo, heuristica
