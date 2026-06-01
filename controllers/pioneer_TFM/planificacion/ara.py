# Este archivo implementa ARA* siguiendo el pseudocódigo de la memoria.
#
# Aunque el archivo tiene varias funciones, cada una representa una pieza del pseudocódigo:
#
# _key_ara:
#     calcula KEY(s)
#
# _sacar_menor_open:
#     saca de OPEN el menor nodo
#
# _reconstruir_camino_desde_sucesores:
#     reconstruye la ruta final
#
# _improve_path_ara:
#     hace la reparación principal
#
# planificar_ara_offline:
#     crea las listas, baja epsilon y guarda el historial
#
# ara_star:
#     decide si usar offline o anytime

from planificacion.costes import coste_camino, coste_movimiento


ULTIMO_INFORME_ARA = None
INFORME_ARA_MISION = []


def _epsilons_ara(epsilons=None):
    from configuracion import config

    if epsilons is not None:
        return epsilons

    valores = []
    epsilon = config.EPSILON_INICIAL_ARA

    # lista de epsilons: 5 -> 4 -> 3 -> 2 -> 1
    while epsilon >= config.EPSILON_FINAL_ARA:
        valores.append(round(epsilon, 2))
        epsilon -= config.EPSILON_PASO_ARA

    return valores


def _key_ara(s, inicio, g, heuristica, epsilon):
    g_s = g.get(s, float("inf"))
    if g_s == float("inf"):
        return float("inf")
    return g_s + epsilon * heuristica(inicio, s)


def _sacar_menor_open(open_list, inicio, g, heuristica, epsilon):
    # se saca el nodo con menor KEY
    s = min(open_list, key=lambda nodo: _key_ara(nodo, inicio, g, heuristica, epsilon))
    open_list.remove(s)
    return s


def _reconstruir_camino_desde_sucesores(inicio, objetivo, sucesor):
    if inicio not in sucesor and inicio != objetivo:
        return []

    camino = [inicio]
    actual = inicio
    while actual != objetivo:
        if actual not in sucesor:
            return []
        actual = sucesor[actual]
        camino.append(actual)
    return camino


def _improve_path_ara(inicio, g, sucesor, open_list, closed, incons, heuristica, epsilon):
    from planificacion.algoritmos import _vecinos

    nodos_iteracion = 0

    while open_list:
        # calcular KEY(inicio)
        key_inicio = _key_ara(inicio, inicio, g, heuristica, epsilon)

        # calcular menor KEY de OPEN
        menor_key = float("inf")
        for s in open_list:
            key_s = _key_ara(s, inicio, g, heuristica, epsilon)
            if key_s < menor_key:
                menor_key = key_s

        # si ningún nodo de OPEN mejora KEY(inicio), se termina esta fase
        if menor_key >= key_inicio:
            break

        # sacar de OPEN el nodo con menor KEY
        s = _sacar_menor_open(open_list, inicio, g, heuristica, epsilon)

        # el nodo procesado pasa a CLOSED
        closed.add(s)

        # cada nodo extraído de OPEN cuenta como nodo explorado
        nodos_iteracion += 1

        # g(s): coste conocido desde s hasta el objetivo
        g_s = g.get(s, float("inf"))

        # En el grid, Pred(s) se obtiene como vecinos libres de s.
        for s_pred in _vecinos(s):
            if s_pred not in g:
                g[s_pred] = float("inf")

            # c_nuevo = c(s_pred, s) + g(s)
            coste_nuevo = coste_movimiento(s_pred, s) + g_s

            if coste_nuevo < g[s_pred]:
                # si mejora, se actualiza g y sucesor
                g[s_pred] = coste_nuevo
                sucesor[s_pred] = s

                if s_pred not in closed:
                    # si no estaba cerrado, se mete en OPEN
                    if s_pred not in open_list:
                        open_list.append(s_pred)
                else:
                    # si ya estaba cerrado, pasa a INCONS
                    incons.add(s_pred)

    return nodos_iteracion


def planificar_ara_offline(inicio, objetivo, heuristica, epsilons=None):
    epsilons = _epsilons_ara(epsilons)
    historial = []
    mejor_camino = []
    nodos_totales = 0

    # g(s_goal) = 0
    g = {objetivo: 0.0}

    # sucesor permite reconstruir la ruta inicio -> objetivo
    sucesor = {}

    # OPEN empieza con el objetivo
    open_list = [objetivo]

    # CLOSED: nodos procesados en esta fase
    closed = set()

    # INCONS: nodos cerrados cuyo coste mejora
    incons = set()

    for i, epsilon in enumerate(epsilons):
        nodos_iteracion = _improve_path_ara(
            inicio, g, sucesor, open_list, closed, incons, heuristica, epsilon,
        )
        nodos_totales += nodos_iteracion

        if g.get(inicio, float("inf")) < float("inf"):
            camino = _reconstruir_camino_desde_sucesores(inicio, objetivo, sucesor)
            coste = coste_camino(camino)
            if camino:
                mejor_camino = camino
        else:
            camino = []
            coste = float("inf")

        historial.append({
            "epsilon": epsilon,
            "ruta": list(camino),
            "coste": coste,
            "nodos": nodos_iteracion,
        })

        # al bajar epsilon, INCONS vuelve a OPEN
        if i < len(epsilons) - 1:
            for s in incons:
                if s not in open_list:
                    open_list.append(s)

            incons.clear()
            closed.clear()

    return mejor_camino, historial, nodos_totales

def ara_star(inicio, objetivo, heuristica, eps_inicial=None, eps_final=None, eps_paso=None):
    from configuracion import config

    global ULTIMO_INFORME_ARA

    # lista de epsilons: 2.5 -> 2.0 -> 1.5 -> 1.0
    epsilons = _epsilons_ara()

    # decide si ARA* se ejecuta en modo offline o anytime
    modo = getattr(config, "MODO_ARA", "offline")

    if modo == "anytime_simple":
        from planificacion.ara_anytime import planificar_ara_anytime_simple

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
