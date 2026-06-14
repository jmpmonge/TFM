
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

import configuracion.config as config
import planificacion.ara as ara
import planificacion.ara_anytime as ara_anytime

from planificacion.algoritmos import astar, dijkstra, greedy
from planificacion.costes import coste_camino
from planificacion.heuristicas import (
    h_nula,
    h_manhattan,
    h_euclidiana,
    h_octil,
)


# Guardar los costes originales
COSTE_ZONA_1_ORIGINAL = config.COSTE_ZONA_1
COSTE_ZONA_2_ORIGINAL = config.COSTE_ZONA_2
COSTE_ZONA_3_ORIGINAL = config.COSTE_ZONA_3


def restaurar_suelo():
    config.COSTE_ZONA_1 = COSTE_ZONA_1_ORIGINAL
    config.COSTE_ZONA_2 = COSTE_ZONA_2_ORIGINAL
    config.COSTE_ZONA_3 = COSTE_ZONA_3_ORIGINAL
    config.aplicar_costes_zonas(
        COSTE_ZONA_1_ORIGINAL,
        COSTE_ZONA_2_ORIGINAL,
        COSTE_ZONA_3_ORIGINAL,
    )


# =========================================================
# 1. A* CON DISTINTAS HEURÍSTICAS
# =========================================================

restaurar_suelo()

print("=============================================")
print("A* POR HEURÍSTICA")
print("=============================================")

heuristicas = {
    "nula": h_nula,
    "manhattan": h_manhattan,
    "euclidiana": h_euclidiana,
    "octil": h_octil,
}

for nombre, heuristica in heuristicas.items():
    camino, nodos = astar(
        config.CELDA_INICIO,
        config.CELDA_OBJETIVO,
        heuristica
    )

    print(
        f"{nombre:10} | "
        f"celdas={len(camino):3} | "
        f"nodos={nodos:4}"
    )


# =========================================================
# 2. COMPARACIÓN GENERAL
# =========================================================

restaurar_suelo()

print()
print("=============================================")
print("COMPARACIÓN GENERAL CON MANHATTAN")
print("=============================================")

camino, nodos = dijkstra(
    config.CELDA_INICIO,
    config.CELDA_OBJETIVO
)

print(
    f"{'Dijkstra':10} | "
    f"celdas={len(camino):3} | "
    f"nodos={nodos:4}"
)

camino, nodos = astar(
    config.CELDA_INICIO,
    config.CELDA_OBJETIVO,
    h_manhattan
)

print(
    f"{'A*':10} | "
    f"celdas={len(camino):3} | "
    f"nodos={nodos:4}"
)

camino, nodos = greedy(
    config.CELDA_INICIO,
    config.CELDA_OBJETIVO,
    h_manhattan
)

print(
    f"{'Greedy':10} | "
    f"celdas={len(camino):3} | "
    f"nodos={nodos:4}"
)


# =========================================================
# 3. A* CON CAMBIO DE TERRENO DURANTE LA RUTA
# =========================================================

restaurar_suelo()

camino_astar, nodos_astar = astar(
    config.CELDA_INICIO,
    config.CELDA_OBJETIVO,
    h_manhattan
)

coste_astar_antes = coste_camino(camino_astar)

# El suelo cambia después de calcular la ruta
config.COSTE_ZONA_1 *= 30
config.COSTE_ZONA_2 /= 5
config.COSTE_ZONA_3 = 10.0

# A* no vuelve a ejecutarse.
# Se calcula el nuevo coste de la misma ruta.
coste_astar_despues = coste_camino(camino_astar)

print()
print("=============================================")
print("A* CON CAMBIO DE TERRENO DURANTE LA RUTA")
print("=============================================")

print(
    f"Antes   | "
    f"celdas={len(camino_astar):3} | "
    f"nodos={nodos_astar:4} | "
    f"coste={coste_astar_antes:.2f}"
)

print(
    f"Después | "
    f"celdas={len(camino_astar):3} | "
    f"misma ruta | "
    f"coste={coste_astar_despues:.2f}"
)


# =========================================================
# 4. ARA*: OFFLINE Y ANYTIME
# =========================================================

pruebas_ara = [
    {
        "nombre": "ARA* OFFLINE SIN CAMBIO DE SUELO",
        "modo": "offline",
        "cambiar_suelo": False,
    },
    {
        "nombre": "ARA* ANYTIME SIN CAMBIO DE SUELO",
        "modo": "anytime",
        "cambiar_suelo": False,
    },
    {
        "nombre": "ARA* ANYTIME CON CAMBIO DE SUELO",
        "modo": "anytime",
        "cambiar_suelo": True,
    },
]

for prueba in pruebas_ara:

    restaurar_suelo()
    ara_anytime._SUELO_CAMBIANTE_APLICADO = False
    config.SUELO_CAMBIANTE = prueba["cambiar_suelo"]

    camino_ara, nodos_ara = ara.ara_star(
        config.CELDA_INICIO,
        config.CELDA_OBJETIVO,
        h_manhattan,
        modo=prueba["modo"],
        cambiar_suelo=prueba["cambiar_suelo"],
    )

    informe = ara.ULTIMO_INFORME_ARA
    historial = informe.get("historial", informe.get("iteraciones", []))

    print()
    print("=============================================")
    print(prueba["nombre"])
    print("=============================================")
    print(f"modo={informe.get('modo', prueba['modo'])}")
    print(f"cambio_suelo={informe.get('cambiar_suelo', prueba['cambiar_suelo'])}")
    print(f"celdas_finales={len(camino_ara)}")

    for fase in historial:
        print(
            f"  modo={fase.get('modo', '?')} | "
            f"epsilon={fase.get('epsilon', 0):.1f} | "
            f"inicio={fase.get('inicio', fase.get('inicio_fase', '?'))} | "
            f"celdas={fase.get('celdas', len(fase.get('ruta', fase.get('ruta_calculada', [])))):3} | "
            f"coste={fase.get('coste', 0.0):7.2f} | "
            f"nodos={fase.get('nodos', 0):4}"
            + (
                f" | suelo={'SI' if fase.get('suelo_actualizado') else 'NO'}"
                if "suelo_actualizado" in fase else ""
            )
        )

    print(f"Nodos totales={nodos_ara}")

restaurar_suelo()
ara_anytime._SUELO_CAMBIANTE_APLICADO = False
