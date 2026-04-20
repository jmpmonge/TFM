# TFM - Navegacion Autonoma con Pioneer 3-AT en Webots

Proyecto de simulacion en `Webots` para un robot `Pioneer 3-AT` centrado en planificacion de rutas sobre rejilla, comparativa de algoritmos y ejecucion de misiones con multiples objetivos.

## Objetivo

El proyecto modela un entorno con obstaculos en `worlds/pioneer3at.wbt`, genera una representacion discreta del mapa y ejecuta una mision de navegacion que:

- parte de una salida fija,
- visita varios objetivos,
- tiene en cuenta una restriccion de bateria,
- y sigue la ruta calculada dentro de la simulacion.

## Funcionalidades principales

- Planificacion con `Dijkstra`, `A*` y `Greedy Best-First Search`.
- Heuristicas configurables: nula (equivale a Dijkstra), Manhattan y Euclidiana.
- Seleccion interactiva de algoritmo y heuristica por teclado al iniciar la simulacion.
- Extraccion automatica de obstaculos y objetivos desde el mundo Webots a `generated_map.json`.
- Mision multiobjetivo con vuelta a base y restriccion de bateria.
- Visualizacion simple del nivel de bateria durante la simulacion.
- Comparativa experimental de algoritmos y heuristicas con exportacion a CSV.

## Estructura del proyecto

```text
pioneer_TFM/
├── worlds/
│   └── pioneer3at.wbt
├── controllers/
│   └── pioneer_TFM/
│       ├── pioneer_TFM.py              # punto de entrada del controlador Webots
│       │
│       ├── planificacion/              # logica algoritmica
│       │   ├── algoritmos.py           # dijkstra, astar, greedy, planificar_mision
│       │   ├── heuristicas.py          # h_nula, h_manhattan, h_euclidiana
│       │   └── mapa.py                 # grid, celda_a_mundo, es_libre
│       │
│       ├── simulacion/                 # interaccion con Webots
│       │   ├── robot_io.py             # supervisor, ruedas, display, pose real
│       │   ├── seguimiento.py          # control de velocidades sobre la ruta
│       │   └── menu_heuristica.py      # menu interactivo por teclado
│       │
│       ├── configuracion/              # parametros y datos del mundo
│       │   ├── config.py
│       │   └── generated_map.json
│       │
│       ├── experimentos/               # comparativas offline
│       │   ├── datos_comparados.py
│       │   └── resultados_experimentos.csv
│       │
│       └── herramientas/               # scripts auxiliares
│           ├── extract_wbt_to_json.py  # .wbt -> generated_map.json
│           ├── dump_map.py             # visualizacion del mapa con ruta
│           ├── dump_map_simple.py      # visualizacion sencilla de la rejilla
│           └── metricas.py             # benchmark rapido de algoritmos
└── README.md
```

## Requisitos

- `Webots R2025a`
- `Python 3`
- `matplotlib` y `numpy` (solo para los scripts de visualizacion en `herramientas/`)

## Ejecucion

1. Abre `worlds/pioneer3at.wbt` en Webots.
2. Comprueba que el controlador asociado al robot es `controllers/pioneer_TFM/pioneer_TFM.py`.
3. Ejecuta la simulacion.
4. En la consola de Webots, elige algoritmo y heuristica con las teclas numericas.

Si modificas el mundo (`.wbt`) y cambias obstaculos u objetivos, regenera el mapa con:

```bash
python3 controllers/pioneer_TFM/herramientas/extract_wbt_to_json.py
```

El JSON se escribe en `controllers/pioneer_TFM/configuracion/generated_map.json`.

## Configuracion

Los parametros principales se ajustan en `controllers/pioneer_TFM/configuracion/config.py`:

- `ALGORITMO`: variante de planificacion por defecto (`dijkstra`, `astar`, `greedy`). Se sobreescribe al elegir por teclado.
- `HEURISTICA`: heuristica por defecto (`nula`, `manhattan`, `euclidiana`). Se sobreescribe al elegir por teclado.
- `BATERIA_MAX`: presupuesto de bateria de la mision.
- `INICIO_MUNDO`: posicion inicial del robot.
- `CELL_SIZE`, `MARGEN_SEGURIDAD`: resolucion de la rejilla y margen para inflar obstaculos.

Los objetivos se cargan automaticamente desde `controllers/pioneer_TFM/configuracion/generated_map.json`, que a su vez se genera a partir del mundo de Webots.

## Comparativa experimental

El script `controllers/pioneer_TFM/experimentos/datos_comparados.py` ejecuta una comparativa sobre la mision completa (A*, Greedy y Dijkstra, cada uno con sus heuristicas compatibles) y genera:

- salida tabulada en consola con longitud de ruta, coste, nodos expandidos, tiempo, eficiencia y factor de expansion,
- y `controllers/pioneer_TFM/experimentos/resultados_experimentos.csv`.

Para lanzarla:

```bash
python3 controllers/pioneer_TFM/experimentos/datos_comparados.py
```

Adicionalmente, `herramientas/metricas.py` ofrece un benchmark mas ligero (un unico par inicio-objetivo) util para medir el coste de cada heuristica de forma aislada:

```bash
python3 controllers/pioneer_TFM/herramientas/metricas.py
```

## Visualizacion del mapa

Para depurar la rejilla y el camino planificado:

```bash
python3 controllers/pioneer_TFM/herramientas/dump_map.py         # mapa con ruta A*
python3 controllers/pioneer_TFM/herramientas/dump_map_simple.py  # mision completa simplificada
```

Ambos guardan un `.png` junto al script.

## Notas

- El repositorio esta orientado a experimentacion academica y presentacion de resultados de TFM.
- El punto de entrada `pioneer_TFM.py` debe permanecer en la raiz del directorio del controlador por convencion de Webots (el nombre del archivo y el de su carpeta coinciden obligatoriamente).
