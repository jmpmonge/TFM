from heapq import heappop, heappush
import math

from configuracion import config
from planificacion.heuristicas import resolver_heuristica, h_nula, h_manhattan
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


# --------------------------------------------------------------------------
# ARA* — ultimo informe guardado para logs y comparativas
# --------------------------------------------------------------------------
ULTIMO_INFORME_ARA = None
INFORME_ARA_MISION = []


def _epsilons_ara(epsilons=None, eps_inicial=None, eps_final=None, eps_paso=None):
    """Lista de epsilon decreciente a partir de config o de una secuencia explicita."""
    if epsilons is not None:
        return [round(float(e), 4) for e in epsilons]

    eps_inicial = config.EPSILON_INICIAL_ARA if eps_inicial is None else eps_inicial
    eps_final = config.EPSILON_FINAL_ARA if eps_final is None else eps_final
    eps_paso = config.EPSILON_PASO_ARA if eps_paso is None else eps_paso

    valores = []
    epsilon = eps_inicial
    while epsilon >= eps_final - 1e-9:
        valores.append(round(epsilon, 4))
        if epsilon <= eps_final + 1e-9:
            break
        epsilon = max(eps_final, epsilon - eps_paso)
    return valores


def planificar_ara_offline(inicio, objetivo, heuristica, epsilons=None,
                           eps_inicial=None, eps_final=None, eps_paso=None):
    """
    ARA* simplificado offline (sin INCONS): A* ponderado con epsilon decreciente.

    Calcula todas las rutas antes de mover el robot. Devuelve la ultima ruta
    (normalmente la de menor epsilon), el historial y los nodos totales.
    """
    epsilons = _epsilons_ara(epsilons, eps_inicial, eps_final, eps_paso)
    historial = []
    mejor_camino = []
    nodos_totales = 0

    for epsilon in epsilons:
        camino, nodos = astar_ponderado(
            inicio,
            objetivo,
            heuristica,
            peso_heuristica=epsilon,
        )
        coste = coste_camino(camino)
        historial.append({
            "epsilon": epsilon,
            "ruta": list(camino),
            "coste": coste,
            "nodos": nodos,
        })
        nodos_totales += nodos
        if camino:
            mejor_camino = camino

    return mejor_camino, historial, nodos_totales


def _anexar_segmento_ruta(ruta_ejecutada, segmento):
    """Une segmento evitando duplicar la celda de union."""
    if not segmento:
        return
    if ruta_ejecutada and segmento[0] == ruta_ejecutada[-1]:
        ruta_ejecutada.extend(segmento[1:])
    else:
        ruta_ejecutada.extend(segmento)


def _avanzar_sobre_ruta(ruta_ejecutada, ruta_activa, posicion_actual, pasos):
    """Avanza hasta `pasos` celdas siguiendo ruta_activa desde posicion_actual."""
    if not ruta_activa:
        return posicion_actual

    inicio_idx = 0
    for idx, celda in enumerate(ruta_activa):
        if celda == posicion_actual:
            inicio_idx = idx
            break

    fin_idx = min(inicio_idx + pasos, len(ruta_activa) - 1)
    _anexar_segmento_ruta(ruta_ejecutada, ruta_activa[inicio_idx:fin_idx + 1])
    return ruta_ejecutada[-1]


def _completar_hasta_objetivo(ruta_ejecutada, ruta_activa, posicion_actual, objetivo):
    """Anade el tramo restante de ruta_activa si aun no se ha llegado al objetivo."""
    if posicion_actual == objetivo or not ruta_activa:
        return posicion_actual

    for idx, celda in enumerate(ruta_activa):
        if celda == posicion_actual:
            _anexar_segmento_ruta(ruta_ejecutada, ruta_activa[idx:])
            break
    return ruta_ejecutada[-1] if ruta_ejecutada else posicion_actual


def planificar_ara_anytime_simple(inicio, objetivo, heuristica, epsilons=None,
                                  pasos_por_fase=None):
    """
    ARA* anytime simplificado: simulacion por fases sin hilos.

    1. Calcula ruta con epsilon alto.
    2. Avanza pasos_por_fase celdas.
    3. Recalcula desde la posicion alcanzada con epsilon menor.
    4. Sustituye la ruta activa si mejora el coste restante.
    """
    epsilons = _epsilons_ara(epsilons)
    pasos_por_fase = config.PASOS_POR_FASE_ARA if pasos_por_fase is None else pasos_por_fase

    ruta_ejecutada = []
    posicion_actual = inicio
    ruta_activa = None
    coste_restante_actual = float("inf")
    historial = []
    nodos_totales = 0

    for i, epsilon in enumerate(epsilons):
        nueva_ruta, nodos = astar_ponderado(
            posicion_actual,
            objetivo,
            heuristica,
            peso_heuristica=epsilon,
        )
        nodos_totales += nodos
        nuevo_coste = coste_camino(nueva_ruta) if nueva_ruta else float("inf")

        if ruta_activa is None or nuevo_coste < coste_restante_actual:
            ruta_activa = nueva_ruta
            coste_restante_actual = nuevo_coste
            accion = "ruta inicial" if i == 0 else "ruta actualizada"
        else:
            accion = "se mantiene ruta anterior"

        historial.append({
            "epsilon": epsilon,
            "inicio_fase": posicion_actual,
            "ruta_calculada": list(nueva_ruta),
            "coste": nuevo_coste,
            "nodos": nodos,
            "accion": accion,
        })

        if not ruta_activa:
            break

        posicion_actual = _avanzar_sobre_ruta(
            ruta_ejecutada, ruta_activa, posicion_actual, pasos_por_fase
        )

        if posicion_actual == objetivo:
            break

    if posicion_actual != objetivo:
        posicion_actual = _completar_hasta_objetivo(
            ruta_ejecutada, ruta_activa, posicion_actual, objetivo
        )

    return ruta_ejecutada, historial, nodos_totales


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
        Esta version NO implementa INCONS ni reutilizacion interna de nodos.
        Es una aproximacion experimental sencilla basada en reduccion progresiva
        de epsilon (A* ponderado iterativo).

    Modos (config.MODO_ARA):
        - offline: calcula todas las iteraciones y devuelve la ultima ruta.
        - anytime_simple: simula avance por fases y puede cambiar de trayectoria.

    Retorno:
        camino final (o ejecutado en anytime) y nodos totales expandidos.
    """
    global ULTIMO_INFORME_ARA

    epsilons = _epsilons_ara(None, eps_inicial, eps_final, eps_paso)
    modo = getattr(config, "MODO_ARA", "offline")

    if modo == "anytime_simple":
        camino, historial, nodos_totales = planificar_ara_anytime_simple(
            inicio, objetivo, heuristica, epsilons=epsilons
        )
        ULTIMO_INFORME_ARA = {
            "modo": "anytime_simple",
            "inicio": inicio,
            "objetivo": objetivo,
            "historial": historial,
            "ruta_final": list(camino),
            "ruta_ejecutada": list(camino),
        }
    else:
        camino, historial, nodos_totales = planificar_ara_offline(
            inicio, objetivo, heuristica, epsilons=epsilons
        )
        ULTIMO_INFORME_ARA = {
            "modo": "offline",
            "inicio": inicio,
            "objetivo": objetivo,
            "iteraciones": historial,
            "ruta_final": list(camino),
        }

    return camino, nodos_totales


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

def coste_base_celda(celda):
    """Coste base del terreno: celda libre (0) → 1; valor > 0 → ese valor."""
    valor = config.GRID[celda[0]][celda[1]]
    return 1.0 if valor == 0 else float(valor)


def coste_movimiento(actual, vecino):
    """
    Coste g(n) de entrar en la celda vecino según GRID y tipo de paso:
    - ortogonal: coste base de la celda
    - diagonal: coste base × sqrt(2)
    """
    base = coste_base_celda(vecino)

    df = abs(vecino[0] - actual[0])
    dc = abs(vecino[1] - actual[1])
    if df == 1 and dc == 1:
        return base * math.sqrt(2)
    return base


def coste_camino(camino):
    """Suma g(n) a lo largo de una secuencia de celdas consecutivas."""
    if len(camino) <= 1:
        return 0

    total = 0.0
    for i in range(1, len(camino)):
        total += coste_movimiento(camino[i - 1], camino[i])
    return total


def coste_bateria_movimiento(actual, vecino):
    """
    Consumo energético al pasar de actual a vecino.
    Usa el mismo coste base del terreno; el factor diagonal depende de config.
    """
    base = coste_base_celda(vecino)

    if config.USAR_FACTOR_DIAGONAL_BATERIA:
        df = abs(vecino[0] - actual[0])
        dc = abs(vecino[1] - actual[1])
        if df == 1 and dc == 1:
            return base * math.sqrt(2)
    return base


def coste_bateria_camino(camino):
    """Batería consumida recorriendo un camino de celdas consecutivas."""
    if len(camino) <= 1:
        return 0.0

    total = 0.0
    for i in range(1, len(camino)):
        total += coste_bateria_movimiento(camino[i - 1], camino[i])
    return total


def log_consumo_bateria_celda(celda, origen, consumo_tramo, consumo_acum, bateria_restante):
    """Consola de depuración: una línea por celda atravesada."""
    if not config.LOG_BATERIA_CELDAS:
        return

    valor_grid = config.GRID[celda[0]][celda[1]]
    factor_diag = "×√2" if (
        config.USAR_FACTOR_DIAGONAL_BATERIA
        and abs(celda[0] - origen[0]) == 1
        and abs(celda[1] - origen[1]) == 1
    ) else ""
    print(
        f"[BATERIA] celda={celda} valor_grid={valor_grid} "
        f"consumo_celda={consumo_tramo:.2f}{factor_diag} "
        f"acumulado={consumo_acum:.2f} restante={bateria_restante:.2f}"
    )


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
    return ALGORITMOS_DISPONIBLES.get(nombre or config.ALGORITMO, astar)


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
    funcion = _normalizar_algoritmo(algoritmo)
    h = _normalizar_heuristica(heuristica)
    camino_celdas, nodos_explorados = funcion(inicio, objetivo, h)

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


def filtrar_objetivos_por_bateria(origen, objetivos, base, bateria,
                                  algoritmo=None, heuristica=None):
    """Filtra objetivos según batería usando rutas planificadas y coste_bateria_camino."""
    funcion = _normalizar_algoritmo(algoritmo)
    h = _normalizar_heuristica(heuristica)
    objetivos_ordenados = ordenar_objetivos(origen, objetivos)

    objetivos_validos = []
    coste_total = 0.0
    posicion_actual = origen

    for obj in objetivos_ordenados:
        camino_ida, _ = funcion(posicion_actual, obj, h)
        if not camino_ida:
            break
        coste_hasta_obj = coste_bateria_camino(camino_ida)

        camino_vuelta, _ = funcion(obj, base, h)
        coste_vuelta_base = coste_bateria_camino(camino_vuelta) if camino_vuelta else float("inf")

        if coste_total + coste_hasta_obj + coste_vuelta_base > bateria:
            if config.LOG_BATERIA_OBJETIVOS:
                print(
                    f"[BATERIA] objetivo {obj} descartado: "
                    f"coste_mision={coste_total + coste_hasta_obj:.1f} + "
                    f"vuelta={coste_vuelta_base:.1f} > {bateria}"
                )
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

    Por defecto usa el algoritmo y la heurística definidos en `config` (p. ej.
    tras el menú interactivo o los valores por defecto de config.py). Para
    comparativas (datos_comparados.py) se pueden inyectar manualmente vía
    `algoritmo=` y `heuristica=` (función o nombre str).
    """
    global INFORME_ARA_MISION

    funcion = _normalizar_algoritmo(algoritmo)
    h = _normalizar_heuristica(heuristica)

    if funcion is ara_star:
        # Se vacia al inicio; preparar_ruta ira anadiendo un informe por tramo.
        INFORME_ARA_MISION = []

    objetivos_validos = filtrar_objetivos_por_bateria(
        origen, objetivos, base, bateria, algoritmo=funcion, heuristica=h
    )

    rutas = []
    nodos_totales = 0
    posicion_actual = origen

    for obj in objetivos_validos:
        camino, _, _, nodos = preparar_ruta(posicion_actual, obj, h, funcion)
        rutas.append(camino)
        nodos_totales += nodos
        posicion_actual = obj

    camino_vuelta, _, _, nodos = preparar_ruta(posicion_actual, base, h, funcion)
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
    if nombre == "octil":
        return "Octil"
    return nombre.upper()


def _nodos_informe_ara(informe):
    if informe.get("modo") == "anytime_simple":
        return sum(it["nodos"] for it in informe.get("historial", []))
    return sum(it["nodos"] for it in informe.get("iteraciones", []))


def imprimir_tabla_iteraciones_ara(informe):
    """Tabla didactica: una fila por valor de epsilon (modo offline)."""
    print("  ARA* — iteraciones (offline):")
    print("  epsilon | coste | nodos | celdas")
    print("  --------+-------+-------+-------")

    for it in informe.get("iteraciones", []):
        coste = it.get("coste", coste_camino(it["ruta"]))
        celdas = len(it["ruta"])
        print(
            f"  {it['epsilon']:<7.2f} | {coste:<5.0f} | {it['nodos']:<5d} | {celdas}"
        )


def imprimir_historial_ara_anytime(informe):
    """Consola: una linea por fase del modo anytime_simple."""
    print("  ARA* — fases (anytime_simple):")
    for entry in informe.get("historial", []):
        print(
            f"  epsilon={entry['epsilon']} | coste={entry['coste']:.1f} | "
            f"nodos={entry['nodos']} | accion={entry['accion']}"
        )


def imprimir_detalle_informe_ara(informe):
    """Imprime el historial segun el modo ARA* del informe."""
    modo = informe.get("modo", "offline")
    print(f"  Modo ARA*: {modo}")
    if modo == "anytime_simple":
        imprimir_historial_ara_anytime(informe)
    else:
        imprimir_tabla_iteraciones_ara(informe)


def imprimir_resumen_planificacion(inicio, objetivos, camino, nodos_totales):
    """Resumen en consola tras planificar la mision."""
    coste = coste_camino(camino)
    coste_energia = coste_bateria_camino(camino)

    print()
    print("=" * 45)
    print("RESUMEN DE PLANIFICACION")
    print("=" * 45)
    print("Algoritmo   :", config.ALGORITMO.upper())
    print("Heuristica  :", _etiqueta_heuristica(config.HEURISTICA))
    print("Inicio grid :", inicio)
    print("Objetivos   :", objetivos)
    print("Longitud    :", len(camino), "celdas")
    print("Coste g     :", f"{coste:.2f}", "(planificacion)")
    print("Coste energia:", f"{coste_energia:.2f}", "(bateria)")
    print("Factor diag.:", config.USAR_FACTOR_DIAGONAL_BATERIA)
    print("Nodos vistos:", nodos_totales)

    if config.ALGORITMO == "ara_star" and INFORME_ARA_MISION:
        print("-" * 45)
        print("Detalle ARA* por tramo:")

        for i, informe in enumerate(INFORME_ARA_MISION, start=1):
            nodos_tramo = _nodos_informe_ara(informe)
            print(f"  Tramo {i}: {informe['inicio']} -> {informe['objetivo']}")
            imprimir_detalle_informe_ara(informe)

            if informe.get("modo") == "anytime_simple":
                coste_fin = coste_camino(informe.get("ruta_ejecutada", informe["ruta_final"]))
                print(
                    f"  celdas ejecutadas: {len(informe.get('ruta_ejecutada', []))} | "
                    f"coste_g={coste_fin:.1f} | nodos {nodos_tramo}"
                )
            else:
                iters = informe.get("iteraciones", [])
                coste_ini = iters[0]["coste"] if iters else 0
                coste_fin = coste_camino(informe["ruta_final"])
                print(
                    f"  coste {coste_ini:.0f} -> {coste_fin:.0f} | "
                    f"nodos {nodos_tramo}"
                )
            print()

        nodos_ara = sum(_nodos_informe_ara(t) for t in INFORME_ARA_MISION)
        print("Totales ARA*:")
        print("  nodos explorados:", nodos_ara)

    print("=" * 45)
    print()

