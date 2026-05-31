# config_menu.py
import os


def limpiar_terminal():
    """
    Limpia la terminal.
    Funciona en Mac/Linux y Windows.
    """
    os.system("cls" if os.name == "nt" else "clear")


def imprimir_encabezado():
    """
    Muestra el encabezado del menú de configuración.
    """
    print("=" * 60)
    print("CONFIGURACIÓN DEL EXPERIMENTO PIONEER TFM")
    print("=" * 60)
    print("Pulsa Intro para mantener el valor por defecto.")
    print("=" * 60)
    print()


def pedir_decimal(nombre, valor_por_defecto):
    """
    Pide un número decimal.
    Si el usuario pulsa Intro, deja el valor por defecto.
    """
    entrada = input(f"{nombre} [{valor_por_defecto}]: ")

    if entrada == "":
        return valor_por_defecto

    return float(entrada)


def pedir_entero(nombre, valor_por_defecto):
    """
    Pide un número entero.
    Si el usuario pulsa Intro, deja el valor por defecto.
    """
    entrada = input(f"{nombre} [{valor_por_defecto}]: ")

    if entrada == "":
        return valor_por_defecto

    return int(entrada)


def pedir_configuracion():
    """
    Pregunta los valores principales del experimento.
    Devuelve un diccionario con los valores elegidos.
    """

    limpiar_terminal()
    imprimir_encabezado()

    valores = {}

    # 1. Costes de zonas
    valores["COSTE_ZONA_1"] = pedir_decimal("COSTE_ZONA_1 / zona azul", 5)
    valores["COSTE_ZONA_2"] = pedir_decimal("COSTE_ZONA_2 / zona verde", 5)
    valores["COSTE_ZONA_3"] = pedir_decimal("COSTE_ZONA_3 / zona amarilla", 5)

    # 2. Parámetros ARA*
    valores["PASOS_POR_FASE_ARA"] = pedir_entero("PASOS_POR_FASE_ARA", 5)

    # 3. A* ponderado
    valores["PESO_ASTAR_PONDERADO"] = pedir_decimal("PESO_ASTAR_PONDERADO", 1.5)

    # 4. Epsilon ARA*
    valores["EPSILON_INICIAL_ARA"] = pedir_decimal("EPSILON_INICIAL_ARA", 5)
    valores["EPSILON_FINAL_ARA"] = pedir_decimal("EPSILON_FINAL_ARA", 1.0)
    valores["EPSILON_PASO_ARA"] = pedir_decimal("EPSILON_PASO_ARA", 1)

    # 5. Batería
    valores["BATERIA_MAX"] = pedir_entero("BATERIA_MAX", 800)

    # 6. Inicio
    inicio_x = pedir_decimal("INICIO_MUNDO_X", -4.25)
    inicio_y = pedir_decimal("INICIO_MUNDO_Y", 10.25)
    valores["INICIO_MUNDO_POR_DEFECTO"] = (inicio_x, inicio_y)

    # 7. Objetivo
    objetivo_x = pedir_decimal("OBJETIVO_MUNDO_X", -4.25)
    objetivo_y = pedir_decimal("OBJETIVO_MUNDO_Y", 7.25)
    valores["OBJETIVOS_MUNDO_POR_DEFECTO"] = [(objetivo_x, objetivo_y)]

    return valores


def aplicar_a_config(config, valores):
    """
    Mete los valores elegidos dentro de config.py.
    No modifica el archivo config.py en disco.
    Solo cambia los valores mientras el programa está abierto.
    """

    # Costes de zonas.
    # Usamos la función de config porque también actualiza el GRID.
    config.aplicar_costes_zonas(
        valores["COSTE_ZONA_1"],
        valores["COSTE_ZONA_2"],
        valores["COSTE_ZONA_3"],
    )

    # Parámetros simples
    config.PASOS_POR_FASE_ARA = valores["PASOS_POR_FASE_ARA"]
    config.PESO_ASTAR_PONDERADO = valores["PESO_ASTAR_PONDERADO"]

    config.EPSILON_INICIAL_ARA = valores["EPSILON_INICIAL_ARA"]
    config.EPSILON_FINAL_ARA = valores["EPSILON_FINAL_ARA"]
    config.EPSILON_PASO_ARA = valores["EPSILON_PASO_ARA"]

    config.BATERIA_MAX = valores["BATERIA_MAX"]

    # Inicio y objetivo
    config.INICIO_MUNDO_POR_DEFECTO = valores["INICIO_MUNDO_POR_DEFECTO"]
    config.OBJETIVOS_MUNDO_POR_DEFECTO = valores["OBJETIVOS_MUNDO_POR_DEFECTO"]

    config.INICIO_MUNDO = config.INICIO_MUNDO_POR_DEFECTO
    config.OBJETIVOS_MUNDO = config.OBJETIVOS_MUNDO_POR_DEFECTO
    config.OBJETIVO_MUNDO = config.OBJETIVOS_MUNDO[0]

    # Recalcular celdas de inicio y objetivo
    config.CELDA_INICIO = config.mundo_a_rejilla(
        config.INICIO_MUNDO[0],
        config.INICIO_MUNDO[1],
    )

    config.CELDA_OBJETIVO = config.mundo_a_rejilla(
        config.OBJETIVO_MUNDO[0],
        config.OBJETIVO_MUNDO[1],
    )

    config.CELDAS_OBJETIVO = [
        config.mundo_a_rejilla(x, y)
        for x, y in config.OBJETIVOS_MUNDO
    ]


if __name__ == "__main__":
    # Esto solo sirve para probar el archivo con Play.
    valores = pedir_configuracion()

    print("\nCONFIGURACIÓN ELEGIDA:")
    for nombre, valor in valores.items():
        print(nombre, "=", valor)