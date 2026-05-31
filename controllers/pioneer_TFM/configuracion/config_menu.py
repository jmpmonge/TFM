# config_menu.py
import json
import os
from pathlib import Path

_ARCHIVO_EXPERIMENTO = Path(__file__).parent / "experimento.json"


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


def _posicion_transitable(config, x, y):
    fila, col = config.mundo_a_rejilla(x, y)
    return config.GRID[fila][col] != 1


def pedir_configuracion(config_mod=None):
    """
    Pregunta los valores principales del experimento.
    Devuelve un diccionario con los valores elegidos.
    """
    if config_mod is None:
        from configuracion import config as config_mod

    inicio_def = config_mod.INICIO_MUNDO
    objetivo_def = config_mod.OBJETIVOS_MUNDO[0]

    limpiar_terminal()
    imprimir_encabezado()

    valores = {}

    # 1. Costes de zonas
    valores["COSTE_ZONA_1"] = pedir_decimal("COSTE_ZONA_1 / zona azul", config_mod.COSTE_ZONA_1)
    valores["COSTE_ZONA_2"] = pedir_decimal("COSTE_ZONA_2 / zona verde", config_mod.COSTE_ZONA_2)
    valores["COSTE_ZONA_3"] = pedir_decimal("COSTE_ZONA_3 / zona amarilla", config_mod.COSTE_ZONA_3)

    # 2. Parámetros ARA*
    valores["PASOS_POR_FASE_ARA"] = pedir_entero("PASOS_POR_FASE_ARA", config_mod.PASOS_POR_FASE_ARA)

    # 3. A* ponderado
    valores["PESO_ASTAR_PONDERADO"] = pedir_decimal(
        "PESO_ASTAR_PONDERADO", config_mod.PESO_ASTAR_PONDERADO
    )

    # 4. Epsilon ARA*
    valores["EPSILON_INICIAL_ARA"] = pedir_decimal(
        "EPSILON_INICIAL_ARA", config_mod.EPSILON_INICIAL_ARA
    )
    valores["EPSILON_FINAL_ARA"] = pedir_decimal(
        "EPSILON_FINAL_ARA", config_mod.EPSILON_FINAL_ARA
    )
    valores["EPSILON_PASO_ARA"] = pedir_decimal(
        "EPSILON_PASO_ARA", config_mod.EPSILON_PASO_ARA
    )

    # 5. Batería
    valores["BATERIA_MAX"] = pedir_entero("BATERIA_MAX", config_mod.BATERIA_MAX)

    # 6. Inicio
    inicio_x = pedir_decimal("INICIO_MUNDO_X", inicio_def[0])
    inicio_y = pedir_decimal("INICIO_MUNDO_Y", inicio_def[1])
    valores["INICIO_MUNDO_POR_DEFECTO"] = (inicio_x, inicio_y)

    # 7. Objetivo
    objetivo_x = pedir_decimal("OBJETIVO_MUNDO_X", objetivo_def[0])
    objetivo_y = pedir_decimal("OBJETIVO_MUNDO_Y", objetivo_def[1])
    valores["OBJETIVOS_MUNDO_POR_DEFECTO"] = [(objetivo_x, objetivo_y)]

    entrada_suelo = input("¿Suelo cambiante? S/N [N]: ").strip().lower()
    valores["SUELO_CAMBIANTE"] = entrada_suelo == "s"

    return valores


def guardar_en_archivo(valores):
    """Guarda la configuración en experimento.json para que Webots la cargue."""
    datos = dict(valores)
    datos["INICIO_MUNDO_POR_DEFECTO"] = list(datos["INICIO_MUNDO_POR_DEFECTO"])
    datos["OBJETIVOS_MUNDO_POR_DEFECTO"] = [
        list(p) for p in datos["OBJETIVOS_MUNDO_POR_DEFECTO"]
    ]
    with open(_ARCHIVO_EXPERIMENTO, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2)
    print(f"Configuración guardada en {_ARCHIVO_EXPERIMENTO}")


def cargar_desde_archivo(config):
    """Carga experimento.json en config (sin input). Devuelve True si existía."""
    if not _ARCHIVO_EXPERIMENTO.is_file():
        return False

    with open(_ARCHIVO_EXPERIMENTO, encoding="utf-8") as f:
        valores = json.load(f)

    valores["INICIO_MUNDO_POR_DEFECTO"] = tuple(valores["INICIO_MUNDO_POR_DEFECTO"])
    valores["OBJETIVOS_MUNDO_POR_DEFECTO"] = [
        tuple(p) for p in valores["OBJETIVOS_MUNDO_POR_DEFECTO"]
    ]
    aplicar_a_config(config, valores)
    print(f"Configuración cargada desde {_ARCHIVO_EXPERIMENTO}")
    return True


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
    config.SUELO_CAMBIANTE = valores["SUELO_CAMBIANTE"]

    # Inicio y objetivo (solo si la celda es transitable; si no, se mantiene el .wbt)
    config.INICIO_MUNDO_POR_DEFECTO = valores["INICIO_MUNDO_POR_DEFECTO"]
    config.OBJETIVOS_MUNDO_POR_DEFECTO = valores["OBJETIVOS_MUNDO_POR_DEFECTO"]

    inicio = valores["INICIO_MUNDO_POR_DEFECTO"]
    if _posicion_transitable(config, inicio[0], inicio[1]):
        config.INICIO_MUNDO = inicio
    else:
        print(
            f"Aviso: inicio {inicio} no es transitable; "
            f"se mantiene {config.INICIO_MUNDO}"
        )

    objetivos_ok = []
    for ox, oy in valores["OBJETIVOS_MUNDO_POR_DEFECTO"]:
        if _posicion_transitable(config, ox, oy):
            objetivos_ok.append((ox, oy))
        else:
            print(
                f"Aviso: objetivo ({ox}, {oy}) no es transitable; "
                f"se mantiene {config.OBJETIVOS_MUNDO}"
            )

    if objetivos_ok:
        config.OBJETIVOS_MUNDO = objetivos_ok
        config.OBJETIVO_MUNDO = config.OBJETIVOS_MUNDO[0]

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
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from configuracion import config

    valores = pedir_configuracion(config)
    guardar_en_archivo(valores)
    aplicar_a_config(config, valores)

    print("\nCONFIGURACIÓN ELEGIDA:")
    for nombre, valor in valores.items():
        print(nombre, "=", valor)