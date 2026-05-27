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


# --------------------------------------------------------------------------
# ARA* — ultimo informe guardado para logs y comparativas
# --------------------------------------------------------------------------
ULTIMO_INFORME_ARA = None
INFORME_ARA_MISION = []


def ara_star(inicio, objetivo, heuristica, eps_inicial=None, eps_final=None, eps_paso=None):
    """
    ARA* simplificado para el prototipo del TFM.

    Idea principal:
        Se ejecuta varias veces A* ponderado.
        En cada ejecución se usa un valor menor de epsilon.

    Fórmula usada:
        f(n) = g(n) + ε · h(n)

    Interpretación:
        - Con ε alto, la búsqueda da más importancia a la heurística.
        - Con ε = 1, el algoritmo se comporta como A* normal.

    Importante:
        Esta versión NO implementa INCONS ni reutilización interna de nodos.
        Es una aproximación experimental sencilla:
        repite búsquedas con ε decreciente para observar cómo cambia la ruta.

    Retorno:
        camino final encontrado y nodos totales expandidos.
    """
    global ULTIMO_INFORME_ARA

    eps_inicial = config.EPSILON_INICIAL_ARA if eps_inicial is None else eps_inicial
    eps_final = config.EPSILON_FINAL_ARA if eps_final is None else eps_final
    eps_paso = config.EPSILON_PASO_ARA if eps_paso is None else eps_paso

    mejor_camino = []
    nodos_totales = 0
    iteraciones = []

    epsilon = eps_inicial

    while epsilon >= eps_final - 1e-9:
        camino, nodos = astar_ponderado(
            inicio,
            objetivo,
            heuristica,
            peso_heuristica=epsilon,
        )

        iteraciones.append({
            "epsilon": round(epsilon, 4),
            "ruta": list(camino),
            "nodos": nodos,
        })

        nodos_totales += nodos

        if camino:
            mejor_camino = camino

        if epsilon <= eps_final + 1e-9:
            break

        epsilon = max(eps_final, epsilon - eps_paso)

    ULTIMO_INFORME_ARA = {
        "inicio": inicio,
        "objetivo": objetivo,
        "iteraciones": iteraciones,
        "ruta_final": list(mejor_camino),
    }

    return mejor_camino, nodos_totales


ALGORITMOS_DISPONIBLES = {
    "dijkstra": dijkstra,
    "astar": astar,
    "greedy": greedy,
    "astar_ponderado": astar_ponderado,
    "ara_star": ara_star,
}

# ==============================
# NÚCLEO DE BÚSQUEDA
# ==============================

# ============================================================================
# COSTES DEL TERRENO
# ============================================================================

# Factores ambientales por celda.
# Formato:
# (fila, columna): {
#     "pendiente": valor,
#     "traccion": valor,
#     "energia": valor,
# }
#
# De momento puede estar vacío para no alterar los resultados actuales.
# Más adelante aquí se podrán añadir zonas concretas del mapa.
FACTORES_TERRENO = {
    # Ejemplo:
    # (120, 140): {"pendiente": 2.0, "traccion": 1.5, "energia": 1.0},
}

def obtener_factores_terreno(celda):
    """
    Devuelve los factores ambientales asociados a una celda.

    Si la celda no tiene datos específicos, se considera terreno normal:

    - pendiente = 0
    - traccion = 0
    - energia = 0

    Interpretación:
    - pendiente alta aumenta el coste.
    - tracción baja se codifica como penalización alta.
    - energía representa consumo extra estimado.
    """

    factores_por_defecto = {
        "pendiente": 0.0,
        "traccion": 0.0,
        "energia": 0.0,
    }

    return FACTORES_TERRENO.get(celda, factores_por_defecto)

def coste_movimiento(actual, vecino):
    """
    Calcula el coste real de moverse desde una celda a otra.

    Este coste pertenece a g(n), no a h(n).

    Fórmula:

        c(actual, vecino) =
            coste_base
            + peso_pendiente · pendiente
            + peso_traccion · traccion
            + peso_energia · energia

    De momento, si no hay factores ambientales definidos para la celda,
    el coste sigue siendo 1.0.
    """

    coste_base = 1.0

    factores = obtener_factores_terreno(vecino)

    pendiente = factores["pendiente"]
    traccion = factores["traccion"]
    energia = factores["energia"]

    peso_pendiente = 0.4
    peso_traccion = 0.3
    peso_energia = 0.3

    coste = (
        coste_base
        + peso_pendiente * pendiente
        + peso_traccion * traccion
        + peso_energia * energia
    )

    return coste


def coste_camino(camino):
    """Suma g(n) a lo largo de una secuencia de celdas consecutivas."""
    if len(camino) <= 1:
        return 0

    total = 0.0
    for i in range(1, len(camino)):
        total += coste_movimiento(camino[i - 1], camino[i])
    return total


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
    coste = {inicio: 0}
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

    heappush(abiertos, (prioridad_inicial, 0, inicio))

    while abiertos:
        _, coste_actual, actual = heappop(abiertos)

        # Si este nodo salió con un coste antiguo, se ignora.
        if coste_actual != coste.get(actual, float("inf")):
            continue

        nodos_explorados += 1

        if actual == objetivo:
            return _reconstruir_camino(viene_de, actual), nodos_explorados

        for vecino in _vecinos(actual):
            # De momento cada movimiento cuesta 1.
            # Más adelante aquí podrá entrar energía, rugosidad, pendiente, etc.
            nuevo_coste = coste[actual] + coste_movimiento(actual, vecino)

            h = heuristica(vecino, objetivo)

            if usar_coste:
                prioridad = nuevo_coste + peso_heuristica * h
            else:
                prioridad = h

            if vecino not in coste or nuevo_coste < coste[vecino]:
                coste[vecino] = int(nuevo_coste)
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

    if funcion is ara_star and ULTIMO_INFORME_ARA is not None:
        # Copia del informe para no perderlo en el siguiente tramo de la mision.
        INFORME_ARA_MISION.append(dict(ULTIMO_INFORME_ARA))

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
    global INFORME_ARA_MISION

    funcion = algoritmo if algoritmo is not None else resolver_algoritmo()
    if funcion is ara_star:
        # Se vacia al inicio; preparar_ruta ira anadiendo un informe por tramo.
        INFORME_ARA_MISION = []

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


# ==============================
# LOGS DE PLANIFICACION
# ==============================

def _etiqueta_heuristica(nombre):
    if nombre == "manhattan":
        return "Manhattan"
    if nombre == "euclidiana":
        return "Euclidiana"
    return nombre.upper()


def _nodos_informe_ara(informe):
    return sum(it["nodos"] for it in informe["iteraciones"])


def imprimir_tabla_iteraciones_ara(informe):
    """Tabla didactica: una fila por valor de epsilon."""
    print("  ARA* — iteraciones:")
    print("  epsilon | pasos | nodos | celdas")
    print("  --------+-------+-------+-------")

    for it in informe["iteraciones"]:
        pasos = coste_camino(it["ruta"])
        celdas = len(it["ruta"])
        print(
            f"  {it['epsilon']:<7.2f} | {pasos:<5.0f} | {it['nodos']:<5d} | {celdas}"
        )


def imprimir_resumen_planificacion(inicio, objetivos, camino, nodos_totales):
    """Resumen en consola tras planificar la mision."""
    coste = coste_camino(camino)

    print()
    print("=" * 45)
    print("RESUMEN DE PLANIFICACION")
    print("=" * 45)
    print("Algoritmo   :", config.ALGORITMO.upper())
    print("Heuristica  :", _etiqueta_heuristica(config.HEURISTICA))
    print("Inicio grid :", inicio)
    print("Objetivos   :", objetivos)
    print("Longitud    :", len(camino), "celdas")
    print("Coste final :", coste, "pasos")
    print("Nodos vistos:", nodos_totales)

    if config.ALGORITMO == "ara_star" and INFORME_ARA_MISION:
        print("-" * 45)
        print("Detalle ARA* por tramo:")

        for i, informe in enumerate(INFORME_ARA_MISION, start=1):
            iters = informe["iteraciones"]
            coste_ini = coste_camino(iters[0]["ruta"]) if iters else 0
            coste_fin = coste_camino(informe["ruta_final"])
            nodos_tramo = _nodos_informe_ara(informe)

            print(f"  Tramo {i}: {informe['inicio']} -> {informe['objetivo']}")
            imprimir_tabla_iteraciones_ara(informe)
            print(
                f"  pasos {coste_ini:.0f} -> {coste_fin:.0f} | "
                f"nodos {nodos_tramo}"
            )
            print()

        nodos_ara = sum(_nodos_informe_ara(t) for t in INFORME_ARA_MISION)
        print("Totales ARA*:")
        print("  nodos explorados:", nodos_ara)

    print("=" * 45)
    print()

