from heapq import heappush, heappop

from config import ALGORITMO, CELDA_INICIO, CELDA_OBJETIVO
from heuristicas import resolver_heuristica, h_nula, h_manhattan
from mapa import celda_a_mundo, es_libre


# ==============================
# UTILIDADES
# ==============================

def reconstruir_camino(viene_de, actual):
    camino = []
    while actual is not None:
        camino.append(actual)
        actual = viene_de[actual]
    return camino[::-1]


def vecinos(celda):
    fila, col = celda
    movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for df, dc in movimientos:
        nf, nc = fila + df, col + dc
        if es_libre(nf, nc):
            yield (nf, nc)


def coste_camino(camino):
    if not camino:
        return 0
    return len(camino) - 1


def pasos_camino(camino):
    if not camino:
        return 0
    return len(camino) - 1


# ==============================
# FUNCIÓN BASE
# ==============================

def busqueda_a_estrella(inicio, objetivo, heuristica):
    abiertos = []
    heappush(abiertos, (0, inicio))

    viene_de = {inicio: None}
    coste_g = {inicio: 0}
    nodos_explorados = 0

    while abiertos:
        _, actual = heappop(abiertos)
        nodos_explorados += 1

        if actual == objetivo:
            camino = reconstruir_camino(viene_de, actual)
            return camino, nodos_explorados

        for vecino in vecinos(actual):
            nuevo_coste = coste_g[actual] + 1

            if vecino not in coste_g or nuevo_coste < coste_g[vecino]:
                coste_g[vecino] = nuevo_coste
                viene_de[vecino] = actual

                prioridad = nuevo_coste + heuristica(vecino, objetivo)
                heappush(abiertos, (prioridad, vecino))

    return [], nodos_explorados


# ==============================
# ALGORITMOS
# ==============================

def dijkstra(inicio, objetivo):
    return busqueda_a_estrella(inicio, objetivo, h_nula)


def astar(inicio, objetivo, heuristica):
    return busqueda_a_estrella(inicio, objetivo, heuristica)


def resolver_algoritmo():
    algoritmos = {
        "dijkstra": lambda inicio, objetivo, heuristica: dijkstra(inicio, objetivo),
        "astar": astar,
    }
    return algoritmos.get(ALGORITMO, astar)


# ==============================
# PREPARACIÓN DE RUTA
# ==============================

def preparar_ruta(inicio, objetivo, heuristica):
    funcion_algoritmo = resolver_algoritmo()
    camino_celdas, nodos_explorados = funcion_algoritmo(inicio, objetivo, heuristica)

    puntos = [celda_a_mundo(celda) for celda in camino_celdas]
    indice_objetivo = 1 if len(puntos) > 1 else 0

    metricas = {
        "coste": coste_camino(camino_celdas),
        "pasos": pasos_camino(camino_celdas),
        "nodos_explorados": nodos_explorados,
    }

    return camino_celdas, puntos, indice_objetivo, metricas


def preparar_ruta_desde_config(nombre_heuristica=None):
    heuristica = resolver_heuristica(nombre_heuristica)
    return preparar_ruta(CELDA_INICIO, CELDA_OBJETIVO, heuristica)


# ==============================
# BATERÍA Y MISIÓN
# ==============================

def ordenar_objetivos(origen, objetivos):
    return sorted(objetivos, key=lambda obj: h_manhattan(origen, obj))


def filtrar_objetivos_por_bateria(origen, objetivos, base, bateria):
    objetivos_ordenados = ordenar_objetivos(origen, objetivos)

    objetivos_validos = []
    consumo_total = 0
    posicion_actual = origen

    for obj in objetivos_ordenados:
        coste_hasta_obj = h_manhattan(posicion_actual, obj)
        coste_vuelta_base = h_manhattan(obj, base)

        if consumo_total + coste_hasta_obj + coste_vuelta_base > bateria:
            break

        objetivos_validos.append(obj)
        consumo_total += coste_hasta_obj
        posicion_actual = obj

    return objetivos_validos


def planificar_mision(origen, objetivos, base, bateria, nombre_heuristica=None):
    heuristica = resolver_heuristica(nombre_heuristica)

    objetivos_validos = filtrar_objetivos_por_bateria(origen, objetivos, base, bateria)

    rutas = []
    metricas_tramos = []
    posicion_actual = origen
    bateria_consumida = 0

    for obj in objetivos_validos:
        camino, _, _, metricas = preparar_ruta(posicion_actual, obj, heuristica)
        rutas.append(camino)
        metricas_tramos.append(metricas)

        bateria_consumida += metricas["coste"]
        posicion_actual = obj

    camino_base, _, _, metricas_base = preparar_ruta(posicion_actual, base, heuristica)
    rutas.append(camino_base)
    metricas_tramos.append(metricas_base)

    bateria_consumida += metricas_base["coste"]
    bateria_restante = bateria - bateria_consumida

    resumen = {
        "objetivos_planificados": len(objetivos_validos),
        "bateria_total": bateria,
        "bateria_consumida": bateria_consumida,
        "bateria_restante": bateria_restante,
        "coste_total": sum(m["coste"] for m in metricas_tramos),
        "pasos_totales": sum(m["pasos"] for m in metricas_tramos),
        "nodos_explorados_totales": sum(m["nodos_explorados"] for m in metricas_tramos),
    }

    return rutas, metricas_tramos, resumen