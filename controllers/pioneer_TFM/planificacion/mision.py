from configuracion import config
from planificacion import ara
from planificacion import ara_anytime
from planificacion.costes import coste_bateria_camino
from planificacion.heuristicas import h_manhattan


def ordenar_objetivos(origen, objetivos):
    return sorted(objetivos, key=lambda obj: h_manhattan(origen, obj))


def filtrar_objetivos_por_bateria(origen, objetivos, base, bateria,
                                  algoritmo=None, heuristica=None):
    """Filtra objetivos según batería usando rutas planificadas y coste_bateria_camino."""
    from planificacion.algoritmos import _normalizar_algoritmo, _normalizar_heuristica

    funcion = _normalizar_algoritmo(algoritmo)
    h = _normalizar_heuristica(heuristica)
    objetivos_ordenados = ordenar_objetivos(origen, objetivos)

    objetivos_validos = []
    coste_total = 0.0
    posicion_actual = origen

    ara_anytime._OMITIR_SUELO_CAMBIANTE = True
    try:
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
    finally:
        ara_anytime._OMITIR_SUELO_CAMBIANTE = False

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
    from planificacion.algoritmos import _normalizar_algoritmo, _normalizar_heuristica, preparar_ruta

    funcion = _normalizar_algoritmo(algoritmo)
    h = _normalizar_heuristica(heuristica)

    if funcion is ara.ara_star:
        # Se vacia al inicio; preparar_ruta ira anadiendo un informe por tramo.
        ara.INFORME_ARA_MISION.clear()

    costes_iniciales = (
        config.COSTE_ZONA_1,
        config.COSTE_ZONA_2,
        config.COSTE_ZONA_3,
    )
    ara_anytime._SUELO_CAMBIANTE_APLICADO = False

    objetivos_validos = filtrar_objetivos_por_bateria(
        origen, objetivos, base, bateria, algoritmo=funcion, heuristica=h
    )

    # filtrar_objetivos_por_bateria puede activar suelo cambiante en ARA*;
    # restaurar costes originales antes de la planificacion real de la mision.
    config.aplicar_costes_zonas(
        zona1=costes_iniciales[0],
        zona2=costes_iniciales[1],
        zona3=costes_iniciales[2],
    )
    ara_anytime._SUELO_CAMBIANTE_APLICADO = False

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
