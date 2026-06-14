# leyenda y datos del mapa (solo texto)

from configuracion import config
from configuracion.config import (
    ALGORITMO,
    CELDAS_OBJETIVO,
    COLUMNAS_MAPA,
    FILAS_MAPA,
    HEURISTICA,
    MODO_ARA,
    PASOS_POR_FASE_ARA,
)


def alinear_panel_con_mapa(ax_mapa, ax_panel, fig):
    fig.canvas.draw()
    pos_mapa = ax_mapa.get_position()
    pos_panel = ax_panel.get_position()
    ax_panel.set_position([pos_panel.x0, pos_mapa.y0, pos_panel.width, pos_mapa.height])


_ANCHO_ETIQUETA = 22
_PASO_LINEA = 0.026
_FUENTE_TAM = 7.5


def _linea(etiqueta, valor=None):
    if valor is None:
        return f"  {etiqueta}"
    return f"  {etiqueta:<{_ANCHO_ETIQUETA}}= {valor}"


def _escribir_linea(ax, y, texto):
    ax.text(
        0.02,
        y,
        texto,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=_FUENTE_TAM,
        family="monospace",
        clip_on=True,
    )
    return y - _PASO_LINEA


def dibujar_panel(ax, titulo, len_camino, coste_g, nodos, dibujar_ida=True, dibujar_vuelta=True, informe_anytime=None):
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    y = 1.0

    y = _escribir_linea(ax, y, "LEYENDA")
    y = _escribir_linea(ax, y, _linea("muro físico", "gris oscuro"))
    y = _escribir_linea(ax, y, _linea("margen seguridad", "gris claro"))
    y = _escribir_linea(ax, y, _linea("límite", "linea roja"))
    y = _escribir_linea(ax, y, _linea("zona azul", "coste 1"))
    y = _escribir_linea(ax, y, _linea("zona verde", "coste 2"))
    y = _escribir_linea(ax, y, _linea("zona amarilla", "coste 3"))

    if informe_anytime and dibujar_ida and not dibujar_vuelta:
        y = _escribir_linea(ax, y, _linea("punto gris", "ruta inicial"))
        y = _escribir_linea(ax, y, _linea("punto naranja", "ruta recalculada"))
        y = _escribir_linea(ax, y, _linea("punto verde", "ruta final"))
    else:
        if dibujar_ida:
            y = _escribir_linea(ax, y, _linea("punto verde", "ida"))
        if dibujar_vuelta:
            y = _escribir_linea(ax, y, _linea("círculo azul", "vuelta"))

    y = _escribir_linea(ax, y, _linea("S", "inicio"))
    y = _escribir_linea(ax, y, _linea("G1, G2...", "objetivos"))

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
    y = _escribir_linea(ax, y, _linea("tramo", titulo))
    y = _escribir_linea(ax, y, _linea("mapa", f"{FILAS_MAPA} x {COLUMNAS_MAPA}"))
    y = _escribir_linea(ax, y, _linea("algoritmo", algoritmo))
    y = _escribir_linea(
        ax,
        y,
        _linea(
            "costes zona",
            f"{config.COSTE_ZONA_1:g} / {config.COSTE_ZONA_2:g} / {config.COSTE_ZONA_3:g}",
        ),
    )
    y = _escribir_linea(ax, y, _linea("ponderacion dinámica", "x30 / /5 / x1"))
    y = _escribir_linea(ax, y, _linea("dinámico", str(config.SUELO_CAMBIANTE).lower()))
    y = _escribir_linea(ax, y, _linea("tiempo cambio din.", f"{PASOS_POR_FASE_ARA} pasos"))
    y = _escribir_linea(ax, y, _linea("longitud", f"{len_camino} celdas"))
    y = _escribir_linea(ax, y, _linea("coste g", f"{coste_g:.1f}"))
    y = _escribir_linea(ax, y, _linea("nodos", nodos))
    _escribir_linea(ax, y, _linea("objetivos", len(CELDAS_OBJETIVO)))
