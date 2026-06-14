# Este archivo implementa el modo ARA* anytime_simple.
#
# No contiene el núcleo matemático de ARA*.
# Contiene la ejecución por fases:
#
# 1. calcular una ruta con epsilon alto
# 2. avanzar algunos pasos sobre esa ruta
# 3. cambiar el coste del suelo si toca
# 4. recalcular desde la nueva posición
# 5. mantener o sustituir la ruta activa
#
# El estado sigue siendo la celda del grid.
# El suelo no entra como estado: modifica el coste del entorno.

from configuracion import config
from planificacion.ara import _epsilons_ara
from planificacion.costes import coste_camino


_SUELO_CAMBIANTE_APLICADO = False
_OMITIR_SUELO_CAMBIANTE = False


def _anexar_segmento_ruta(ruta_ejecutada, segmento):
    # evita duplicar la celda de unión al encadenar segmentos
    if not segmento:
        return
    if ruta_ejecutada and segmento[0] == ruta_ejecutada[-1]:
        ruta_ejecutada.extend(segmento[1:])
    else:
        ruta_ejecutada.extend(segmento)


def _avanzar_sobre_ruta(ruta_ejecutada, ruta_activa, posicion_actual, pasos):
    # simula avance de hasta `pasos` celdas sobre ruta_activa
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
    if posicion_actual == objetivo or not ruta_activa:
        return posicion_actual

    for idx, celda in enumerate(ruta_activa):
        if celda == posicion_actual:
            _anexar_segmento_ruta(ruta_ejecutada, ruta_activa[idx:])
            break
    return ruta_ejecutada[-1] if ruta_ejecutada else posicion_actual


def actualizar_suelo_cambiante_si_toca(indice_fase):
    # cambia el coste del entorno una sola vez (suelo no es estado)
    global _SUELO_CAMBIANTE_APLICADO

    if _OMITIR_SUELO_CAMBIANTE:
        return False

    if not getattr(config, "SUELO_CAMBIANTE", False):
        return False

    if indice_fase != 1:
        return False

    if _SUELO_CAMBIANTE_APLICADO:
        return False

    nuevo_zona_1 = config.COSTE_ZONA_1 * 30
    nuevo_zona_2 = config.COSTE_ZONA_2 / 5
    nuevo_zona_3 = config.COSTE_ZONA_3

    config.aplicar_costes_zonas(
        zona1=nuevo_zona_1,
        zona2=nuevo_zona_2,
        zona3=nuevo_zona_3,
    )

    print()
    print("=" * 45)
    print("SUELO CAMBIANTE ACTIVADO")
    print("=" * 45)
    print("COSTE_ZONA_1 x30 =", config.COSTE_ZONA_1)
    print("COSTE_ZONA_2 /5  =", config.COSTE_ZONA_2)
    print("COSTE_ZONA_3     =", config.COSTE_ZONA_3)
    print("=" * 45)
    print()

    _SUELO_CAMBIANTE_APLICADO = True
    return True


def reiniciar_suelo_cambiante(costes_iniciales):
    global _SUELO_CAMBIANTE_APLICADO

    _SUELO_CAMBIANTE_APLICADO = False
    config.aplicar_costes_zonas(
        zona1=costes_iniciales[0],
        zona2=costes_iniciales[1],
        zona3=costes_iniciales[2],
    )


def planificar_ara_anytime_simple(inicio, objetivo, heuristica, epsilons=None,
                                  pasos_por_fase=None, cambiar_suelo=True):
    from planificacion.algoritmos import astar_ponderado

    global _OMITIR_SUELO_CAMBIANTE

    epsilons = _epsilons_ara(epsilons)
    pasos_por_fase = config.PASOS_POR_FASE_ARA if pasos_por_fase is None else pasos_por_fase

    ruta_ejecutada = []
    posicion_actual = inicio
    ruta_activa = None
    coste_restante_actual = float("inf")
    historial = []
    nodos_totales = 0

    omitir_anterior = _OMITIR_SUELO_CAMBIANTE
    if not cambiar_suelo:
        _OMITIR_SUELO_CAMBIANTE = True

    try:
        for i, epsilon in enumerate(epsilons):
            # ciclo por fase: calcular ruta → comparar → guardar historial → avanzar
            suelo_actualizado = actualizar_suelo_cambiante_si_toca(i)

            nueva_ruta, nodos = astar_ponderado(
                posicion_actual,
                objetivo,
                heuristica,
                peso_heuristica=epsilon,
            )
            nodos_totales += nodos
            nuevo_coste = coste_camino(nueva_ruta) if nueva_ruta else float("inf")

            ruta_activa_anterior = list(ruta_activa) if ruta_activa else []

            if ruta_activa is None or suelo_actualizado or nuevo_coste < coste_restante_actual:
                ruta_activa = nueva_ruta
                coste_restante_actual = nuevo_coste
                if i == 0:
                    accion = "ruta inicial"
                elif suelo_actualizado:
                    accion = "ruta actualizada por cambio de suelo"
                else:
                    accion = "ruta actualizada"
            else:
                accion = "se mantiene ruta anterior"

            entrada = {
                "modo": "anytime",
                "epsilon": epsilon,
                "inicio": posicion_actual,
                "inicio_fase": posicion_actual,
                "celdas": len(nueva_ruta),
                "ruta_calculada": list(nueva_ruta),
                "coste": nuevo_coste,
                "nodos": nodos,
                "accion": accion,
                "costes_suelo": (
                    config.COSTE_ZONA_1,
                    config.COSTE_ZONA_2,
                    config.COSTE_ZONA_3,
                ),
                "suelo_actualizado": suelo_actualizado,
            }
            if suelo_actualizado:
                entrada["ruta_antes_cambio_suelo"] = ruta_activa_anterior
                entrada["ruta_despues_cambio_suelo"] = list(nueva_ruta)

            historial.append(entrada)

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
    finally:
        _OMITIR_SUELO_CAMBIANTE = omitir_anterior

    return ruta_ejecutada, historial, nodos_totales
