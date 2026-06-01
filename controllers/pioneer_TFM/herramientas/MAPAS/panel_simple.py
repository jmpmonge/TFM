# leyenda y datos del mapa (solo texto)

from configuracion import config
from configuracion.config import (
    ALGORITMO,
    CELDAS_OBJETIVO,
    COLUMNAS_MAPA,
    FILAS_MAPA,
    HEURISTICA,
    MODO_ARA,
)


def alinear_panel_con_mapa(ax_mapa, ax_panel, fig):
    fig.canvas.draw()
    pos_mapa = ax_mapa.get_position()
    pos_panel = ax_panel.get_position()
    ax_panel.set_position([pos_panel.x0, pos_mapa.y0, pos_panel.width, pos_mapa.height])


def _escribir_linea(ax, y, texto):
    ax.text(
        0.0,
        y,
        texto,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=9,
        family="monospace",
    )
    return y - 0.028


def dibujar_panel(ax, titulo, len_camino, coste_g, nodos, dibujar_ida=True, dibujar_vuelta=True, informe_anytime=None):
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    y = 1.0

    y = _escribir_linea(ax, y, "LEYENDA")
    y = _escribir_linea(ax, y, "  muro fisico      = gris oscuro")
    y = _escribir_linea(ax, y, "  margen seguridad = gris claro")
    y = _escribir_linea(ax, y, "  limite           = linea roja")
    y = _escribir_linea(ax, y, "  zona azul        = coste 1")
    y = _escribir_linea(ax, y, "  zona verde       = coste 2")
    y = _escribir_linea(ax, y, "  zona amarilla    = coste 3")

    if informe_anytime and dibujar_ida and not dibujar_vuelta:
        y = _escribir_linea(ax, y, "  circulo gris     = ruta inicial")
        y = _escribir_linea(ax, y, "  circulo naranja  = ruta recalculada")
        y = _escribir_linea(ax, y, "  punto verde      = ruta final")
    else:
        if dibujar_ida:
            y = _escribir_linea(ax, y, "  punto verde      = ida")
        if dibujar_vuelta:
            y = _escribir_linea(ax, y, "  circulo azul     = vuelta")

    y = _escribir_linea(ax, y, "  S                = inicio")
    y = _escribir_linea(ax, y, "  G1, G2...        = objetivos")

    if ALGORITMO == "dijkstra":
        algoritmo = "Dijkstra"
    elif ALGORITMO == "greedy":
        algoritmo = f"Greedy + {HEURISTICA}"
    elif ALGORITMO == "ara_star":
        modo = "anytime" if MODO_ARA == "anytime_simple" else "offline"
        algoritmo = f"ARA* ({modo}) + {HEURISTICA}"
    else:
        algoritmo = f"{ALGORITMO} + {HEURISTICA}"

    y = _escribir_linea(ax, y, "")
    y = _escribir_linea(ax, y, "DATOS")
    y = _escribir_linea(ax, y, f"  tramo      = {titulo}")
    y = _escribir_linea(ax, y, f"  mapa       = {FILAS_MAPA} x {COLUMNAS_MAPA}")
    y = _escribir_linea(ax, y, f"  algoritmo  = {algoritmo}")
    y = _escribir_linea(
        ax,
        y,
        f"  costes zona= {config.COSTE_ZONA_1:g} / {config.COSTE_ZONA_2:g} / {config.COSTE_ZONA_3:g}",
    )
    y = _escribir_linea(ax, y, f"  longitud   = {len_camino} celdas")
    y = _escribir_linea(ax, y, f"  coste g    = {coste_g:.1f}")
    y = _escribir_linea(ax, y, f"  nodos      = {nodos}")
    _escribir_linea(ax, y, f"  objetivos  = {len(CELDAS_OBJETIVO)}")
