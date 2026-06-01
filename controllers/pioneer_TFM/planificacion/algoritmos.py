from heapq import heappop, heappush

from configuracion import config
from planificacion.costes import coste_movimiento
from planificacion.heuristicas import resolver_heuristica, h_nula
from planificacion.mapa import celda_a_mundo, es_libre


MOVIMIENTOS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]


# ==============================
# ALGORITMOS
# ==============================

def dijkstra(inicio, objetivo, heuristica=None):
    return _buscar_camino(inicio, objetivo, usar_coste=True, heuristica=h_nula)

def greedy(inicio, objetivo, heuristica):
    return _buscar_camino(inicio, objetivo, usar_coste=False, heuristica=heuristica)

def astar(inicio, objetivo, heuristica):
    return _buscar_camino(inicio, objetivo, usar_coste=True, heuristica=heuristica)

def astar_ponderado(inicio, objetivo, heuristica, peso_heuristica=None):
    """
    A* con la heuristica multiplicada por un peso w (o epsilon en ARA*).

    Prioridad de cada nodo:
        f(n) = g(n) + w * h(n)

    - w = 1  -> igual que A* estandar.
    - w > 1  -> se confia mas en h(n); suele expandir menos nodos.
    - w > 1  -> la ruta puede dejar de ser optima.

    ARA* llama a esta funcion en cada iteracion cambiando w = epsilon.
    """
    if peso_heuristica is None:
        peso_heuristica = config.PESO_ASTAR_PONDERADO

    return _buscar_camino(
        inicio=inicio,
        objetivo=objetivo,
        heuristica=heuristica,
        usar_coste=True,
        peso_heuristica=peso_heuristica
    )


ALGORITMOS_DISPONIBLES = {
    "dijkstra": dijkstra,
    "astar": astar,
    "greedy": greedy,
    "astar_ponderado": astar_ponderado,
}


def _buscar_camino(inicio, objetivo, heuristica=None, usar_coste=True, peso_heuristica=1.0):
    """
    Motor común de búsqueda.

    Permite expresar:

    - Dijkstra:
        f(n) = g(n)
        Se consigue usando heurística nula.

    - Greedy:
        f(n) = h(n)
        Se consigue con usar_coste=False.

    - A*:
        f(n) = g(n) + h(n)
        Se consigue con usar_coste=True y peso_heuristica=1.0.

    - A* ponderado:
        f(n) = g(n) + w · h(n)
        Se consigue con usar_coste=True y peso_heuristica > 1.0.
    """

    abiertos = []
    viene_de = {inicio: None}
    coste = {inicio: 0.0}
    nodos_explorados = 0

    # Si no se pasa heurística, se usa h(n)=0.
    # Así evitamos errores y mantenemos el caso Dijkstra.
    if heuristica is None:
        heuristica = lambda nodo, objetivo: 0

    # Prioridad inicial: g(inicio)=0.
    h_inicial = heuristica(inicio, objetivo)

    if usar_coste:
        prioridad_inicial = 0 + peso_heuristica * h_inicial
    else:
        prioridad_inicial = h_inicial

    heappush(abiertos, (prioridad_inicial, 0.0, inicio))

    while abiertos:
        _, coste_actual, actual = heappop(abiertos)

        # Si este nodo salió con un coste antiguo, se ignora.
        if coste_actual != coste.get(actual, float("inf")):
            continue

        nodos_explorados += 1

        if actual == objetivo:
            return _reconstruir_camino(viene_de, actual), nodos_explorados

        for vecino in _vecinos(actual):
            # g(n): coste de entrar en vecino (GRID + factor sqrt(2) si es diagonal).
            nuevo_coste = coste[actual] + coste_movimiento(actual, vecino)

            h = heuristica(vecino, objetivo)

            if usar_coste:
                prioridad = nuevo_coste + peso_heuristica * h
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
    clave = nombre or config.ALGORITMO
    if clave == "ara_star":
        from planificacion import ara
        return ara.ara_star
    return ALGORITMOS_DISPONIBLES.get(clave, astar)


def _normalizar_algoritmo(algoritmo=None):
    """None → config.ALGORITMO; str → nombre en ALGORITMOS_DISPONIBLES; callable → tal cual."""
    if algoritmo is None:
        return resolver_algoritmo()
    if isinstance(algoritmo, str):
        return resolver_algoritmo(algoritmo)
    return algoritmo


def _normalizar_heuristica(heuristica=None):
    """None → config.HEURISTICA; str → nombre en HEURISTICAS_DISPONIBLES; callable → tal cual."""
    if heuristica is None:
        return resolver_heuristica()
    if isinstance(heuristica, str):
        return resolver_heuristica(heuristica)
    return heuristica


def preparar_ruta(inicio, objetivo, heuristica=None, algoritmo=None):
    """Resuelve un tramo. Si `algoritmo`/`heuristica` son None, se leen de config."""
    from planificacion import ara

    funcion = _normalizar_algoritmo(algoritmo)
    h = _normalizar_heuristica(heuristica)
    camino_celdas, nodos_explorados = funcion(inicio, objetivo, h)

    if funcion is ara.ara_star and ara.ULTIMO_INFORME_ARA is not None:
        # Copia del informe para no perderlo en el siguiente tramo de la mision.
        ara.INFORME_ARA_MISION.append(dict(ara.ULTIMO_INFORME_ARA))

    puntos = [celda_a_mundo(celda) for celda in camino_celdas]
    indice_objetivo = 1 if len(puntos) > 1 else 0

    return camino_celdas, puntos, indice_objetivo, nodos_explorados


def preparar_ruta_desde_config(nombre_heuristica=None):
    heuristica = resolver_heuristica(nombre_heuristica)
    return preparar_ruta(config.CELDA_INICIO, config.CELDA_OBJETIVO, heuristica)
