# TFM - Navegacion Autonoma con Pioneer 3-AT en Webots

Simulacion de un `Pioneer 3-AT` con planificacion sobre rejilla 48×48, mision multiobjetivo con bateria y comparativa de algoritmos.

## Objetivo

Partiendo de `worlds/pioneer3at.wbt`, el sistema discretiza el mapa, planifica ida a objetivos y vuelta a base respetando bateria, y ejecuta la ruta en Webots.

## Funcionalidades

- Algoritmos: `Dijkstra`, `Greedy`, `A*`, `A*` ponderado y `ARA*` (modos `offline` y `anytime_simple`).
- Heuristicas: `cero`, `manhattan`, `euclidiana`, `octil`, `agresiva`.
- Menu interactivo por teclado al arrancar (algoritmo, heuristica, modo ARA*).
- Carga automatica del `.wbt` → `generated_map.json` → `GRID` al importar `config.py`.
- Zonas de coste, suelo cambiante opcional y display de bateria en simulacion.

## Estructura

```text
pioneer_TFM/
├── worlds/pioneer3at.wbt
└── controllers/pioneer_TFM/
    ├── pioneer_TFM.py          # controlador Webots
    ├── planificacion/          # algoritmos, ARA*, costes, mision, grid
    ├── simulacion/             # robot_io, seguimiento, menu
    ├── configuracion/          # config.py, experimento.json, generated_map.json
    ├── herramientas/           # extract_wbt_to_json.py, MAPAS/ (PNG offline)
    └── experimentos/           # datos_comparados.py, resultados CSV
```

## Requisitos

- Webots R2025a
- Python 3 (controlador Webots)
- `matplotlib` y `numpy` solo para scripts offline (`pip install -r requirements.txt`)

## Ejecucion

1. Abre `worlds/pioneer3at.wbt` en Webots.
2. Controlador del robot: `pioneer_TFM`.
3. Inicia la simulacion y elige opciones en la consola con las teclas numericas.

Al arrancar, el mapa se regenera solo desde el `.wbt`. Si editas el mundo, basta con relanzar la simulacion.

## Configuracion

Parametros en `configuracion/config.py` y `configuracion/experimento.json`:

- `ALGORITMO`, `HEURISTICA`, `MODO_ARA` (sobreescritos por el menu)
- `BATERIA_MAX`, costes de zona, epsilons ARA*, `SUELO_CAMBIANTE`
- Objetivos e inicio: desde `generated_map.json` (generado del `.wbt`)

## Scripts offline

```bash
python3 controllers/pioneer_TFM/experimentos/datos_comparados.py   # comparativa → CSV
python3 controllers/pioneer_TFM/herramientas/MAPAS/mundo_a_grid.py # mapas PNG
python3 controllers/pioneer_TFM/herramientas/metricas.py           # benchmark rapido
```

## Notas

- El archivo `pioneer_TFM.py` debe coincidir en nombre con su carpeta (convencion Webots).
