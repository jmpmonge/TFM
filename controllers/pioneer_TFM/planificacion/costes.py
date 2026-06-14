import math

from configuracion import config


def coste_base_celda(celda):
    """Coste base del terreno: libre (0) → 1; zona de coste → valor del GRID (puede ser 1)."""
    if celda in config.CELDAS_COSTE:
        return float(config.GRID[celda[0]][celda[1]])
    valor = config.GRID[celda[0]][celda[1]]
    return 1.0 if valor == 0 else float(valor)


def _es_paso_diagonal(actual, vecino):
    return abs(vecino[0] - actual[0]) == 1 and abs(vecino[1] - actual[1]) == 1


def _coste_paso(actual, vecino, aplicar_factor_diagonal):
    """Coste de un paso: base del terreno en vecino; opcionalmente × sqrt(2) si es diagonal."""
    base = coste_base_celda(vecino)
    if aplicar_factor_diagonal and _es_paso_diagonal(actual, vecino):
        return base * math.sqrt(2)
    return base


def _sumar_coste_camino(camino, funcion_coste):
    """Suma el coste de cada tramo consecutivo del camino."""
    total = 0.0
    for i in range(1, len(camino)):
        total += funcion_coste(camino[i - 1], camino[i])
    return total


def coste_movimiento(actual, vecino):
    """
    Coste g(n) de entrar en la celda vecino según GRID y tipo de paso:
    - ortogonal: coste base de la celda
    - diagonal: coste base × sqrt(2)
    """
    return _coste_paso(actual, vecino, True)


def coste_camino(camino):
    """Suma g(n) a lo largo de una secuencia de celdas consecutivas."""
    if len(camino) <= 1:
        return 0
    return _sumar_coste_camino(camino, coste_movimiento)


def coste_bateria_movimiento(actual, vecino):
    """
    Consumo energético al pasar de actual a vecino.
    Usa el mismo coste base del terreno; el factor diagonal depende de config.
    """
    return _coste_paso(actual, vecino, config.USAR_FACTOR_DIAGONAL_BATERIA)


def coste_bateria_camino(camino):
    """Batería consumida recorriendo un camino de celdas consecutivas."""
    if len(camino) <= 1:
        return 0.0
    return _sumar_coste_camino(camino, coste_bateria_movimiento)


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
