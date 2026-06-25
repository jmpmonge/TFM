# TFM - Navegacion Autonoma con Pioneer 3-AT en Webots

Simulacion de un `Pioneer 3-AT` con planificacion sobre rejilla 48×48, mision multiobjetivo con bateria y comparativa de algoritmos.

## Objetivo

Partiendo de `worlds/pioneer3at.wbt`, el sistema discretiza el mapa, planifica ida a objetivos y vuelta a base respetando bateria, y ejecuta la ruta en Webots.

## Funcionalidades

- Algoritmos en el menu Webots: `Dijkstra`, `Greedy`, `A*` y `ARA*` (modos `offline` y `anytime_simple`).
- Heuristicas: `nula` (solo Dijkstra), `manhattan`, `euclidiana`, `octil`.
- Menu interactivo por teclado al arrancar (algoritmo, heuristica, modo ARA*).
- Carga automatica del `.wbt` → `generated_map.json` → `GRID` al importar `config.py`.
- Zonas de coste, suelo cambiante opcional y display de bateria en simulacion.
- A* ponderado (`astar_ponderado`) usado internamente por ARA*; no aparece como opcion separada en el menu.

## Estructura

```text
pioneer_TFM/
├── worlds/pioneer3at.wbt
├── requirements.txt
└── controllers/pioneer_TFM/
    ├── pioneer_TFM.py          # controlador Webots
    ├── planificacion/          # algoritmos, ARA*, costes, mision, grid
    ├── simulacion/             # robot_io, seguimiento, menu
    ├── configuracion/          # config.py, experimento.json, generated_map.json
    ├── herramientas/           # extract_wbt_to_json.py, MAPAS/ (PNG offline)
    └── experimentos/           # datos_comparados.py, resultados_experimentos.csv
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

- `ALGORITMO`, `HEURISTICA`, `MODO_ARA` (sobreescritos por el menu en Webots)
- `BATERIA_MAX`, costes de zona (1 / 10 / 20), epsilons ARA* (5→1), `SUELO_CAMBIANTE`
- Inicio y objetivos en mundo: desde `generated_map.json` (generado del `.wbt`); `experimento.json` actua como respaldo

## Scripts offline

### Comparativa reproducible (tabla del TFM)

```bash
python3 controllers/pioneer_TFM/experimentos/datos_comparados.py
```

Genera `experimentos/resultados_experimentos.csv` con dos grupos aislados:

- **estatico:** un trayecto inicio→objetivo, suelo fijo (`SUELO_CAMBIANTE=False`). Incluye Dijkstra, A*, Greedy.
- **ara:** ARA* con suelo cambiante; el entorno se restaura antes de cada heuristica.

Columnas principales: `grupo_experimento`, `algoritmo`, `heuristica`, `coste_ponderado`, `movimientos`, `celdas`, `nodos_expandidos`, costes de zona inicial/final.

El script verifica automaticamente que Dijkstra y A* nula coinciden, que todos los A* estaticos tienen el mismo coste optimo, y que el orden de ejecucion no altera los resultados.

### Mapas PNG (mision completa Webots)

```bash
python3 controllers/pioneer_TFM/herramientas/MAPAS/mundo_a_grid.py
```

Genera `map_ida.png`, `map_vuelta.png` y `map_ida_vuelta.png` a partir de una **mision completa** (ida + vuelta) con los defaults de `config.py`. Estas figuras no usan la misma metodologia que el CSV estatico; citarlas en la memoria como visualizacion de mision, no como tabla comparativa.

### Benchmark rapido (solo desarrollo)

```bash
python3 controllers/pioneer_TFM/herramientas/metricas.py
```

Script auxiliar sin restauracion completa del entorno entre pruebas. No usar sus metricas como resultados finales del TFM; preferir `datos_comparados.py`.

## Notas

- El archivo `pioneer_TFM.py` debe coincidir en nombre con su carpeta (convencion Webots).
- Ejecucion local con Webots y Python; no se requiere Docker ni Webots Cloud.
