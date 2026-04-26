"""
=========================================================================
ESTE ARCHIVO ES UN SCRIPT EJECUTABLE, NO UN MÓDULO.
=========================================================================

No lo importa nadie del controlador. Sirve para lanzar offline la misma
planificación que ejecuta el robot en Webots, pero variando algoritmo y
heurística para comparar métricas.

Reutiliza directamente la lógica del controlador real:
  - `filtrar_objetivos_por_bateria` y `planificar_mision` de
    `planificacion.algoritmos` (las mismas funciones que se invocan desde
    `pioneer_TFM.py`).
  - `HEURISTICAS_DISPONIBLES` y `astar / greedy / dijkstra` también vienen
    de los módulos del controlador.

Uso:
    python3 controllers/pioneer_TFM/experimentos/datos_comparados.py

Salida:
  - Tabla por consola con: longitud de ruta, coste, nodos expandidos,
    tiempo, eficiencia, factor de expansión y desviación frente a
    A*+Manhattan.
  - Fichero `experimentos/resultados_experimentos.csv` con las mismas
    métricas (formato apto para Excel y para la memoria del TFM).
"""

import csv
import os
import sys
import time

# Permite ejecutar este script directamente añadiendo la raíz del controlador
# (la carpeta padre, donde están planificacion/, configuracion/, etc.) al sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planificacion.algoritmos import (
    astar,
    dijkstra,
    greedy,
    filtrar_objetivos_por_bateria,
    planificar_mision,
)
from configuracion.config import BATERIA_MAX, CELDA_INICIO, CELDAS_OBJETIVO
from planificacion.heuristicas import HEURISTICAS_DISPONIBLES


# ============================================================================
# UTILIDADES
# ============================================================================

def aplanar_rutas(rutas):
    """Une los tramos de una misión en un único camino, sin duplicar uniones."""
    camino = []
    for i, ruta in enumerate(rutas):
        if not ruta:
            return []  # un tramo sin solución invalida la misión completa
        if i == 0:
            camino.extend(ruta)
        else:
            camino.extend(ruta[1:])
    return camino


def lanzar_mision(algoritmo, heuristica, inicio, base):
    """Wrapper para llamar a `planificar_mision` con un algoritmo/heurística fijos."""
    return planificar_mision(
        inicio,
        CELDAS_OBJETIVO,
        base,
        BATERIA_MAX,
        devolver_nodos=True,
        algoritmo=algoritmo,
        heuristica=heuristica,
    )


# ============================================================================
# MEDICIÓN
# ============================================================================

def medir(nombre_algoritmo, nombre_heuristica, funcion, coste_optimo_referencia):
    t0 = time.perf_counter()
    rutas, nodos = funcion()
    t1 = time.perf_counter()

    coste = max(0, len(aplanar_rutas(rutas)) - 1)
    tiempo = t1 - t0
    eficiencia = (coste / nodos * 100.0) if nodos else 0.0
    expansion = (nodos / coste) if coste else 0.0
    diferencia_coste = coste - coste_optimo_referencia

    if diferencia_coste == 0:
        comparacion_referencia = "igual"
    elif diferencia_coste > 0:
        comparacion_referencia = f"+{diferencia_coste} pasos"
    else:
        comparacion_referencia = f"{diferencia_coste} pasos"

    return {
        "algoritmo": nombre_algoritmo,
        "heuristica": nombre_heuristica,
        "coste": coste,
        "nodos": nodos,
        "tiempo": tiempo,
        "eficiencia": eficiencia,
        "expansion": expansion,
        "comparacion_referencia": comparacion_referencia,
    }


# ============================================================================
# SALIDA
# ============================================================================

def imprimir_tabla(resultados):
    columnas = [
        ("Algoritmo", "algoritmo"),
        ("Heurística", "heuristica"),
        ("Coste total (pasos)", "coste"),
        ("Nodos expandidos", "nodos"),
        ("Tiempo ejecución (s)", "tiempo"),
        ("Eficiencia coste/nodos (%)", "eficiencia"),
        ("Factor expansión", "expansion"),
        ("Diferencia frente a A*+Manhattan", "comparacion_referencia"),
    ]

    def formatear(clave, valor):
        if clave == "tiempo":
            return f"{valor:.6g}"
        if clave == "eficiencia":
            return f"{valor:.1f}"
        if clave == "expansion":
            return f"{valor:.2f}"
        return str(valor)

    anchos = []
    for titulo, clave in columnas:
        ancho = len(titulo)
        for resultado in resultados:
            ancho = max(ancho, len(formatear(clave, resultado[clave])))
        anchos.append(ancho)

    cabecera = " ".join(
        titulo.ljust(ancho) for (titulo, _), ancho in zip(columnas, anchos)
    )
    separador = "-" * len(cabecera)

    print(cabecera)
    print(separador)

    for resultado in resultados:
        fila = " ".join(
            formatear(clave, resultado[clave]).ljust(ancho)
            for (_, clave), ancho in zip(columnas, anchos)
        )
        print(fila)


def exportar_csv(resultados, ruta_csv):
    columnas = [
        ("algoritmo", "algoritmo"),
        ("heuristica", "heuristica"),
        ("coste_total_pasos", "coste"),
        ("nodos_expandidos", "nodos"),
        ("tiempo_ejecucion_s", "tiempo"),
        ("eficiencia_coste_sobre_nodos_pct", "eficiencia"),
        ("factor_expansion_nodos_por_paso", "expansion"),
        ("diferencia_coste_frente_astar_manhattan", "comparacion_referencia"),
    ]

    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[nombre_csv for nombre_csv, _ in columnas])
        writer.writeheader()
        for resultado in resultados:
            writer.writerow({
                nombre_csv: resultado[clave_resultado]
                for nombre_csv, clave_resultado in columnas
            })


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    inicio = CELDA_INICIO
    base = CELDA_INICIO

    objetivos = filtrar_objetivos_por_bateria(inicio, CELDAS_OBJETIVO, base, BATERIA_MAX)

    rutas_optimas, _ = lanzar_mision(astar, HEURISTICAS_DISPONIBLES["manhattan"], inicio, base)
    coste_optimo = max(0, len(aplanar_rutas(rutas_optimas)) - 1)

    heuristicas = [
        ("Nula", "nula"),
        ("Manhattan", "manhattan"),
        ("Euclidiana", "euclidiana"),
    ]

    pruebas = []

    for nombre, clave in heuristicas:
        pruebas.append((
            "A*",
            nombre,
            lambda clave=clave: lanzar_mision(astar, HEURISTICAS_DISPONIBLES[clave], inicio, base),
        ))

    for nombre, clave in heuristicas:
        pruebas.append((
            "Greedy",
            nombre,
            lambda clave=clave: lanzar_mision(greedy, HEURISTICAS_DISPONIBLES[clave], inicio, base),
        ))

    pruebas.append((
        "Dijkstra",
        "Nula",
        lambda: lanzar_mision(dijkstra, HEURISTICAS_DISPONIBLES["nula"], inicio, base),
    ))

    resultados = []
    for nombre_algoritmo, nombre_heuristica, funcion in pruebas:
        resultado = medir(nombre_algoritmo, nombre_heuristica, funcion, coste_optimo)
        resultados.append(resultado)

    print("Objetivos comparados:", len(objetivos))
    print(
        "Criterio de comparación: la última columna muestra cuántos pasos "
        "se desvía cada resultado respecto a A* + Manhattan en la misión completa."
    )
    imprimir_tabla(resultados)

    ruta_csv = os.path.join(os.path.dirname(__file__), "resultados_experimentos.csv")
    exportar_csv(resultados, ruta_csv)
    print(f"\nCSV guardado en: {ruta_csv}")
