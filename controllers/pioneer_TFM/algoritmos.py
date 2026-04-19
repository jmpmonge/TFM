from config import ALGORITMO, HEURISTICA
from heuristicas import HEURISTICAS_DISPONIBLES, h_nula
from mapa import celda_a_mundo, es_libre
from config import CELDA_INICIO, CELDA_OBJETIVO
from heapq import heappush, heappop
from heuristicas import h_manhattan


def resolver_heuristica(nombre=None):
    return HEURISTICAS_DISPONIBLES[nombre or HEURISTICA]

# ==============================
# FUNCIÓN BASE
# ==============================

def a_estrella(inicio, objetivo, heuristica,
               modo="normal", peso=1.5, alpha=0.7, beta=0.3):

    abiertos = [(0, inicio)]
    viene_de = {inicio: None}
    coste = {inicio: 0}
    nodos_explorados = 0

    while abiertos:
        _, actual = heappop(abiertos)
        nodos_explorados += 1

        if actual == objetivo:
            camino = []
            while actual is not None:
                camino.append(actual)
                actual = viene_de[actual]
            return camino[::-1], nodos_explorados

        for df, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nf, nc = actual[0] + df, actual[1] + dc

            if not es_libre(nf, nc):
                continue

            nuevo_coste = coste[actual] + 1

            if (nf, nc) not in coste or nuevo_coste < coste[(nf, nc)]:
                coste[(nf, nc)] = nuevo_coste
                viene_de[(nf, nc)] = actual

                # ==============================
                # 🔥 AQUÍ ESTÁ TODO
                # ==============================

                h = heuristica((nf, nc), objetivo)

                if modo == "normal":
                    f = nuevo_coste + h

                elif modo == "weighted":
                    f = nuevo_coste + peso * h

                elif modo == "multi":
                    h_energy = nuevo_coste # simple
                    f = nuevo_coste + alpha*h + beta*h_energy

                elif modo == "greedy":
                    f = h

                else:
                    f = nuevo_coste + h

                heappush(abiertos, (f, (nf, nc)))

    return [], nodos_explorados


# ==============================
# EXTENSIONES
# ==============================


# Fórmula: f(n) = g(n)
def dijkstra(inicio, objetivo):
    return a_estrella(inicio, objetivo, h_nula, modo="normal")

# Fórmula: f(n) = h(n)
def greedy(inicio, objetivo, heuristica):
    return a_estrella(inicio, objetivo, heuristica, modo="greedy")

# Fórmula: f(n) = g(n) + h(n)
def astar(inicio, objetivo, heuristica):
    return a_estrella(inicio, objetivo, heuristica, modo="normal")

# Fórmula: f(n) = g(n) + w * h(n)
def astar_weighted(inicio, objetivo, heuristica, peso=1.5):
    return a_estrella(inicio, objetivo, heuristica, modo="weighted", peso=peso)

# Fórmula: f(n) = g(n) + alpha * h(n) + beta * h_energy(n)
def astar_multi(inicio, objetivo, heuristica, alpha=0.7, beta=0.3):
    return a_estrella(inicio, objetivo, heuristica, modo="multi", alpha=alpha, beta=beta)


def preparar_ruta(inicio, objetivo, heuristica):
    if ALGORITMO == "astar_weighted":
        camino_celdas, nodos_explorados = astar_weighted(inicio, objetivo, heuristica)
    elif ALGORITMO == "astar_multi":
        camino_celdas, nodos_explorados = astar_multi(inicio, objetivo, heuristica)
    else:
        camino_celdas, nodos_explorados = astar(inicio, objetivo, heuristica)

    puntos = [celda_a_mundo(celda) for celda in camino_celdas]
    indice_objetivo = 1 if len(puntos) > 1 else 0
    return camino_celdas, puntos, indice_objetivo, nodos_explorados


def preparar_ruta_desde_config(nombre_heuristica=None):
    heuristica = resolver_heuristica(nombre_heuristica)
    return preparar_ruta(CELDA_INICIO, CELDA_OBJETIVO, heuristica)

def ordenar_objetivos(origen, objetivos): # ordena los objetivos por distancia a la fuente
    lista = [] # lista de tuplas (distancia, objetivo)

    for obj in objetivos: # para cada objetivo, calcula la distancia a la fuente             
        distancia = abs(obj[0]-origen[0]) + abs(obj[1]-origen[1])
        lista.append((distancia, obj)) # añade la distancia y el objetivo a la lista

    lista.sort() # ordena la lista por distancia

    return [elemento[1] for elemento in lista]

def filtrar_objetivos_por_bateria(origen, objetivos, base, bateria):
    objetivos_ordenados = ordenar_objetivos(origen, objetivos)
    objetivos_validos = []
    coste_total = 0
    pos = origen

    for obj in objetivos_ordenados:
        coste_hasta_obj = h_manhattan(pos, obj)
        coste_vuelta_base = h_manhattan(obj, base)

        if coste_total + coste_hasta_obj + coste_vuelta_base > bateria:
            break

        objetivos_validos.append(obj)
        coste_total += coste_hasta_obj
        pos = obj

    return objetivos_validos

def planificar_mision(origen, objetivos, base, bateria):

    # 1. Filtrar objetivos
    objetivos_validos = filtrar_objetivos_por_bateria(origen, objetivos, base, bateria)

    rutas = []
    pos = origen

    for obj in objetivos_validos:
        camino, _, _, nodos = preparar_ruta(pos, obj, resolver_heuristica())
        rutas.append(camino)
        pos = obj

    # vuelta a base
    camino, _, _, nodos = preparar_ruta(pos, base, resolver_heuristica())
    rutas.append(camino)

    return rutas