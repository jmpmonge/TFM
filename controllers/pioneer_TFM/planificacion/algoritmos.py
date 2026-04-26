from heapq import heappop, heappush

from configuracion import config
from planificacion.heuristicas import resolver_heuristica, h_nula, h_manhattan
from planificacion.mapa import celda_a_mundo, es_libre


MOVIMIENTOS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


# ==============================
# ALGORITMOS
# ==============================

def dijkstra(inicio, objetivo, heuristica=None):
    return _buscar_camino(inicio, objetivo, usar_coste=True, heuristica=h_nula)

def greedy(inicio, objetivo, heuristica):
    return _buscar_camino(inicio, objetivo, usar_coste=False, heuristica=heuristica)

def astar(inicio, objetivo, heuristica):
    return _buscar_camino(inicio, objetivo, usar_coste=True, heuristica=heuristica)

ALGORITMOS_DISPONIBLES = {
    "dijkstra": dijkstra,
    "astar": astar,
    "greedy": greedy,
}

# ==============================
# NÚCLEO DE BÚSQUEDA
# ==============================

def _buscar_camino(inicio, objetivo, usar_coste, heuristica):
    abiertos = []
    viene_de = {inicio: None}
    coste = {inicio: 0}
    nodos_explorados = 0

    h_inicial = heuristica(inicio, objetivo)

    if usar_coste:
        prioridad_inicial = 0 + h_inicial
    else:
        prioridad_inicial = h_inicial

    heappush(abiertos, (prioridad_inicial, 0, inicio))

    while abiertos:
        _, coste_actual, actual = heappop(abiertos)

        if coste_actual != coste.get(actual, float("inf")):
            continue

        nodos_explorados += 1

        if actual == objetivo:
            return _reconstruir_camino(viene_de, actual), nodos_explorados

        for vecino in _vecinos(actual):
            nuevo_coste = coste[actual] + 1
            h = heuristica(vecino, objetivo)

            if usar_coste:
                prioridad = nuevo_coste + h
            else:
                prioridad = h

            if vecino not in coste or nuevo_coste < coste[vecino]:
                coste[vecino] = nuevo_coste
                viene_de[vecino] = actual
                heappush(abiertos, (prioridad, nuevo_coste, vecino))

    return [], nodos_explorados


def _reconstruir_camino(viene_de, actual):
    camino = []
    while actual is not None:
        camino.append(actual)
        actual = viene_de[actual]
    return camino[::-1]


def _vecinos(celda):
    fila, col = celda
    for df, dc in MOVIMIENTOS:
        nf, nc = fila + df, col + dc
        if es_libre(nf, nc):
            yield (nf, nc)


# ==============================
# RESOLUCIÓN DESDE CONFIG
# ==============================

def resolver_algoritmo(nombre=None):
    return ALGORITMOS_DISPONIBLES.get(nombre or config.ALGORITMO, astar)


def preparar_ruta(inicio, objetivo, heuristica, algoritmo=None):
    """Resuelve un tramo. Si `algoritmo` es None, se lee de config."""
    funcion = algoritmo if algoritmo is not None else resolver_algoritmo()
    camino_celdas, nodos_explorados = funcion(inicio, objetivo, heuristica)

    puntos = [celda_a_mundo(celda) for celda in camino_celdas]
    indice_objetivo = 1 if len(puntos) > 1 else 0

    return camino_celdas, puntos, indice_objetivo, nodos_explorados


def preparar_ruta_desde_config(nombre_heuristica=None):
    heuristica = resolver_heuristica(nombre_heuristica)
    return preparar_ruta(config.CELDA_INICIO, config.CELDA_OBJETIVO, heuristica)


# ==============================
# BATERÍA Y MISIÓN
# ==============================

def ordenar_objetivos(origen, objetivos):
    return sorted(objetivos, key=lambda obj: h_manhattan(origen, obj))


def filtrar_objetivos_por_bateria(origen, objetivos, base, bateria):
    objetivos_ordenados = ordenar_objetivos(origen, objetivos)

    objetivos_validos = []
    coste_total = 0
    posicion_actual = origen

    for obj in objetivos_ordenados:
        coste_hasta_obj = h_manhattan(posicion_actual, obj)
        coste_vuelta_base = h_manhattan(obj, base)

        if coste_total + coste_hasta_obj + coste_vuelta_base > bateria:
            break

        objetivos_validos.append(obj)
        coste_total += coste_hasta_obj
        posicion_actual = obj

    return objetivos_validos


def aplanar_mision(rutas):
    """Une los tramos devueltos por `planificar_mision` en un único camino.

    Si algún tramo está vacío (no se encontró ruta), devuelve [] para señalar
    que la misión completa es inválida.
    """
    camino = []
    for i, ruta in enumerate(rutas):
        if not ruta:
            return []
        if i == 0:
            camino.extend(ruta)
        else:
            camino.extend(ruta[1:])
    return camino


def planificar_mision(origen, objetivos, base, bateria, devolver_nodos=False,
                      algoritmo=None, heuristica=None):
    """Planifica la misión completa (visita objetivos válidos y vuelve a base).

    Por defecto usa el algoritmo y la heurística definidos en `config`. Para
    comparativas (datos_comparados.py) se pueden inyectar manualmente vía
    `algoritmo=` y `heuristica=`.
    """
    objetivos_validos = filtrar_objetivos_por_bateria(origen, objetivos, base, bateria)

    rutas = []
    nodos_totales = 0
    posicion_actual = origen
    h = heuristica if heuristica is not None else resolver_heuristica()

    for obj in objetivos_validos:
        camino, _, _, nodos = preparar_ruta(posicion_actual, obj, h, algoritmo)
        rutas.append(camino)
        nodos_totales += nodos
        posicion_actual = obj

    camino_vuelta, _, _, nodos = preparar_ruta(posicion_actual, base, h, algoritmo)
    rutas.append(camino_vuelta)
    nodos_totales += nodos

    if devolver_nodos:
        return rutas, nodos_totales

    return rutas