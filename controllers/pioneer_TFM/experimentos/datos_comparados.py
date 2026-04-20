import csv
import os
import sys
import time

# Permite ejecutar este script directamente (`python experimentos/datos_comparados.py`)
# añadiendo la raíz del controlador al sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planificacion.algoritmos import astar, dijkstra, greedy, ordenar_objetivos
from configuracion.config import BATERIA_MAX, CELDA_INICIO, CELDAS_OBJETIVO
from planificacion.heuristicas import HEURISTICAS_DISPONIBLES, h_manhattan


def construir_mision(origen, objetivos, base, bateria):
    objetivos_ordenados = ordenar_objetivos(origen, objetivos)
    objetivos_validos = []
    coste_estimado = 0
    pos = origen

    for obj in objetivos_ordenados:
        coste_hasta_obj = h_manhattan(pos, obj)
        coste_vuelta_base = h_manhattan(obj, base)

        if coste_estimado + coste_hasta_obj + coste_vuelta_base > bateria:
            break

        objetivos_validos.append(obj)
        coste_estimado += coste_hasta_obj
        pos = obj

    return objetivos_validos


def ejecutar_mision(funcion_tramo, heuristica, origen, objetivos, base):
    ruta_total = []
    nodos_totales = 0
    pos = origen

    for destino in [*objetivos, base]:
        camino, nodos = funcion_tramo(pos, destino, heuristica)
        nodos_totales += nodos

        if not camino:
            return [], nodos_totales

        if ruta_total:
            ruta_total.extend(camino[1:])
        else:
            ruta_total.extend(camino)

        pos = destino

    return ruta_total, nodos_totales


def medir(nombre_algoritmo, nombre_heuristica, funcion, coste_optimo_referencia):
    t0 = time.perf_counter()
    camino, nodos = funcion()
    t1 = time.perf_counter()

    longitud = len(camino)
    coste = max(0, longitud - 1)
    tiempo = t1 - t0
    eficiencia = (longitud / nodos * 100.0) if nodos else 0.0
    expansion = (nodos / longitud) if longitud else 0.0
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
        "ruta": longitud,
        "coste": coste,
        "nodos": nodos,
        "tiempo": tiempo,
        "eficiencia": eficiencia,
        "expansion": expansion,
        "comparacion_referencia": comparacion_referencia,
    }


def imprimir_tabla(resultados):
    columnas = [
        ("Algoritmo", "algoritmo"),
        ("Heurística", "heuristica"),
        ("Longitud ruta (celdas)", "ruta"),
        ("Coste total (pasos)", "coste"),
        ("Nodos expandidos", "nodos"),
        ("Tiempo ejecución (s)", "tiempo"),
        ("Eficiencia camino/nodos (%)", "eficiencia"),
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
        ("longitud_ruta_celdas", "ruta"),
        ("coste_total_pasos", "coste"),
        ("nodos_expandidos", "nodos"),
        ("tiempo_ejecucion_s", "tiempo"),
        ("eficiencia_camino_sobre_nodos_pct", "eficiencia"),
        ("factor_expansion_nodos_por_celda", "expansion"),
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


if __name__ == "__main__":
    inicio = CELDA_INICIO
    base = CELDA_INICIO
    objetivos = construir_mision(inicio, CELDAS_OBJETIVO, base, BATERIA_MAX)

    ruta_optima, _ = ejecutar_mision(
        astar,
        HEURISTICAS_DISPONIBLES["manhattan"],
        inicio,
        objetivos,
        base,
    )
    coste_optimo = max(0, len(ruta_optima) - 1)

    heuristicas = [
        ("Nula", "nula"),
        ("Manhattan", "manhattan"),
        ("Euclidiana", "euclidiana"),
    ]

    pruebas = [
        (
            "A*",
            nombre,
            lambda clave=clave: ejecutar_mision(
                astar, HEURISTICAS_DISPONIBLES[clave], inicio, objetivos, base
            ),
        )
        for nombre, clave in heuristicas
    ]

    pruebas += [
        (
            "Greedy",
            nombre,
            lambda clave=clave: ejecutar_mision(
                greedy, HEURISTICAS_DISPONIBLES[clave], inicio, objetivos, base
            ),
        )
        for nombre, clave in heuristicas
    ]

    pruebas.append(
        (
            "Dijkstra",
            "Nula",
            lambda clave="nula": ejecutar_mision(
                lambda origen, destino, heuristica: dijkstra(origen, destino),
                HEURISTICAS_DISPONIBLES[clave],
                inicio,
                objetivos,
                base,
            ),
        )
    )

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