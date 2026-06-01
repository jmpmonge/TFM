from configuracion import config
from planificacion.ara import INFORME_ARA_MISION
from planificacion.costes import coste_bateria_camino, coste_camino


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
