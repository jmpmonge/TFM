# TFM - Navegacion Autonoma con Pioneer 3-AT en Webots

Proyecto de simulacion en `Webots` para un robot `Pioneer 3-AT` centrado en planificacion de rutas sobre rejilla, comparativa de algoritmos y ejecucion de misiones con multiples objetivos.

## Objetivo

El proyecto modela un entorno con obstaculos en `worlds/pioneer3at.wbt`, genera una representacion discreta del mapa y ejecuta una mision de navegacion que:

- parte de una salida fija,
- visita varios objetivos,
- tiene en cuenta una restriccion de bateria,
- y sigue la ruta calculada dentro de la simulacion.

## Funcionalidades principales

- Planificacion con `A*`, `A*_Weighted` y `A*_Multi`.
- Heuristicas configurables: Manhattan, Euclidiana, Energia y Ponderada.
- Extraccion automatica de obstaculos y objetivos desde el mundo Webots a `generated_map.json`.
- Mision multiobjetivo con vuelta a base.
- Visualizacion simple del nivel de bateria durante la simulacion.
- Comparativa experimental de algoritmos y heuristicas con exportacion a CSV.

## Estructura del proyecto

```text
pioneer_TFM/
├── worlds/
│   └── pioneer3at.wbt
├── controllers/
│   └── pioneer_TFM/
│       ├── pioneer_TFM.py
│       ├── config.py
│       ├── algoritmos.py
│       ├── heuristicas.py
│       ├── mapa.py
│       ├── seguimiento.py
│       ├── robot_io.py
│       ├── datos_comparados.py
│       ├── generated_map.json
│       └── herramientas/
│           ├── extract_wbt_to_json.py
│           ├── dump_map.py
│           └── metricas.py
└── README.md
```

## Requisitos

- `Webots R2025a`
- `Python 3`

## Ejecucion

1. Abre `worlds/pioneer3at.wbt` en Webots.
2. Comprueba que el controlador asociado al robot es `controllers/pioneer_TFM/pioneer_TFM.py`.
3. Ejecuta la simulacion.

Si modificas el mundo (`.wbt`) y cambias obstaculos u objetivos, regenera el mapa con:

```bash
python3 controllers/pioneer_TFM/herramientas/extract_wbt_to_json.py
```

## Configuracion

Los parametros principales se ajustan en `controllers/pioneer_TFM/config.py`:

- `ALGORITMO`: variante de planificacion activa.
- `HEURISTICA`: heuristica usada en la estimacion.
- `BATERIA_MAX`: presupuesto de bateria de la mision.
- `INICIO_MUNDO`: posicion inicial del robot.

Los objetivos se cargan automaticamente desde `controllers/pioneer_TFM/generated_map.json`, que a su vez se genera a partir del mundo de Webots.

## Comparativa experimental

El script `controllers/pioneer_TFM/datos_comparados.py` ejecuta una comparativa sobre la mision completa y genera:

- salida tabulada en consola,
- y `controllers/pioneer_TFM/resultados_experimentos.csv`.

Para lanzarla:

```bash
python3 controllers/pioneer_TFM/datos_comparados.py
```

## Notas

- El archivo `controllers/pioneer_TFM/READ.MD` contiene documentacion antigua y no refleja del todo la estructura actual.
- El repositorio esta orientado a experimentacion academica y presentacion de resultados de TFM.
