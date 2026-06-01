"""
Visualiza la rejilla GRID y la ruta planificada.

Genera en esta carpeta:
  - map_ida.png
  - map_vuelta.png
  - map_ida_vuelta.png

Uso:
    python3 controllers/pioneer_TFM/herramientas/MAPAS/mundo_a_grid.py
"""

import os
import sys

MPLCONFIGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mpl-cache")
os.makedirs(MPLCONFIGDIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", MPLCONFIGDIR)

import matplotlib
matplotlib.use("Agg")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from planificacion.ara import INFORME_ARA_MISION
from planificacion.costes import coste_camino
from planificacion.mision import planificar_mision
from configuracion import config
from configuracion import config_menu
from configuracion.config import ALGORITMO, BATERIA_MAX, CELDA_INICIO, CELDAS_OBJETIVO, MODO_ARA
from dibujo_mapa import guardar_mapa


def main():
    config_menu.cargar_desde_archivo(config)

    rutas, nodos = planificar_mision(
        CELDA_INICIO,
        CELDAS_OBJETIVO,
        CELDA_INICIO,
        BATERIA_MAX,
        devolver_nodos=True,
    )

    camino = []
    for i, ruta in enumerate(rutas):
        if not ruta:
            continue
        if i == 0:
            camino.extend(ruta)
        else:
            camino.extend(ruta[1:])

    ruta_ida = list(rutas[0]) if rutas else []
    ruta_vuelta = list(rutas[-1]) if len(rutas) > 1 else []

    coste_g = coste_camino(camino)
    carpeta = os.path.dirname(os.path.abspath(__file__))

    informe_anytime = None
    if ALGORITMO == "ara_star" and MODO_ARA == "anytime_simple":
        for informe in INFORME_ARA_MISION:
            if informe.get("modo") == "anytime_simple":
                informe_anytime = informe
                break

    mapas = [
        ("map_ida.png", True, False, "Ruta de ida"),
        ("map_vuelta.png", False, True, "Ruta de vuelta"),
        ("map_ida_vuelta.png", True, True, "Ruta ida y vuelta"),
    ]

    for archivo, dibujar_ida, dibujar_vuelta, titulo in mapas:
        guardar_mapa(
            ruta_ida,
            ruta_vuelta,
            os.path.join(carpeta, archivo),
            titulo,
            coste_g,
            nodos,
            len(camino),
            dibujar_ida,
            dibujar_vuelta,
            informe_anytime if dibujar_ida and not dibujar_vuelta else None,
        )

    print(
        f"Resumen | longitud={len(camino)} | coste_g={coste_g:.1f} | nodos={nodos}"
    )


if __name__ == "__main__":
    main()
