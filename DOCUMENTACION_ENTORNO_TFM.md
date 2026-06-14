# Documentación del entorno experimental del TFM

| Elemento | Archivo real | Función o variable | Función dentro del sistema |
| -------- | ------------ | ------------------ | -------------------------- |
| Mundo Webots | `worlds/pioneer3at.wbt` | nodos `DEF` (`PIONEER_3AT`, `START_MARKER`, `GOAL_ARA`, `COST_ZONE_*`, `WALL_*`) | Define arena 24×24 m, robot, muros, zonas de coste, inicio y objetivos |
| Generación del JSON | `controllers/pioneer_TFM/herramientas/extract_wbt_to_json.py` | `generar_mapa_json()`, `cargar_mapa_desde_wbt()` | Parsea el `.wbt` línea a línea y escribe `generated_map.json` |
| Carga del JSON | `controllers/pioneer_TFM/configuracion/config.py` | `cargar_mapa_desde_wbt()` (al importar), variables `mapa`, `OBSTACULOS`, `GOALS`, `START` | Construye `GRID`, celdas de inicio/objetivo y parámetros del mapa |
| Conversión a grid | `controllers/pioneer_TFM/configuracion/config.py` | `mundo_a_rejilla()`, `centro_celda()`, `_GRID_BASE`, `aplicar_margen_contorno()` | Discretiza obstáculos del JSON en matriz 48×48 con margen de seguridad |
| Selección de algoritmo | `controllers/pioneer_TFM/simulacion/menu_heuristica.py` | `elegir_configuracion()`, `elegir_algoritmo()` | Menú por teclado en Webots; escribe `config.ALGORITMO`, `config.HEURISTICA`, `config.MODO_ARA` |
| Cálculo de ruta | `controllers/pioneer_TFM/planificacion/mision.py` | `planificar_mision()`, `preparar_ruta()` en `algoritmos.py` | Planifica ida a objetivos válidos y vuelta a base; devuelve listas de celdas |
| Movimiento del robot | `controllers/pioneer_TFM/pioneer_TFM.py`, `simulacion/seguimiento.py`, `simulacion/robot_io.py` | `decidir()`, `seguir_camino()`, `fijar_velocidad_ruedas()` | Sigue waypoints en coordenadas mundo; control diferencial por ruedas |
| Generación de mapas | `controllers/pioneer_TFM/herramientas/MAPAS/mundo_a_grid.py`, `dibujo_mapa.py` | `main()`, `guardar_mapa()` | Genera `map_ida.png`, `map_vuelta.png`, `map_ida_vuelta.png` |

---

## 1. Resumen general del sistema

**Confirmado en el código:** El proyecto simula un Pioneer 3-AT en Webots sobre un laberinto discretizado en rejilla 48×48 (celda 0,5 m) en una arena de 24×24 m. Al importar `config.py`, se lee `worlds/pioneer3at.wbt`, se regenera `generated_map.json` y se construye la matriz `GRID`. El controlador `pioneer_TFM.py` carga parámetros desde `experimento.json`, muestra un menú interactivo de algoritmo/heurística/modo ARA*, planifica la misión completa (ida + vuelta) y ejecuta la ruta como secuencia de waypoints en coordenadas Webots.

**Confirmado en el código:** Los algoritmos de búsqueda operan sobre un **grafo implícito 8-conectado** definido por la rejilla (`planificacion/algoritmos.py`, `MOVIMIENTOS` y `_vecinos()`). No existe una estructura de grafo explícita en memoria.

**Confirmado en el código:** Existe un único controlador Webots activo: `controllers/pioneer_TFM/pioneer_TFM.py` (nombre de carpeta y archivo coincidentes, convención Webots).

---

## 2. Archivos principales

| Ruta | Rol |
| ---- | --- |
| `worlds/pioneer3at.wbt` | Mundo Webots: arena, robot, muros, zonas, marcadores |
| `controllers/pioneer_TFM/pioneer_TFM.py` | Punto de entrada del controlador |
| `controllers/pioneer_TFM/configuracion/config.py` | Parámetros, carga del mapa, construcción de `GRID` |
| `controllers/pioneer_TFM/configuracion/experimento.json` | Costes de zona, batería, epsilons ARA*, suelo cambiante |
| `controllers/pioneer_TFM/configuracion/generated_map.json` | Salida de extracción; entrada para `config.py` |
| `controllers/pioneer_TFM/herramientas/extract_wbt_to_json.py` | Extracción `.wbt` → JSON |
| `controllers/pioneer_TFM/planificacion/algoritmos.py` | Dijkstra, Greedy, A*, A* ponderado |
| `controllers/pioneer_TFM/planificacion/ara.py` | ARA* offline |
| `controllers/pioneer_TFM/planificacion/ara_anytime.py` | Modo `anytime_simple` y suelo cambiante |
| `controllers/pioneer_TFM/planificacion/heuristicas.py` | Manhattan, Euclídea, Octil |
| `controllers/pioneer_TFM/planificacion/costes.py` | Coste de movimiento y batería |
| `controllers/pioneer_TFM/planificacion/mapa.py` | Conversión celda ↔ mundo (capa planificación) |
| `controllers/pioneer_TFM/planificacion/mision.py` | Misión multiobjetivo con batería |
| `controllers/pioneer_TFM/simulacion/menu_heuristica.py` | Menú por teclado |
| `controllers/pioneer_TFM/simulacion/robot_io.py` | Supervisor, ruedas, display, pose |
| `controllers/pioneer_TFM/simulacion/seguimiento.py` | Seguimiento de waypoints |
| `controllers/pioneer_TFM/herramientas/MAPAS/mundo_a_grid.py` | Script offline de mapas PNG |
| `controllers/pioneer_TFM/herramientas/MAPAS/dibujo_mapa.py` | Renderizado matplotlib |
| `controllers/pioneer_TFM/herramientas/MAPAS/panel_simple.py` | Leyenda y datos del panel |
| `README.md` | Documentación general (parcialmente desactualizada respecto al código actual) |

**No localizado:** `dump_map.py` y `dump_map_simple.py` citados en `README.md` no existen en el repositorio; la visualización actual usa `herramientas/MAPAS/mundo_a_grid.py`.

---

## 3. Configuración del mundo en Webots

### Archivo del mundo

**Confirmado en el código:** `worlds/pioneer3at.wbt`.

### Objetos principales

**Confirmado en el código** (`worlds/pioneer3at.wbt`):

| Elemento | Representación | Notas |
| -------- | -------------- | ----- |
| Arena | `RectangleArena` | `floorSize 24 24`, `floorTileSize 0.5 0.5` (líneas 27–38) |
| Robot | `DEF PIONEER_3AT Pioneer3at` | `controller "pioneer_TFM"`, `supervisor TRUE` (líneas 59–86) |
| Inicio lógico | `DEF START_MARKER Solid` | Cilindro azul; `translation -4.5 9.75 0.015` (líneas 40–57) |
| Objetivo visual auxiliar | `DEF GOAL_MARKER Solid` | Cilindro rojo; misma posición que `GOAL_ARA` (líneas 87–104) |
| Objetivo lógico | `DEF GOAL_ARA Solid` | Esfera roja; `translation -0.75 7.15 0.55` (líneas 106–124) |
| Zonas de coste | `DEF COST_ZONE_1/2/3 Solid` | Cajas semitransparentes sobre el suelo (líneas 125–174) |
| Muros | `DEF WALL_* Solid` | 14 muros tipo caja (`Box`) |

### Muros

**Confirmado en el código:** Cada muro es un `Solid` con geometría `Box` y campos `translation` + `size`. Nombres `DEF` detectados en el `.wbt`:

- `WALL_LEFT_TOP`, `WALL_LEFT`, `WALL_RIGHT_INNER`, `WALL_RIGHT_OUTER`
- `WALL_001`, `WALL_002`, `WALL_004`, `WALL_005`, `WALL_006`, `WALL_008`, `WALL_010`, `WALL_012`, `WALL_013`, `WALL_016`

**Confirmado en el código:** `extract_wbt_to_json.extraer_obstaculos_y_muros()` (aprox. líneas 204–268) los exporta como objetos `"type": "box"` con campos `x`, `y`, `z`, `size_x`, `size_y`, `size_z`.

### Robot

**Confirmado en el código:** Prototipo `Pioneer3at` con `DEF PIONEER_3AT`. Posición inicial en el `.wbt`: `translation -4.250000072604639 9.750000001168623 ...` (línea 68). El controlador asociado es `"pioneer_TFM"`.

Dispositivos relevantes en `extensionSlot` (`worlds/pioneer3at.wbt`, líneas 72–85): `SickLms291`, `GPS`, `InertialUnit` (`name "imu"`), `Display` (140×36).

**Confirmado en el código:** `simulacion/robot_io.py` obtiene el nodo con `supervisor.getFromDef("PIONEER_3AT")` (líneas 17–19) y controla ruedas `"front left wheel"`, `"back left wheel"`, `"front right wheel"`, `"back right wheel"`.

### Posición inicial

**Confirmado en el código:** La extracción usa `START_MARKER`, no la `translation` del robot:

- `extract_wbt_to_json.extraer_inicio()` (aprox. líneas 408–428): prioriza `DEF START_MARKER`; si no existe, usa `Pioneer3at`.
- Valor extraído actual en `generated_map.json`: `"start": {"name": "START", "x": -4.5, "y": 9.75, "z": 0.015}`.
- `config.py` asigna `INICIO_MUNDO = (START["x"], START["y"])` si existe `START` (aprox. líneas 102–105).

**Confirmado en el código:** `experimento.json` puede sobreescribir inicio vía `config_menu.aplicar_a_config()` si la celda es transitable (`config_menu.py`, aprox. líneas 178–185). Valor actual en `experimento.json`: `[-4.5, 9.75]`.

**Confirmado en el código:** Tras planificar, `pioneer_TFM.py` reposiciona el robot con `colocar_inicio(config.INICIO_MUNDO[0], config.INICIO_MUNDO[1], orientacion=...)` (`robot_io.py`, `colocar_inicio()`, aprox. líneas 54–59).

### Objetivos

**Confirmado en el código:** `extract_wbt_to_json.extraer_objetivos()` (aprox. líneas 370–401) recoge nodos `DEF GOAL_* Solid` excepto `GOAL_MARKER`.

Objetivo activo en el JSON: `GOAL_ARA` en `(-0.75, 7.15)`.

**Confirmado en el código:** `config.py` (aprox. líneas 107–112):

```python
if GOALS:
    OBJETIVOS_MUNDO = [(goal["x"], goal["y"]) for goal in GOALS]
else:
    OBJETIVOS_MUNDO = OBJETIVOS_MUNDO_POR_DEFECTO
```

### Zonas de coste

**Confirmado en el código:** Geometría en el `.wbt` como cajas semitransparentes:

| DEF | Posición (`translation`) | Tamaño (`size`) | Color base |
| --- | ------------------------ | --------------- | ---------- |
| `COST_ZONE_1` | `1.5 10.25 0.008` | `3 3.5 0.01` | azul |
| `COST_ZONE_2` | `-8.5 -1 0.008` | `7 3 0.01` | verde |
| `COST_ZONE_3` | `0 -4.5 0.008` | `3 2 0.01` | naranja/amarillo |

**Confirmado en el código:** Los **valores numéricos de coste g** no vienen del `.wbt`. Se definen en `config.py` (`COSTE_ZONA_1/2/3`, aprox. líneas 16–18) y se pueden cargar desde `experimento.json` vía `config_menu.cargar_desde_archivo()`.

Valores por defecto en `config.py`: 1, 5, 10. Valores en `experimento.json` actual: 1, 5, 20.

### Nombres `DEF` relevantes

`START_MARKER`, `PIONEER_3AT`, `GOAL_MARKER`, `GOAL_ARA`, `GOAL_GEOM`, `COST_ZONE_1`, `COST_ZONE_2`, `COST_ZONE_3`, y los 14 `WALL_*` listados arriba.

### Controlador asociado

**Confirmado en el código:** `controller "pioneer_TFM"` en `DEF PIONEER_3AT` → ejecuta `controllers/pioneer_TFM/pioneer_TFM.py`.

### Parámetros del mundo importantes para el experimento

**Confirmado en el código:**

- `WorldInfo.info`: `"48x48 logical grid at 0.5 m/cell."` (líneas 11–14)
- `RectangleArena.floorSize 24 24` → límites mundo ±12 m en X e Y
- `floorTileSize 0.5 0.5` → `CELL_SIZE = 0.5` m
- `lineScale 0.5` en `WorldInfo` (línea 16)
- Robot con `supervisor TRUE` (necesario para menú, pose y display)

---

## 4. Extracción del escenario

### Qué lee el `.wbt`

**Confirmado en el código:** `controllers/pioneer_TFM/herramientas/extract_wbt_to_json.py`.

Funciones principales:

| Función | Datos extraídos |
| ------- | --------------- |
| `leer_lineas()` | Lee el archivo texto `.wbt` |
| `extraer_floor_size()` | Tamaño de la arena |
| `extraer_floor_tile_size()` | Tamaño de celda lógica |
| `extraer_obstaculos_y_muros()` | Muros (`DEF WALL_*`) y obstáculos (`DEF OBSTACLE_*`) |
| `extraer_zonas_coste()` | Cajas `DEF COST_ZONE_*` |
| `extraer_objetivos()` | `DEF GOAL_*` excepto `GOAL_MARKER` |
| `extraer_inicio()` | `DEF START_MARKER` o fallback `Pioneer3at` |
| `zona_coste_a_rejilla()` | Celdas de cada zona |
| `generar_mapa_json()` | Ensambla el diccionario y escribe JSON |

### Método de extracción

**Confirmado en el código:** Parsing **directo del archivo `.wbt`** (texto VRML), **no** mediante Supervisor en tiempo de simulación.

**Confirmado en el código:** Existe `resolver_wbt_activo()` (aprox. líneas 537–552) que intenta usar `supervisor.getWorldPath()` si `robot_io.supervisor` ya está cargado; pero **`config.py` no lo usa al importar**: pasa ruta fija `_WBT_MAPA = worlds/pioneer3at.wbt` (aprox. líneas 79–87).

**Confirmado en el código:** Existe `sincronizar_si_necesario()` (aprox. líneas 529–534) que solo regenera si el `.wbt` es más reciente que el JSON, pero **no se invoca desde ningún otro módulo del proyecto** (búsqueda en el repositorio).

### Cuándo se genera `generated_map.json`

**Confirmado en el código:**

1. **Siempre al importar `config.py`:** `cargar_mapa_desde_wbt(wbt_path=str(_WBT_MAPA), ...)` con `escribir_json=True` (aprox. líneas 84–88).
2. **Manualmente:** `python3 controllers/pioneer_TFM/herramientas/extract_wbt_to_json.py` → `main()` → `generar_mapa_json(verbose=True)` (aprox. líneas 566–571).

**Inferencia:** El JSON en disco se **sobrescribe en cada arranque** del controlador (import de `config`), aunque el `.wbt` no haya cambiado.

### Transformación de coordenadas en extracción

**Confirmado en el código** (`generar_mapa_json()`, aprox. líneas 464–470):

```python
origen_x = -floor_x / 2.0
origen_y = -floor_y / 2.0
```

Para arena 24×24: `origen_x = origen_y = -12.0`, `x_limits = [-12, 12]`, `y_limits = [-12, 12]`.

Las posiciones de obstáculos/zonas/objetivos se leen directamente del campo `translation` del `.wbt` (metros, sistema Webots).

---

## 5. Estructura de `generated_map.json`

### Quién lo crea y quién lo carga

| Fase | Módulo | Función |
| ---- | ------ | ------- |
| Creación | `extract_wbt_to_json.py` | `generar_mapa_json()` |
| Carga | `config.py` | `cargar_mapa_desde_wbt()` → variable `mapa` |

**Confirmado en el código:** El JSON es **salida** de la extracción y **entrada** inmediata para construir `GRID` en el mismo import de `config.py`.

### Estructura y claves

**Confirmado en el código** (estructura real, valores actuales):

```json
{
  "x_limits": [-12.0, 12.0],
  "y_limits": [-12.0, 12.0],
  "grid_cols": 48,
  "grid_rows": 48,
  "grid_cells": 48,
  "cell_size": 0.5,
  "obstacle_radius": 0.4,
  "obstacles": [
    {
      "name": "WALL_LEFT_TOP",
      "type": "box",
      "x": -4.75, "y": 7.0, "z": 0.25,
      "size_x": 0.5, "size_y": 1.0, "size_z": 0.5
    }
  ],
  "cost_zones": [
    {
      "name": "COST_ZONE_1",
      "type": "box",
      "cost": 1.0,
      "x": 1.5, "y": 10.25, "z": 0.008,
      "size_x": 3, "size_y": 3.5, "size_z": 0.01,
      "grid": {
        "row_ini": ..., "row_fin": ...,
        "col_ini": ..., "col_fin": ...,
        "cells": [[fila, col], ...]
      }
    }
  ],
  "goals": [{"name": "GOAL_ARA", "x": -0.75, "y": 7.15, "z": 0.55}],
  "start": {"name": "START", "x": -4.5, "y": 9.75, "z": 0.015}
}
```

### Significado de campos

| Campo | Representación | Unidades |
| ----- | -------------- | -------- |
| `x_limits`, `y_limits` | Extensión del mapa | metros (Webots) |
| `grid_cols`, `grid_rows` | Dimensiones de la rejilla | celdas enteras |
| `cell_size` | Tamaño de celda | metros |
| `obstacles` | Geometría continua de muros | coordenadas mundo + dimensiones |
| `cost_zones` | Geometría continua + `grid.cells` discretas | mixto |
| `cost` en zona | Valor inferido del nombre (`COST_ZONE_N → N.0`) | solo informativo en JSON |
| `start`, `goals` | Posiciones lógicas | coordenadas mundo continuas |

**Confirmado en el código:** Los costes de planificación **no** usan el campo `"cost"` del JSON; usan `COSTE_ZONA_1/2/3` de `config.py` (`config.py`, `coste_de_zona()`, aprox. líneas 234–240).

### Archivos que dependen del JSON

**Confirmado en el código:** Principalmente `config.py` (directamente). Indirectamente: todo módulo que importa `config` (`planificacion/*`, `pioneer_TFM.py`, `mundo_a_grid.py`, etc.).

---

## 6. Conversión del mundo a grid

### Archivo y función principal

**Confirmado en el código:** La conversión ocurre en **`config.py` al importar el módulo**, no en `mundo_a_grid.py`.

- `mundo_a_grid.py` **visualiza** el `GRID` ya construido; no genera la rejilla.

Secuencia en `config.py` (aprox. líneas 220–252):

1. Inicializar `_GRID_BASE` a 0.
2. Marcar celdas ocupadas por obstáculos (`celda_ocupada()`).
3. Aplicar margen: `GRID = aplicar_margen_contorno(_GRID_BASE)`.
4. Pintar zonas de coste en `GRID` con `COSTE_ZONA_*`.

### Tamaño del grid

**Confirmado en el código:**

- Arena: 24 m × 24 m (`floorSize 24 24`)
- Celda: 0,5 m (`floorTileSize 0.5 0.5` / `CELL_SIZE`)
- Rejilla: **48 × 48** (`grid_cols`, `grid_rows` en JSON y `COLUMNAS_MAPA`, `FILAS_MAPA` en `config.py`)

### Fórmulas de conversión

**Confirmado en el código** (`config.py`, `mundo_a_rejilla()`, aprox. líneas 136–142; replicado en `planificacion/mapa.py`, aprox. líneas 17–27):

```python
col = int((x - ORIGEN_MAPA_X) / CELL_SIZE)
row = int(((ORIGEN_MAPA_Y + FILAS_MAPA * CELL_SIZE) - y) / CELL_SIZE)
col = max(0, min(COLUMNAS_MAPA - 1, col))
row = max(0, min(FILAS_MAPA - 1, row))
```

Inversa, centro de celda (`centro_celda()`, aprox. líneas 145–148):

```python
x = ORIGEN_MAPA_X + col * CELL_SIZE + CENTRO_CELDA
y = ORIGEN_MAPA_Y + (FILAS_MAPA - 1 - row) * CELL_SIZE + CENTRO_CELDA
```

Donde `ORIGEN_MAPA_X = X_LIMITS[0]`, `ORIGEN_MAPA_Y = Y_LIMITS[0]`, `CENTRO_CELDA = CELL_SIZE / 2`.

**Confirmado en el código:** Fila 0 = parte superior del mapa (Y alto en Webots).

### Representación de celdas

| Valor en `_GRID_BASE` / `GRID` | Significado |
| ------------------------------ | ----------- |
| `0` | Celda libre (sin muro físico) |
| `1` | Muro físico o celda de margen de seguridad |
| `> 1` (p. ej. 1, 5, 20) | Celda de zona de coste (transitable) |

**Confirmado en el código:** `celda_bloqueada()` (aprox. líneas 262–268):

- Bloqueada si `_GRID_BASE[row][col] == 1` (muro físico).
- Las celdas en `CELDAS_COSTE` **nunca** se bloquean aunque `GRID` tenga valor numérico de coste.

### Margen de seguridad

**Confirmado en el código:** `MARGEN_SEGURIDAD = 0.3` (metros, `config.py`, línea 93) actúa como **flag**: si `<= 0`, no se aplica margen.

Implementación real: **`aplicar_margen_contorno()`** (aprox. líneas 187–213) — dilatación de 1 celda en **8 vecinos** alrededor de cada celda con muro en `_GRID_BASE`. No usa distancia euclídea `< 0.3 m` en la versión actual.

**Confirmado en el código:** En visualización (`dibujo_mapa.py`):

- Muro físico: `_GRID_BASE == 1` → gris oscuro (`COLOR_MURO`)
- Margen: `GRID == 1` pero `_GRID_BASE == 0` → gris claro (`COLOR_SEGURIDAD`)

### Zonas de coste en grid

**Confirmado en el código:** `extract_wbt_to_json.zona_coste_a_rejilla()` calcula qué celdas caen dentro de la caja Webots. En `config.py`, solo se activan celdas libres (`GRID[_row][_col] == 0` antes de asignar coste) y se guardan en `CELDAS_POR_ZONA`.

### Inicio y objetivos en grid

**Confirmado en el código** (`config.py`, aprox. líneas 288–315):

```python
CELDA_INICIO = mundo_a_rejilla(INICIO_MUNDO[0], INICIO_MUNDO[1])
CELDAS_OBJETIVO = [mundo_a_rejilla(x, y) for x, y in OBJETIVOS_MUNDO]
```

Se valida que inicio y objetivos no estén bloqueados (`celda_bloqueada()`).

### Límites del mapa

**Confirmado en el código:** `mundo_a_rejilla()` **recorta** coordenadas al rango `[0, COLUMNAS-1]` × `[0, FILAS-1]`. No hay inflación de borde de arena más allá de los muros definidos en el `.wbt`.

---

## 7. Construcción del espacio de búsqueda

### Grafo implícito vs explícito

**Confirmado en el código:** **Grafo implícito** sobre la rejilla. No hay lista de aristas ni objeto `Grafo`.

### Nodos y aristas

| Concepto | Representación |
| -------- | -------------- |
| Nodo | Celda `(fila, col)` |
| Arista | Paso a celda vecina libre |
| Coste de arista | `coste_movimiento(actual, vecino)` en `costes.py` |

### Movimientos permitidos

**Confirmado en el código** (`algoritmos.py`, línea 9):

```python
MOVIMIENTOS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
```

- Ortogonales y diagonales (8-conectividad).
- Vecinos generados en `_vecinos()` (aprox. líneas 140–145) filtrando con `es_libre()` → `config.celda_bloqueada()`.

### Costes de movimiento

**Confirmado en el código** (`costes.py`, `coste_movimiento()`, aprox. líneas 34–40):

- Ortogonal: coste base de la celda destino (`coste_base_celda(vecino)`).
- Diagonal: coste base × `sqrt(2)`.

```python
base = coste_base_celda(vecino)
if _es_paso_diagonal(actual, vecino):
    return base * math.sqrt(2)
```

**Confirmado en el código:** `coste_base_celda()`: celda libre → 1.0; celda en `CELDAS_COSTE` → valor de `GRID`.

### Muros y esquinas

**Confirmado en el código:** Solo se comprueba que la celda destino sea libre. **No hay comprobación anti-corte-de-esquina** (no se verifican las dos celdas ortogonales adyacentes en un paso diagonal).

### Incorporación de costes de zona

**Confirmado en el código:** El coste de zona entra en `coste_base_celda()` al evaluar la celda destino del paso. Las zonas son transitables gracias a `celda_bloqueada()`.

---

## 8. Algoritmos y heurísticas

### Dijkstra

| Aspecto | Detalle |
| ------- | ------- |
| Archivo | `planificacion/algoritmos.py` |
| Función | `dijkstra(inicio, objetivo, heuristica=None)` (aprox. línea 16) |
| Núcleo | `_buscar_camino(..., usar_coste=True, heuristica=h_nula)` |
| Heurística | `h_nula` → 0 |
| Evaluación | Prioridad = `g(n)` |
| Retorno | `(camino: list[(fila,col)], nodos_explorados: int)` |
| Llamado desde | `preparar_ruta()`, `planificar_mision()`, `mundo_a_grid.py` |

### Greedy (Best-First)

| Aspecto | Detalle |
| ------- | ------- |
| Función | `greedy(inicio, objetivo, heuristica)` (aprox. línea 19) |
| Evaluación | Prioridad = `h(n)` (`usar_coste=False`) |
| Heurística | Obligatoria (Manhattan, Euclídea u Octil) |

### A*

| Aspecto | Detalle |
| ------- | ------- |
| Función | `astar(inicio, objetivo, heuristica)` (aprox. línea 22) |
| Evaluación | `f(n) = g(n) + h(n)` (`peso_heuristica=1.0`) |

### A* ponderado

| Aspecto | Detalle |
| ------- | ------- |
| Función | `astar_ponderado(inicio, objetivo, heuristica, peso_heuristica=None)` (aprox. líneas 25–47) |
| Evaluación | `f(n) = g(n) + w · h(n)` |
| Peso por defecto | `config.PESO_ASTAR_PONDERADO` (1.5 en `config.py`; 1.5 en `experimento.json`) |
| Uso en ARA* | Modo `anytime_simple` usa `peso_heuristica=epsilon` |

### ARA*

| Aspecto | Detalle |
| ------- | ------- |
| Archivo offline | `planificacion/ara.py` → `planificar_ara_offline()`, `ara_star()` |
| Archivo anytime | `planificacion/ara_anytime.py` → `planificar_ara_anytime_simple()` |
| Entrada | `(inicio, objetivo, heuristica)` + epsilons desde config |
| Retorno | `(camino, nodos_totales)` vía `ara_star()` |
| Informe | `ULTIMO_INFORME_ARA`, acumulado en `INFORME_ARA_MISION` por tramo (`preparar_ruta()`, aprox. líneas 186–188) |

### Selección de algoritmo

**Confirmado en el código:**

- Por defecto: `config.ALGORITMO = "ara_star"` (`config.py`, línea 48).
- En Webots: menú teclado → `config.ALGORITMO` (`menu_heuristica.py`, `elegir_configuracion()`, aprox. líneas 210–221).
- Resolución: `resolver_algoritmo()` / `_normalizar_algoritmo()` en `algoritmos.py`.

### Métricas calculadas

**Confirmado en el código** (`logs_planificacion.imprimir_resumen_planificacion()`, aprox. líneas 56–73):

- Longitud en celdas
- `coste g` → `coste_camino()` (suma de `coste_movimiento`)
- Coste energía → `coste_bateria_camino()`
- Nodos explorados (suma por tramos)
- Detalle ARA* por tramo si aplica

---

## 9. Implementación de ARA*

### Dos modos

**Confirmado en el código:** `config.MODO_ARA`: `"offline"` | `"anytime_simple"` (por defecto `"anytime_simple"`, `config.py` línea 55). Se elige en menú Webots si algoritmo = ARA* (`menu_heuristica.elegir_modo_ara()`).

### Epsilons

**Confirmado en el código** (`ara.py`, `_epsilons_ara()`, aprox. líneas 30–44):

```python
epsilon = config.EPSILON_INICIAL_ARA  # 5
while epsilon >= config.EPSILON_FINAL_ARA:  # 1.0
    valores.append(round(epsilon, 2))
    epsilon -= config.EPSILON_PASO_ARA  # 1
```

Secuencia: **5 → 4 → 3 → 2 → 1** (con valores actuales de `config.py` / `experimento.json`).

Configurables en `config.py` y `experimento.json`: `EPSILON_INICIAL_ARA`, `EPSILON_FINAL_ARA`, `EPSILON_PASO_ARA`.

### Modo offline (`planificar_ara_offline`)

**Confirmado en el código** (`ara.py`, aprox. líneas 131–183):

- Búsqueda **hacia atrás desde el objetivo** (`OPEN = [objetivo]`, `g(objetivo) = 0`).
- `_improve_path_ara()` expande predecesores con `_vecinos()`.
- Clave: `KEY(s) = g(s) + epsilon * h(inicio, s)` (`_key_ara()`, aprox. líneas 47–51) — heurística hacia **inicio**, no hacia objetivo.
- Entre fases de epsilon: nodos en `INCONS` vuelven a `OPEN`; `closed` se vacía; **`g` y `sucesor` se conservan** (reutilización parcial).
- Historial por epsilon en `historial[]` con `ruta`, `coste`, `nodos`.
- Devuelve `mejor_camino` (última ruta válida inicio→objetivo).

**Diferencia respecto al ARA* teórico:** La heurística en `KEY` apunta al inicio (búsqueda reversa). El modo offline planifica **toda la ruta antes** de mover el robot.

### Modo anytime_simple (`planificar_ara_anytime_simple`)

**Confirmado en el código** (`ara_anytime.py`, aprox. líneas 112–181):

- **No usa** `_improve_path_ara`. En cada fase llama a `astar_ponderado(posicion_actual, objetivo, heuristica, peso_heuristica=epsilon)`.
- Simula avance: `_avanzar_sobre_ruta(..., pasos_por_fase)` con `pasos_por_fase = config.PASOS_POR_FASE_ARA` (5).
- Suelo cambiante en fase `i == 1` (segundo epsilon): `actualizar_suelo_cambiante_si_toca(1)`.
- Sustitución de ruta activa si: primera fase, suelo actualizado, o `nuevo_coste < coste_restante_actual`.
- Almacenamiento:
  - `historial[]`: por fase, con `ruta_calculada`, `accion`, `epsilon`, etc.
  - `ruta_ejecutada`: camino simulado acumulado (retorno de la función).
  - `ULTIMO_INFORME_ARA["ruta_ejecutada"]` y `["ruta_final"]` en `ara_star()` (aprox. líneas 203–210).

**Diferencia respecto al ARA* teórico:** Es una **simulación por fases** con A* ponderado repetido, no la reparación incremental de OPEN/CLOSED/INCONS del pseudocódigo clásico.

### `PASOS_POR_FASE_ARA`

**Confirmado en el código:**

| Contexto | Archivo | Comportamiento |
| -------- | ------- | -------------- |
| Planificación anytime | `ara_anytime.py` | Avanza `PASOS_POR_FASE_ARA` celdas sobre `ruta_activa` tras cada fase |
| Simulación Webots | `pioneer_TFM.py` (aprox. líneas 113–114) | Si `INDICE_OBJETIVO >= PASOS_POR_FASE_ARA`, llama `actualizar_suelo_cambiante_si_toca(1)` |

**Confirmado en el código:** En Webots, el contador es **waypoints alcanzados** (`INDICE_OBJETIVO`), no segundos de simulación.

### Mapas PNG en modo anytime

**Confirmado en el código** (`mundo_a_grid.py`, aprox. líneas 60–65; `dibujo_mapa.dibujar_camino_anytime()`, aprox. líneas 219–238):

- `map_ida.png`: rutas inicial (gris `0.55`), recalculadas (naranja `darkorange`) y final (verde) del informe anytime del primer tramo de ida.
- `map_vuelta.png`: solo ruta de vuelta (círculos azules huecos).
- `map_ida_vuelta.png`: ida (verde) + vuelta (azul hueco), o solo verde si ida == vuelta invertida.

---

## 10. Zonas de coste y suelo cambiante

### Definición de costes

**Confirmado en el código:**

| Zona | Variable | Default `config.py` | `experimento.json` actual |
| ---- | -------- | ------------------- | ------------------------- |
| Azul (`COST_ZONE_1`) | `COSTE_ZONA_1` | 1 | 1 |
| Verde (`COST_ZONE_2`) | `COSTE_ZONA_2` | 5 | 5 |
| Amarilla (`COST_ZONE_3`) | `COSTE_ZONA_3` | 10 | 20 |

Asignación a celdas: bucle en `config.py` (aprox. líneas 243–252) al construir `CELDAS_POR_ZONA`.

### Activación del suelo cambiante

**Confirmado en el código:** `config.SUELO_CAMBIANTE = True` (default y en `experimento.json`).

Función: `actualizar_suelo_cambiante_si_toca(indice_fase)` en `ara_anytime.py` (aprox. líneas 61–98).

Condiciones (todas necesarias):

- `_OMITIR_SUELO_CAMBIANTE == False`
- `config.SUELO_CAMBIANTE == True`
- `indice_fase == 1`
- `_SUELO_CAMBIANTE_APLICADO == False` (solo una vez)

Multiplicaciones (`ara_anytime.py`, aprox. líneas 77–85):

```python
nuevo_zona_1 = config.COSTE_ZONA_1 * 30
nuevo_zona_2 = config.COSTE_ZONA_2 / 5
nuevo_zona_3 = config.COSTE_ZONA_3  # sin cambio
```

Aplicación: `config.aplicar_costes_zonas()` reescribe valores en `GRID` para celdas de `CELDAS_POR_ZONA`.

### Cuándo cambia

**Confirmado en el código:**

1. **Durante planificación anytime:** fase con índice `i == 1` en `planificar_ara_anytime_simple()`.
2. **Durante simulación Webots:** cuando `INDICE_OBJETIVO >= PASOS_POR_FASE_ARA` (`pioneer_TFM.py`, aprox. líneas 113–114).

**Confirmado en el código:** Antes de la planificación real, `planificar_mision()` restaura costes iniciales tras filtrar objetivos por batería (`mision.py`, aprox. líneas 100–107).

### Efecto en planificación y visualización

**Confirmado en el código:** Afecta a `GRID` en memoria → cambia `coste_movimiento()` para búsquedas posteriores en la misma ejecución.

**Confirmado en el código:** Las cajas `COST_ZONE_*` en Webots **no cambian** de color/apariencia. El display del robot (`dibujar_bateria()` en `robot_io.py`) muestra los costes numéricos actuales `COSTE_ZONA_1/2/3` en texto.

---

## 11. Ejecución de la ruta por el robot

### Formato de la ruta del algoritmo

**Confirmado en el código:** Lista de celdas `[(fila, col), ...]` devuelta por algoritmos y unida por `aplanar_mision()`.

### Recepción y transformación

**Confirmado en el código** (`pioneer_TFM.py`, aprox. líneas 38–51):

```python
rutas, NODOS_EXPLORADOS = planificar_mision(...)
CAMINO_CELDAS = aplanar_mision(rutas)
PUNTOS = [celda_a_mundo(celda) for celda in CAMINO_CELDAS]
INDICE_OBJETIVO = 1 if len(PUNTOS) > 1 else 0
```

**Confirmado en el código:** El robot recibe la **ruta completa** como lista de waypoints (`PUNTOS`), no un único punto sucesivo calculado online (salvo que la planificación anytime ya haya simulado recortes en `ruta_ejecutada` antes de la ejecución).

### Control de movimiento

| Paso | Módulo | Función |
| ---- | ------ | ------- |
| Bucle principal | `pioneer_TFM.py` | `while paso():` (aprox. línea 91) |
| Lectura pose | `robot_io.py` | `leer_estado()` → `x`, `y`, `orientacion` |
| Decisión velocidades | `seguimiento.py` | `decidir()` → `seguir_camino()` |
| Actuación | `robot_io.py` | `fijar_velocidad_ruedas(left, right)` |

**Confirmado en el código** (`seguimiento.py`, `seguir_camino()`, aprox. líneas 6–30):

- Objetivo actual: `puntos[indice_objetivo]`.
- Umbral de llegada: **0,3 m** (`distancia < 0.3` → incrementa `indice_objetivo`).
- Giro: `error = angulo_deseado - orientacion` normalizado.
- Velocidades: combinación de avance (`VELOCIDAD_AVANCE = 6.4`) y giro (`VELOCIDAD_GIRO = 6.0`) desde `config.py`.

### Ida y vuelta

**Confirmado en el código** (`mision.planificar_mision()`, aprox. líneas 113–121):

1. Por cada objetivo válido (ordenados por Manhattan desde origen): tramo `posicion_actual → objetivo`.
2. Tramo final: `posicion_actual → base` (vuelta a `CELDA_INICIO`).
3. `aplanar_mision()` concatena tramos evitando duplicar la celda de unión.

**Confirmado en el código:** Objetivos intermedios existen en la lógica (`OBJETIVOS_MUNDO` es lista; filtro por batería), pero el mundo actual tiene **un solo objetivo** (`GOAL_ARA`).

### Orientación inicial

**Confirmado en el código:** `pioneer_TFM.py` (aprox. líneas 53–65) orienta el robot hacia el segundo waypoint con `atan2`.

---

## 12. Interfaz y salida de resultados

### Selección de algoritmo y heurística

**Confirmado en el código:** `simulacion/menu_heuristica.py`.

| Tecla (ventana 3D) | Efecto |
| ------------------ | ------ |
| 1–4 | Algoritmo: Dijkstra, A*, Greedy, ARA* |
| 1–3 | Heurística: Manhattan, Euclídea, Octil (no para Dijkstra → `"nula"`) |
| 1–2 | Modo ARA*: offline / anytime_simple |

Flujo: `pioneer_TFM.py` importa `menu_heuristica` **antes** que `config` (comentario líneas 3–4); luego `config_menu.cargar_desde_archivo(config)`; después `menu_heuristica.elegir_configuracion()`.

**Confirmado en el código:** `config_menu.cargar_desde_archivo()` carga `experimento.json` **sin menú interactivo** (solo lectura de archivo).

### Consola Webots

**Confirmado en el código:** Impresiones principales:

- Menús de selección (`menu_heuristica.py`)
- `config.imprimir_configuracion_planificacion()` (aprox. líneas 337–355)
- `imprimir_resumen_planificacion()` — algoritmo, heurística, longitud, coste g, coste energía, nodos, detalle ARA*
- Mensaje `SUELO CAMBIANTE ACTIVADO` (`ara_anytime.py`, aprox. líneas 87–95)
- Logs opcionales de batería (`LOG_BATERIA_CELDAS`, `LOG_BATERIA_OBJETIVOS`)

### Display visual

**Confirmado en el código:** `Display` en el robot (`robot_io.dibujar_bateria()`): barra de batería, costes de zona `Z:1/5/20`, aviso si está en celda de coste.

### Panel en mapas PNG

**Confirmado en el código:** `panel_simple.dibujar_panel()` — leyenda, algoritmo, costes, suelo cambiante, longitud, coste g, nodos.

---

## 13. Generación de mapas visuales

### Script generador

**Confirmado en el código:** `controllers/pioneer_TFM/herramientas/MAPAS/mundo_a_grid.py`.

Ejecución:

```bash
python3 controllers/pioneer_TFM/herramientas/MAPAS/mundo_a_grid.py
```

Flujo: importa `config` (regenera JSON y GRID) → `config_menu.cargar_desde_archivo()` → `planificar_mision()` → `guardar_mapa()` × 3.

### Colores y símbolos (`dibujo_mapa.py`)

| Elemento | Representación |
| -------- | -------------- |
| Libre | Fondo blanco |
| Muro físico | Gris oscuro `(0.15, 0.15, 0.15)` |
| Margen seguridad | Gris claro `(0.82, 0.82, 0.82)` |
| Zona azul/verde/amarilla | `COLORES_ZONA` con alpha 0.65 |
| Límite bloqueado | Línea roja discontinua (`COLOR_LINEA_LIMITE`) |
| Inicio | Texto **S** verde |
| Objetivos | **G1**, **G2**... rojo |
| Ida | Puntos verdes (`COLOR_IDA`) |
| Vuelta | Círculos azules huecos (`COLOR_VUELTA`, tamaño mayor) |
| Ruta anytime inicial | Puntos grises (`0.55`) |
| Ruta anytime recalculada | Puntos naranja (`darkorange`) |

### Ubicación de salida

**Confirmado en el código:** `controllers/pioneer_TFM/herramientas/MAPAS/`:

- `map_ida.png`
- `map_vuelta.png`
- `map_ida_vuelta.png`

### Diferencia entre los tres PNG

| Archivo | Contenido |
| ------- | --------- |
| `map_ida.png` | Solo tramo de ida (`rutas[0]`); en anytime muestra historial de rutas |
| `map_vuelta.png` | Solo tramo de vuelta (`rutas[-1]`) |
| `map_ida_vuelta.png` | Ambos tramos superpuestos |

---

## 14. Flujo completo del sistema

```text
worlds/pioneer3at.wbt
    ↓  (parseo texto, extract_wbt_to_json.py)
generated_map.json  ← siempre reescrito al importar config.py
    ↓  (config.py: _GRID_BASE, margen 8-vecinos, zonas COSTE_ZONA_*)
GRID 48×48 + CELDA_INICIO + CELDAS_OBJETIVO
    ↓  (experimento.json vía config_menu; menú teclado vía menu_heuristica)
config.ALGORITMO / HEURISTICA / MODO_ARA
    ↓  (planificar_mision → preparar_ruta → algoritmo elegido)
listas de celdas por tramo (ida objetivos + vuelta base)
    ↓  (aplanar_mision)
CAMINO_CELDAS
    ↓  (celda_a_mundo)
PUNTOS [(x,y), ...]  — ruta completa precalculada
    ↓  (colocar_inicio; bucle paso/decidir/fijar_velocidad_ruedas)
ejecución Webots + display batería/zona
    ↓  (opcional: suelo cambiante en INDICE_OBJETIVO >= PASOS_POR_FASE_ARA)
actualización GRID en memoria (sin cambio visual en .wbt)

Paralelo offline:
mundo_a_grid.py → planificar_mision → dibujo_mapa.guardar_mapa → PNG
```

**Nota sobre orden de arranque en Webots:**

```text
import menu_heuristica  (carga robot_io + config → 1ª extracción .wbt)
import config          (ya cargado)
config_menu.cargar_desde_archivo  (sobrescribe parámetros, no regenera geometría)
menu_heuristica.elegir_configuracion  (sobrescribe algoritmo/heurística/modo)
planificar_mision(...)
bucle simulación
```

---

## 15. Información no localizada o dudas pendientes

### No localizado

- **`dump_map.py` / `dump_map_simple.py`:** citados en `README.md` pero ausentes del repositorio.
- **Uso de `sincronizar_si_necesario()`:** definida pero no invocada; la regeneración condicional por fecha no está activa en el flujo principal.
- **Uso de `resolver_wbt_activo()` en runtime:** existe, pero `config.py` fuerza `worlds/pioneer3at.wbt` al importar; abrir otro `.wbt` en Webots no cambiaría el mapa lógico sin modificar código.
- **Comprobación anti-corte-de-esquina en diagonales:** no implementada.
- **Heurística `"agresiva"`:** mencionada en comentario de `config.py` (línea 51) pero no existe en `HEURISTICAS_DISPONIBLES`.
- **Función `colocar_meta()`:** definida en `robot_io.py` pero no llamada desde `pioneer_TFM.py`.

### Inferencias razonables

- La discrepancia entre `START_MARKER` (`-4.5, 9.75`) y `translation` del robot en el `.wbt` (`-4.25, 9.75`) es intencional: la lógica usa el marcador; el robot se reposiciona al inicio lógico al arrancar.
- `GOAL_MARKER` es solo referencia visual; la planificación usa `GOAL_ARA` vía JSON.

### Dudas para revisión manual

1. **`COSTE_ZONA_3`:** default en `config.py` es 10, pero `experimento.json` tiene 20. ¿Cuál debe documentarse como valor experimental oficial?
2. **`README.md` desactualizado:** no menciona ARA*, Octil, zonas de coste, suelo cambiante ni `mundo_a_grid.py`. ¿Actualizar README aparte de esta documentación?
3. **Suelo cambiante dual:** se activa en planificación anytime (fase ε índice 1) y en simulación Webots (`INDICE_OBJETIVO >= 5`). ¿Es el comportamiento deseado para el TFM o son dos experimentos acoplados?
4. **Regeneración incondicional del JSON** en cada import de `config`: ¿conviene usar `sincronizar_si_necesario()` para evitar reescrituras y acelerar arranque?
5. **Filtrado por batería** en `filtrar_objetivos_por_bateria()` activa `_OMITIR_SUELO_CAMBIANTE` durante simulaciones de coste: confirmar que no enmascara efectos del suelo cambiante en misiones multiobjetivo futuras.
6. **Validación experimental:** comparar si el coste g mostrado en consola coincide con expectativas cuando `USAR_FACTOR_DIAGONAL_BATERIA` difiere del factor en planificación (√2 en ambos por defecto, pero son funciones distintas).
