import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle
import numpy as np

from configuracion.config import (
    CELDA_INICIO,
    CELDAS_OBJETIVO,
    CELDAS_POR_ZONA,
    COLUMNAS_MAPA,
    FILAS_MAPA,
    GRID,
    ZONAS_COSTE,
    _GRID_BASE,
)


# --- COLORES BÁSICOS ---

COLOR_LIBRE = (1.0, 1.0, 1.0)
COLOR_SEGURIDAD = (0.82, 0.82, 0.82)
COLOR_MURO = (0.15, 0.15, 0.15)

COLOR_IDA = "green"
COLOR_VUELTA = "royalblue"
COLOR_LINEA_LIMITE = "red"
COLOR_RUTA_INICIAL = "0.55"
COLOR_RUTA_CAMBIADA = "darkorange"

TAM_IDA = 3
TAM_VUELTA = 7
BORDE_VUELTA = 1.5

COLORES_ZONA = {
    "COST_ZONE_1": (0.12, 0.45, 0.95),  # azul
    "COST_ZONE_2": (0.18, 0.72, 0.28),  # verde
    "COST_ZONE_3": (0.95, 0.55, 0.12),  # amarillo
}


# --- 1. REJILLA ---

def dibujar_rejilla(ax):
    ax.set_xticks(np.arange(-0.5, COLUMNAS_MAPA, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, FILAS_MAPA, 1), minor=True)
    ax.grid(which="minor", color="lightgray", linestyle="-", linewidth=0.25)
    ax.tick_params(
        which="both",
        bottom=False,
        left=False,
        labelbottom=False,
        labelleft=False,
    )


# --- 2. MUROS FÍSICOS ---

def dibujar_muros(ax):
    base = np.array(_GRID_BASE, dtype=bool)

    for fila in range(FILAS_MAPA):
        for col in range(COLUMNAS_MAPA):
            if base[fila][col]:
                ax.add_patch(
                    Rectangle(
                        (col - 0.5, fila - 0.5),
                        1,
                        1,
                        facecolor=COLOR_MURO,
                        edgecolor=COLOR_MURO,
                        linewidth=0,
                        zorder=1,
                    )
                )


# --- 3. ZONA DE SEGURIDAD ---

def dibujar_zona_seguridad(ax):
    base = np.array(_GRID_BASE, dtype=bool)

    for fila in range(FILAS_MAPA):
        for col in range(COLUMNAS_MAPA):
            if GRID[fila][col] == 1 and not base[fila][col]:
                ax.add_patch(
                    Rectangle(
                        (col - 0.5, fila - 0.5),
                        1,
                        1,
                        facecolor=COLOR_SEGURIDAD,
                        edgecolor=COLOR_SEGURIDAD,
                        linewidth=0,
                        zorder=1,
                    )
                )


# --- 4. ZONAS DE COSTE ---

def dibujar_zonas_coste(ax):
    for nombre, celdas in CELDAS_POR_ZONA.items():
        color = COLORES_ZONA.get(nombre, (0.12, 0.45, 0.95))

        for fila, col in celdas:
            ax.add_patch(
                    Rectangle(
                        (col - 0.5, fila - 0.5),
                        1,
                        1,
                        facecolor=color,
                        edgecolor=color,
                        alpha=0.65,
                        linewidth=0.5,
                        zorder=2,
                    )
                )


# --- 5. LÍNEA ROJA DEL LÍMITE ---

def _celda_libre(fila, col):
    if fila < 0 or fila >= FILAS_MAPA or col < 0 or col >= COLUMNAS_MAPA:
        return True
    from configuracion import config
    return not config.celda_bloqueada(fila, col)


def dibujar_linea_limite(ax):
    segmentos = []

    for fila in range(FILAS_MAPA):
        for col in range(COLUMNAS_MAPA):
            if _celda_libre(fila, col):
                continue

            x0 = col - 0.5
            x1 = col + 0.5
            y0 = fila - 0.5
            y1 = fila + 0.5

            if _celda_libre(fila - 1, col):
                segmentos.append([(x0, y0), (x1, y0)])
            if _celda_libre(fila + 1, col):
                segmentos.append([(x0, y1), (x1, y1)])
            if _celda_libre(fila, col - 1):
                segmentos.append([(x0, y0), (x0, y1)])
            if _celda_libre(fila, col + 1):
                segmentos.append([(x1, y0), (x1, y1)])

    if segmentos:
        ax.add_collection(
            LineCollection(
                segmentos,
                colors=COLOR_LINEA_LIMITE,
                linewidths=1.2,
                linestyles="--",
                zorder=5,
            )
        )


# --- 6. SALIDA Y OBJETIVOS ---

def dibujar_start_goal(ax):
    ax.text(
        CELDA_INICIO[1],
        CELDA_INICIO[0],
        "S",
        ha="center",
        va="center",
        color="green",
        fontsize=12,
        fontweight="bold",
        zorder=20,
    )

    for i, (fila, col) in enumerate(CELDAS_OBJETIVO, start=1):
        ax.text(
            col,
            fila,
            f"G{i}",
            ha="center",
            va="center",
            color="red",
            fontsize=7,
            fontweight="bold",
            zorder=20,
        )


# --- 7. CAMINO IDA / VUELTA ---

def _misma_ruta_ida_vuelta(ruta_ida, ruta_vuelta):
    if not ruta_ida or not ruta_vuelta:
        return False
    return list(ruta_ida) == list(reversed(ruta_vuelta))


def _dibujar_puntos(ax, ruta, color, tam, hueco=False):
    puntos_omitidos = {CELDA_INICIO, *CELDAS_OBJETIVO}

    for fila, col in ruta:
        if (fila, col) in puntos_omitidos:
            continue

        ax.plot(
            col,
            fila,
            marker="o",
            markersize=tam,
            markerfacecolor="none" if hueco else color,
            markeredgecolor=color,
            markeredgewidth=BORDE_VUELTA if hueco else 0.8,
            linestyle="None",
            zorder=10,
        )


def dibujar_camino_anytime(ax, informe):
    historial = informe.get("historial", [])
    if not historial:
        return False

    inicial = list(historial[0]["ruta_calculada"])
    _dibujar_puntos(ax, inicial, COLOR_RUTA_INICIAL, TAM_IDA, hueco=False)

    anterior = inicial
    for entry in historial[1:]:
        if entry.get("accion") != "ruta actualizada":
            continue
        nueva = list(entry["ruta_calculada"])
        if nueva != anterior:
            _dibujar_puntos(ax, nueva, COLOR_RUTA_CAMBIADA, TAM_IDA, hueco=False)
        anterior = nueva

    final = list(informe.get("ruta_final", historial[-1]["ruta_calculada"]))
    _dibujar_puntos(ax, final, COLOR_IDA, TAM_IDA, hueco=False)
    return True


def dibujar_camino(ax, ruta_ida, ruta_vuelta, dibujar_ida=True, dibujar_vuelta=True, informe_anytime=None):
    if informe_anytime and dibujar_ida and not dibujar_vuelta:
        if dibujar_camino_anytime(ax, informe_anytime):
            return

    if dibujar_ida and dibujar_vuelta:
        misma = _misma_ruta_ida_vuelta(ruta_ida, ruta_vuelta)
        if misma:
            _dibujar_puntos(ax, ruta_ida, COLOR_IDA, TAM_IDA, hueco=False)
            return
        _dibujar_puntos(ax, ruta_vuelta, COLOR_VUELTA, TAM_VUELTA, hueco=True)
        _dibujar_puntos(ax, ruta_ida, COLOR_IDA, TAM_IDA, hueco=False)
    elif dibujar_ida:
        _dibujar_puntos(ax, ruta_ida, COLOR_IDA, TAM_IDA, hueco=False)
    elif dibujar_vuelta:
        _dibujar_puntos(ax, ruta_vuelta, COLOR_VUELTA, TAM_VUELTA, hueco=True)


# --- 8. GUARDAR MAPA ---

def guardar_mapa(
    ruta_ida,
    ruta_vuelta,
    nombre_archivo,
    titulo="Ruta ida y vuelta",
    coste_g=0.0,
    nodos=0,
    len_camino=0,
    dibujar_ida=True,
    dibujar_vuelta=True,
    informe_anytime=None,
):
    from panel_simple import alinear_panel_con_mapa, dibujar_panel

    fig, (ax, ax_panel) = plt.subplots(
        1,
        2,
        figsize=(13, 10),
        gridspec_kw={"width_ratios": [3, 1.55]},
    )

    ax.set_xlim(-0.5, COLUMNAS_MAPA - 0.5)
    ax.set_ylim(-0.5, FILAS_MAPA - 0.5)
    ax.set_aspect("equal")

    ax.set_facecolor(COLOR_LIBRE)

    dibujar_muros(ax)
    dibujar_zona_seguridad(ax)
    dibujar_zonas_coste(ax)
    dibujar_linea_limite(ax)
    dibujar_rejilla(ax)
    dibujar_start_goal(ax)
    dibujar_camino(ax, ruta_ida, ruta_vuelta, dibujar_ida, dibujar_vuelta, informe_anytime)

    plt.tight_layout()
    alinear_panel_con_mapa(ax, ax_panel, fig)

    dibujar_panel(
        ax_panel, titulo, len_camino, coste_g, nodos, dibujar_ida, dibujar_vuelta, informe_anytime,
    )

    plt.savefig(nombre_archivo, dpi=150, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)

    print(f"Mapa guardado en {nombre_archivo}")
