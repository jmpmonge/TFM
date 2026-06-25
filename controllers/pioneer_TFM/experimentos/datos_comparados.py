"""
Script de comparación reproducible de algoritmos de planificación.

Ejecutar desde la raíz del repo:
    python3 controllers/pioneer_TFM/experimentos/datos_comparados.py

Genera experimentos/resultados_experimentos.csv con dos grupos aislados:
  A) comparación estática (suelo fijo, un trayecto inicio→objetivo)
  B) ARA* (suelo cambiante permitido solo dentro de cada ejecución)
"""

import copy
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuracion import config
from planificacion import ara, ara_anytime
from planificacion.algoritmos import astar, dijkstra, greedy
from planificacion.ara import ara_star
from planificacion.costes import coste_camino
from planificacion.heuristicas import HEURISTICAS_DISPONIBLES
from configuracion.config import (
    CELDA_INICIO,
    CELDAS_OBJETIVO,
    EPSILON_FINAL_ARA,
    EPSILON_INICIAL_ARA,
)

COSTES_ORIGINALES = (1.0, 10.0, 20.0)

COLUMNAS_CSV = [
    "grupo_experimento",
    "algoritmo",
    "heuristica",
    "tramo",
    "coste_ponderado",
    "movimientos",
    "celdas",
    "nodos_expandidos",
    "epsilon_inicial",
    "epsilon_final",
    "suelo_cambiante",
    "coste_zona_1_inicial",
    "coste_zona_2_inicial",
    "coste_zona_3_inicial",
    "coste_zona_1_final",
    "coste_zona_2_final",
    "coste_zona_3_final",
]


def cargar_configuracion_base():
    """Captura una copia inmutable del grid y costes al iniciar el script."""
    return {
        "grid": copy.deepcopy(config.GRID),
        "grid_base": copy.deepcopy(config._GRID_BASE),
        "costes": COSTES_ORIGINALES,
        "suelo_cambiante": config.SUELO_CAMBIANTE,
    }


def restaurar_entorno(base):
    """Restaura costes, grid y flags globales antes de cada algoritmo."""
    z1, z2, z3 = base["costes"]
    config.COSTE_ZONA_1 = z1
    config.COSTE_ZONA_2 = z2
    config.COSTE_ZONA_3 = z3
    config.aplicar_costes_zonas(z1, z2, z3)
    config.GRID = copy.deepcopy(base["grid"])
    config._GRID_BASE = copy.deepcopy(base["grid_base"])
    config.SUELO_CAMBIANTE = base["suelo_cambiante"]
    ara_anytime._SUELO_CAMBIANTE_APLICADO = False
    ara_anytime._OMITIR_SUELO_CAMBIANTE = False
    ara.INFORME_ARA_MISION.clear()
    ara.ULTIMO_INFORME_ARA = None
    assert (config.COSTE_ZONA_1, config.COSTE_ZONA_2, config.COSTE_ZONA_3) == COSTES_ORIGINALES


def ejecutar_tramo(algoritmo, heuristica, inicio, objetivo, suelo_cambiante):
    """Ejecuta un único trayecto inicio→objetivo con el algoritmo indicado."""
    config.SUELO_CAMBIANTE = suelo_cambiante
    camino, nodos = algoritmo(inicio, objetivo, heuristica)
    return camino, nodos


def medir_fila(base, grupo, nombre_alg, nombre_h, algoritmo, clave_h, suelo_cambiante):
    restaurar_entorno(base)
    inicio = CELDA_INICIO
    objetivo = CELDAS_OBJETIVO[0]
    heuristica = HEURISTICAS_DISPONIBLES[clave_h]
    costes_iniciales = COSTES_ORIGINALES

    camino, nodos = ejecutar_tramo(algoritmo, heuristica, inicio, objetivo, suelo_cambiante)
    costes_finales = (config.COSTE_ZONA_1, config.COSTE_ZONA_2, config.COSTE_ZONA_3)

    return {
        "grupo_experimento": grupo,
        "algoritmo": nombre_alg,
        "heuristica": nombre_h,
        "tramo": "inicio->objetivo",
        "coste_ponderado": coste_camino(camino) if camino else 0.0,
        "movimientos": max(0, len(camino) - 1),
        "celdas": len(camino),
        "nodos_expandidos": nodos,
        "epsilon_inicial": EPSILON_INICIAL_ARA if grupo == "ara" else "",
        "epsilon_final": EPSILON_FINAL_ARA if grupo == "ara" else "",
        "suelo_cambiante": suelo_cambiante,
        "coste_zona_1_inicial": costes_iniciales[0],
        "coste_zona_2_inicial": costes_iniciales[1],
        "coste_zona_3_inicial": costes_iniciales[2],
        "coste_zona_1_final": costes_finales[0],
        "coste_zona_2_final": costes_finales[1],
        "coste_zona_3_final": costes_finales[2],
    }


def pruebas_estaticas():
    return [
        ("Dijkstra", "Nula", "nula", dijkstra),
        ("A*", "Nula", "nula", astar),
        ("A*", "Manhattan", "manhattan", astar),
        ("A*", "Euclidiana", "euclidiana", astar),
        ("A*", "Octil", "octil", astar),
        ("Greedy", "Nula", "nula", greedy),
        ("Greedy", "Manhattan", "manhattan", greedy),
        ("Greedy", "Euclidiana", "euclidiana", greedy),
        ("Greedy", "Octil", "octil", greedy),
    ]


def pruebas_ara():
    return [
        ("ARA*", "Manhattan", "manhattan"),
        ("ARA*", "Euclidiana", "euclidiana"),
        ("ARA*", "Octil", "octil"),
    ]


def ejecutar_grupo_estatico(base, pruebas):
    resultados = []
    for nombre_alg, nombre_h, clave_h, algoritmo in pruebas:
        resultados.append(
            medir_fila(base, "estatico", nombre_alg, nombre_h, algoritmo, clave_h, False)
        )
    return resultados


def ejecutar_grupo_ara(base):
    resultados = []
    for nombre_alg, nombre_h, clave_h in pruebas_ara():
        resultados.append(
            medir_fila(base, "ara", nombre_alg, nombre_h, ara_star, clave_h, True)
        )
    return resultados


def clave_comparacion(fila):
    return (fila["algoritmo"], fila["heuristica"])


def verificar_reproducibilidad(base):
    normal = ejecutar_grupo_estatico(base, pruebas_estaticas())
    inverso = ejecutar_grupo_estatico(base, list(reversed(pruebas_estaticas())))

    claves = ("coste_ponderado", "movimientos", "celdas", "nodos_expandidos")
    mapa_normal = {clave_comparacion(f): f for f in normal}
    mapa_inverso = {clave_comparacion(f): f for f in inverso}

    assert set(mapa_normal) == set(mapa_inverso), "Conjunto de pruebas distinto entre ordenes"
    for clave in mapa_normal:
        for campo in claves:
            assert mapa_normal[clave][campo] == mapa_inverso[clave][campo], (
                f"Orden altera {clave} campo {campo}: "
                f"{mapa_normal[clave][campo]} vs {mapa_inverso[clave][campo]}"
            )

    return normal


def verificar_coherencia_estatico(resultados):
    por_alg = {(r["algoritmo"], r["heuristica"]): r for r in resultados}

    for fila in resultados:
        assert (
            fila["coste_zona_1_inicial"],
            fila["coste_zona_2_inicial"],
            fila["coste_zona_3_inicial"],
        ) == COSTES_ORIGINALES

    dijkstra = por_alg[("Dijkstra", "Nula")]["coste_ponderado"]
    astar_nula = por_alg[("A*", "Nula")]["coste_ponderado"]
    assert dijkstra == astar_nula, f"Dijkstra ({dijkstra}) != A* Nula ({astar_nula})"

    costes_astar = {
        por_alg[("A*", h)]["coste_ponderado"]
        for h in ("Nula", "Manhattan", "Euclidiana", "Octil")
    }
    assert len(costes_astar) == 1, f"A* estáticos con costes distintos: {costes_astar}"


def imprimir_tabla(resultados):
    columnas_visibles = [
        ("Grupo", "grupo_experimento"),
        ("Algoritmo", "algoritmo"),
        ("Heurística", "heuristica"),
        ("Coste pond.", "coste_ponderado"),
        ("Movimientos", "movimientos"),
        ("Celdas", "celdas"),
        ("Nodos", "nodos_expandidos"),
        ("Suelo camb.", "suelo_cambiante"),
    ]

    def fmt(clave, valor):
        if clave == "coste_ponderado":
            return f"{valor:.6f}"
        if clave == "suelo_cambiante":
            return str(valor)
        return str(valor)

    anchos = []
    for titulo, clave in columnas_visibles:
        ancho = len(titulo)
        for fila in resultados:
            ancho = max(ancho, len(fmt(clave, fila[clave])))
        anchos.append(ancho)

    cabecera = " ".join(t.ljust(a) for (t, _), a in zip(columnas_visibles, anchos))
    print(cabecera)
    print("-" * len(cabecera))
    for fila in resultados:
        print(" ".join(fmt(c, fila[c]).ljust(a) for (_, c), a in zip(columnas_visibles, anchos)))


def exportar_csv(resultados, ruta_csv):
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS_CSV)
        writer.writeheader()
        for fila in resultados:
            writer.writerow(fila)


if __name__ == "__main__":
    base = cargar_configuracion_base()
    restaurar_entorno(base)

    print("Configuración base:")
    print(f"  inicio={CELDA_INICIO}  objetivo={CELDAS_OBJETIVO[0]}")
    print(f"  grid={config.FILAS_MAPA}x{config.COLUMNAS_MAPA}  costes={COSTES_ORIGINALES}")
    print()

    estaticos = verificar_reproducibilidad(base)
    verificar_coherencia_estatico(estaticos)
    ara_resultados = ejecutar_grupo_ara(base)

    todos = estaticos + ara_resultados

    print("Comparación estática (orden normal, verificada también en orden inverso):")
    imprimir_tabla(estaticos)
    print()
    print("Experimento ARA* (restauración previa a cada heurística):")
    imprimir_tabla(ara_resultados)

    ruta_csv = os.path.join(os.path.dirname(__file__), "resultados_experimentos.csv")
    exportar_csv(todos, ruta_csv)
    print(f"\nCSV guardado en: {ruta_csv}")
    print("Verificaciones OK: costes iniciales (1,10,20), Dijkstra=A* Nula, A* óptimos iguales, orden invariante.")
