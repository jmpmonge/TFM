# README — Pioneer TFM

## 1. Objetivo del proyecto

Este proyecto simula un robot **Pioneer 3-AT** en **Webots** sobre un laberinto con rejilla discreta. A partir del mundo `.wbt` construye un **GRID** de planificación, asigna **costes de terreno** en zonas coloreadas y planifica una misión que va del inicio a uno o más objetivos y vuelve a la base.

Funcionalidades implementadas:

- **Simulación** del robot con supervisor de Webots, seguimiento de ruta y display de batería.
- **Mapa / rejilla**: conversión mundo ↔ celdas, obstáculos, margen de seguridad y zonas de coste.
- **Planificación de rutas** con **Dijkstra**, **A**, **Greedy** y **ARA** (modos `offline` y `anytime_simple`).
- **Heurísticas**: nula, Manhattan, euclidiana y octil.
- **Costes de suelo** configurables por zona (`COSTE_ZONA_1/2/3`) y opción de **suelo cambiante** (`SUELO_CAMBIANTE`).
- **Batería**: filtrado de objetivos y consumo durante la simulación usando el mismo coste base del terreno.
- **Herramientas offline**: mapas PNG, comparativas experimentales y scripts de prueba.

---

## 2. Flujo general de ejecución

Al arrancar el controlador en Webots ocurre lo siguiente:

```text
pioneer_TFM.py
    ↓
import configuracion/config.py
    ↓
cargar_mapa_desde_wbt()  →  lee worlds/pioneer3at.wbt  →  generated_map.json
    ↓
construye GRID (obstáculos + margen + zonas de coste)
    ↓
config_menu.cargar_desde_archivo(config)  →  experimento.json (si existe)
    ↓
menu_heuristica.elegir_configuracion()  →  teclado Webots: algoritmo, heurística, modo ARA*
    ↓
planificar_mision()  →  ida a objetivos + vuelta a base
    ↓
si SUELO_CAMBIANTE: reiniciar_suelo_cambiante()  (restaura costes para la simulación)
    ↓
aplanar_mision()  →  CAMINO_CELDAS y PUNTOS en coordenadas mundo
    ↓
colocar_inicio(), imprimir resúmenes, dibujar_bateria()
    ↓
bucle while paso():
        leer_estado()  →  decidir()  →  fijar_velocidad_ruedas()
        si SUELO_CAMBIANTE y celdas recorridas ≥ PASOS_POR_FASE_ARA:
            actualizar_suelo_cambiante_si_toca(1)
        dibujar_bateria()
```

**Nota:** la planificación ocurre **una vez al inicio**. El robot no replanifica en tiempo real; sigue la ruta ya calculada. El suelo cambiante durante la simulación actualiza `GRID` y el display, pero no recalcula la ruta en marcha.

---

## 3. Estructura de carpetas y archivos principales


| Carpeta / archivo                                                  | Función principal                                                                                         |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `worlds/pioneer3at.wbt`                                            | Mundo Webots: laberinto, muros, inicio, objetivo y superficies `COST_ZONE_1/2/3` (azul, verde, amarillo). |
| `controllers/pioneer_TFM/pioneer_TFM.py`                           | Punto de entrada del controlador Webots: carga config, menú, planifica, ejecuta bucle de simulación.      |
| `controllers/pioneer_TFM/configuracion/config.py`                  | Parámetros globales, carga del mapa, construcción de `GRID`, costes de zona e inicio/objetivo en celdas.  |
| `controllers/pioneer_TFM/configuracion/config_menu.py`             | Menú por consola y puente `experimento.json` → variables de `config` (sin `input()` en Webots).           |
| `controllers/pioneer_TFM/configuracion/experimento.json`           | Parámetros del experimento generados por `config_menu.py` y leídos al arrancar Webots.                    |
| `controllers/pioneer_TFM/configuracion/generated_map.json`         | Mapa intermedio: obstáculos, start, goals, zonas de coste y dimensiones de la rejilla.                    |
| `controllers/pioneer_TFM/planificacion/algoritmos.py`              | Algoritmos de búsqueda, ARA*, costes, batería, misión y logs de planificación.                            |
| `controllers/pioneer_TFM/planificacion/heuristicas.py`             | Funciones heurísticas (`h_manhattan`, `h_euclidiana`, `h_octil`, `h_nula`) y `resolver_heuristica()`.     |
| `controllers/pioneer_TFM/planificacion/mapa.py`                    | Conversión mundo ↔ rejilla (`mundo_a_rejilla`, `celda_a_mundo`, `es_libre`) usada por la planificación.   |
| `controllers/pioneer_TFM/simulacion/menu_heuristica.py`            | Menú interactivo por teclado en la ventana 3D de Webots.                                                  |
| `controllers/pioneer_TFM/simulacion/robot_io.py`                   | Supervisor Webots: ruedas, pose, display de batería, paso de simulación.                                  |
| `controllers/pioneer_TFM/simulacion/seguimiento.py`                | Control proporcional simple para seguir `PUNTOS` (`decidir`, `seguir_camino`).                            |
| `controllers/pioneer_TFM/herramientas/mundo_a_grid.py`             | Genera PNG del mapa y la ruta planificada (ida, vuelta, combinado).                                       |
| `controllers/pioneer_TFM/herramientas/metricas.py`                 | Benchmark rápido en consola: A* por heurística y comparación de algoritmos.                               |
| `controllers/pioneer_TFM/herramientas/prueba_ara_astar.py`         | Script de prueba A* vs ARA* con tiempos e informe ARA*.                                                   |
| `controllers/pioneer_TFM/experimentos/datos_comparados.py`         | Comparativa offline de algoritmos/heurísticas; exporta `resultados_experimentos.csv`.                     |
| `controllers/pioneer_TFM/experimentos/resultados_experimentos.csv` | Resultados de la comparativa experimental (generado al ejecutar el script).                               |


**Importación del mapa:** `config.py` importa `cargar_mapa_desde_wbt` desde `herramientas/extract_wbt_to_json.py` (referenciado en el código). Esa función lee `worlds/pioneer3at.wbt` y actualiza `configuracion/generated_map.json`.



---

## 4. Configuración principal

Valores por defecto en `configuracion/config.py` (pueden sobrescribirse con `experimento.json` o el menú Webots):


| Variable                      | Valor por defecto          | Para qué sirve                                                        | Dónde se usa                                                                                                                         |
| ----------------------------- | -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `ALGORITMO`                   | `"ara_star"`               | Algoritmo de planificación activo.                                    | `menu_heuristica.elegir_configuracion()` → `config.ALGORITMO`; `planificar_mision()`, `_buscar_camino()` vía `resolver_algoritmo()`. |
| `HEURISTICA`                  | `"octil"`                  | Heurística para A*, Greedy y ARA*.                                    | Menú Webots → `config.HEURISTICA`; `resolver_heuristica()` en planificación.                                                         |
| `MODO_ARA`                    | `"anytime_simple"`         | Modo ARA*: `"offline"` o `"anytime_simple"`.                          | `menu_heuristica.elegir_modo_ara()`; `ara_star()` elige rama offline o anytime.                                                      |
| `EPSILON_INICIAL_ARA`         | `5`                        | Primer ε de ARA*.                                                     | `_epsilons_ara()` → lista decreciente de epsilon.                                                                                    |
| `EPSILON_FINAL_ARA`           | `1.0`                      | Último ε de ARA*.                                                     | `_epsilons_ara()`.                                                                                                                   |
| `EPSILON_PASO_ARA`            | `1`                        | Decremento de ε entre iteraciones.                                    | `_epsilons_ara()`.                                                                                                                   |
| `PASOS_POR_FASE_ARA`          | `5`                        | Celdas simuladas por fase en ARA* anytime.                            | `planificar_ara_anytime_simple()`; disparo de suelo cambiante en `pioneer_TFM.py`.                                                   |
| `PESO_ASTAR_PONDERADO`        | `1.5`                      | Peso por defecto de A* ponderado si no se pasa epsilon.               | `astar_ponderado()` cuando `peso_heuristica is None`.                                                                                |
| `COSTE_ZONA_1`                | `5`                        | Coste g de la zona azul (`COST_ZONE_1`).                              | `aplicar_costes_zonas()`, `coste_de_zona()`, display y mapas.                                                                        |
| `COSTE_ZONA_2`                | `5`                        | Coste g de la zona verde (`COST_ZONE_2`).                             | Igual que zona 1.                                                                                                                    |
| `COSTE_ZONA_3`                | `5`                        | Coste g de la zona amarilla (`COST_ZONE_3`).                          | Igual que zona 1.                                                                                                                    |
| `BATERIA_MAX`                 | `800`                      | Presupuesto de batería de la misión.                                  | `filtrar_objetivos_por_bateria()`, bucle de batería en `pioneer_TFM.py`.                                                             |
| `INICIO_MUNDO_POR_DEFECTO`    | `(-4.25, 10.25)`           | Inicio si el `.wbt` no trae `START`.                                  | `config_menu`; fallback antes de leer `START` del JSON.                                                                              |
| `OBJETIVOS_MUNDO_POR_DEFECTO` | `[(-4.25, 7.25)]`          | Objetivos si el `.wbt` no trae `goals`.                               | `config_menu`; fallback de objetivos.                                                                                                |
| `INICIO_MUNDO`                | Desde `.wbt` o por defecto | Posición inicial en metros (p. ej. `(-4.5, 9.75)`).                   | `colocar_inicio()`, conversión a `CELDA_INICIO`.                                                                                     |
| `OBJETIVOS_MUNDO`             | Desde `.wbt` o por defecto | Lista de objetivos en metros.                                         | `planificar_mision()`, `CELDAS_OBJETIVO`.                                                                                            |
| `GRID`                        | Matriz 48×48               | Estado del terreno para planificar.                                   | Todos los algoritmos vía `coste_base_celda()` y `es_libre()`.                                                                        |
| `CELDA_INICIO`                | Calculada al importar      | Celda `(fila, col)` del inicio.                                       | `planificar_mision()`, `pioneer_TFM.py`.                                                                                             |
| `CELDA_OBJETIVO`              | Calculada al importar      | Celda del primer objetivo.                                            | Planificación, validaciones.                                                                                                         |
| `CELDAS_OBJETIVO`             | Lista calculada            | Todas las celdas objetivo.                                            | `planificar_mision()`, `mundo_a_grid.py`.                                                                                            |
| `SUELO_CAMBIANTE`             | `False`                    | Si es `True`, los costes de zona 1 y 2 cambian una vez por ejecución. | `actualizar_suelo_cambiante_si_toca()`, menú consola, `pioneer_TFM.py`.                                                              |


Otras variables relevantes en `config.py`:


| Variable                       | Valor por defecto  | Para qué sirve                                        |
| ------------------------------ | ------------------ | ----------------------------------------------------- |
| `CELL_SIZE`                    | `0.5` (desde JSON) | Tamaño de celda en metros.                            |
| `MARGEN_SEGURIDAD`             | `0.3`              | Inflado de obstáculos hacia celdas libres adyacentes. |
| `USAR_FACTOR_DIAGONAL_BATERIA` | `False`            | Si es `True`, diagonales en batería consumen `×√2`.   |
| `LOG_BATERIA_CELDAS`           | `False`            | Log detallado por celda en consola.                   |
| `LOG_BATERIA_OBJETIVOS`        | `True`             | Aviso cuando un objetivo se descarta por batería.     |


---

## 5. Menú de configuración por consola

Archivo: `configuracion/config_menu.py`.

### Funciones auxiliares


| Función                               | Qué hace                                               |
| ------------------------------------- | ------------------------------------------------------ |
| `limpiar_terminal()`                  | Limpia la consola (Mac/Linux/Windows).                 |
| `imprimir_encabezado()`               | Muestra título del menú de experimento.                |
| `pedir_decimal(nombre, default)`      | Pide un número decimal; Intro mantiene el default.     |
| `pedir_entero(nombre, default)`       | Pide un entero; Intro mantiene el default.             |
| `_posicion_transitable(config, x, y)` | Comprueba que la celda no sea obstáculo (`GRID != 1`). |


### Flujo principal

1. `**pedir_configuracion(config_mod)`** — Pregunta interactivamente todos los parámetros y devuelve un diccionario `valores`.
2. `**guardar_en_archivo(valores)**` — Escribe `configuracion/experimento.json`.
3. `**cargar_desde_archivo(config)**` — Lee el JSON y llama a `aplicar_a_config()` **sin** `input()` (usado por Webots y `mundo_a_grid.py`).
4. `**aplicar_a_config(config, valores)`** — Copia los valores a las variables globales de `config` en memoria (no modifica `config.py` en disco):
  - `aplicar_costes_zonas()` para costes y `GRID`;
  - parámetros ARA*, batería, suelo cambiante;
  - inicio/objetivo (solo si la celda es transitable; si no, mantiene valores del `.wbt`);
  - recalcula `CELDA_INICIO`, `CELDA_OBJETIVO`, `CELDAS_OBJETIVO`.

### Ejecución del menú (fuera de Webots)

```bash
cd controllers/pioneer_TFM
python3 configuracion/config_menu.py
```

### Ejemplo de sesión

```text
COSTE_ZONA_1 / zona azul [5]: 2
COSTE_ZONA_2 / zona verde [5]: 20
COSTE_ZONA_3 / zona amarilla [5]: 5
PASOS_POR_FASE_ARA [5]: 3
PESO_ASTAR_PONDERADO [1.5]: 
EPSILON_INICIAL_ARA [5]: 
EPSILON_FINAL_ARA [1.0]: 
EPSILON_PASO_ARA [1]: 
BATERIA_MAX [800]: 
INICIO_MUNDO_X [-4.5]: 
INICIO_MUNDO_Y [9.75]: 
OBJETIVO_MUNDO_X [-3.75]: 
OBJETIVO_MUNDO_Y [7.15]: 
¿Suelo cambiante? S/N [N]: S
```

Si pulsas **Intro** en cualquier campo, se mantiene el valor entre corchetes.

**En Webots:** `pioneer_TFM.py` llama solo a `cargar_desde_archivo(config)`. Hay que generar `experimento.json` antes con el script anterior.

**Qué no configura el menú consola:** `ALGORITMO`, `HEURISTICA` y `MODO_ARA` se eligen en el menú por teclado de Webots (`menu_heuristica.py`).

---

## 6. Mapa, GRID y costes del terreno

### Carga del mapa

1. Al **importar** `config.py`, se ejecuta `cargar_mapa_desde_wbt(wbt_path=worlds/pioneer3at.wbt, json_path=generated_map.json)`.
2. El JSON contiene obstáculos, start, goals, `cost_zones`, límites y `cell_size`.
3. Se construye `_GRID_BASE` marcando celdas ocupadas por muros del `.wbt`.
4. `aplicar_margen_contorno()` expande obstáculos con `MARGEN_SEGURIDAD`.
5. El resultado es `**GRID`**.

### Significado de valores en `GRID`


| Valor | Significado                                           |
| ----- | ----------------------------------------------------- |
| `0`   | Celda libre (coste base de planificación = **1**).    |
| `1`   | Obstáculo o margen de seguridad (**no transitable**). |
| `> 1` | Zona de coste (el número es el coste g de esa celda). |


### Zonas de coste

En `pioneer3at.wbt` hay tres superficies:


| Nombre Webots | Color             | Variable config |
| ------------- | ----------------- | --------------- |
| `COST_ZONE_1` | Azul (arriba)     | `COSTE_ZONA_1`  |
| `COST_ZONE_2` | Verde (izquierda) | `COSTE_ZONA_2`  |
| `COST_ZONE_3` | Amarillo (centro) | `COSTE_ZONA_3`  |


Al construir `GRID`, para cada zona en `ZONAS_COSTE`:

```python
_coste = coste_de_zona(nombre)   # COST_ZONE_N → COSTE_ZONA_N
GRID[row][col] = _coste          # solo si la celda era libre (0)
```

### Funciones clave

`**coste_de_zona(nombre)**` — Devuelve `COSTE_ZONA_1/2/3` según el sufijo numérico de `COST_ZONE_N`; si no reconoce el nombre, devuelve `1.0`.

`**aplicar_costes_zonas(zona1, zona2, zona3)**` — Actualiza las variables globales `COSTE_ZONA_*` y **reescribe** todas las celdas registradas en `CELDAS_POR_ZONA`.

### Ejemplo didáctico

Si una celda pertenece a la zona azul y `COSTE_ZONA_1 = 5`:

1. Esa celda del `GRID` pasa a valer **5**.
2. `coste_base_celda(celda)` devuelve **5**.
3. `coste_movimiento(actual, vecino)` usa ese valor (× `√2` si el paso es diagonal).
4. ARA* / A* / Dijkstra leen el coste **desde `GRID`**, no necesitan conocer el color de la zona.

---

## 7. Algoritmos de planificación

Archivo: `planificacion/algoritmos.py`.

### Tabla de funciones principales


| Función                                                               | Qué hace                                                                     |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `dijkstra(inicio, objetivo, heuristica=None)`                         | Búsqueda con f(n)=g(n) usando heurística nula.                               |
| `greedy(inicio, objetivo, heuristica)`                                | Búsqueda con f(n)=h(n) (ignora coste acumulado).                             |
| `astar(inicio, objetivo, heuristica)`                                 | A* estándar: f(n)=g(n)+h(n).                                                 |
| `astar_ponderado(inicio, objetivo, heuristica, peso_heuristica=None)` | f(n)=g(n)+w·h(n). ARA* lo llama con w=ε.                                     |
| `_epsilons_ara(...)`                                                  | Genera la lista de epsilon decreciente desde `config`.                       |
| `planificar_ara_offline(...)`                                         | ARA* offline: calcula todas las rutas con ε decreciente; devuelve la última. |
| `planificar_ara_anytime_simple(...)`                                  | ARA* anytime: simula avance por fases y puede cambiar de ruta.               |
| `ara_star(...)`                                                       | Punto de entrada ARA*; elige offline o anytime según `config.MODO_ARA`.      |
| `preparar_ruta(inicio, objetivo, ...)`                                | Resuelve un tramo y convierte celdas a puntos mundo (`celda_a_mundo`).       |
| `planificar_mision(...)`                                              | Misión completa: filtra objetivos, planifica ida + vuelta, acumula nodos.    |
| `filtrar_objetivos_por_bateria(...)`                                  | Descarta objetivos si no hay batería suficiente (usa rutas simuladas).       |
| `aplanar_mision(rutas)`                                               | Une tramos en un único `CAMINO_CELDAS`.                                      |


Motor común: `**_buscar_camino()*`* (cola de prioridad, 8 direcciones incluidas diagonales).

### Ideas sencillas

- **A**: f(n) = g(n) + h(n), con g(n) = coste real acumulado y h(n) = estimación al objetivo.
- **A ponderado**: f(n) = g(n) + w·h(n). Con w>1 se expanden menos nodos pero la ruta puede dejar de ser óptima.
- **ARA**: repite A* ponderado reduciendo ε desde `EPSILON_INICIAL_ARA` hasta `EPSILON_FINAL_ARA`.
- **Modo `anytime_simple`**: entre iteraciones **simula** avanzar `PASOS_POR_FASE_ARA` celdas y recalcula desde la posición alcanzada.

**Limitación documentada en código:** esta ARA* **no implementa INCONS** ni reutilización interna de nodos; es una aproximación experimental.

---

## 8. Coste de celda, movimiento y batería

### Planificación (coste g)

```text
config.GRID[fila][col]
    ↓
coste_base_celda(celda)     # 0 → 1.0 ; >0 → valor del GRID
    ↓
coste_movimiento(actual, vecino)   # base, o base×√2 si diagonal
    ↓
coste_camino(camino)        # suma de movimientos consecutivos
```

### Batería

```text
config.GRID[fila][col]
    ↓
coste_base_celda(celda)
    ↓
coste_bateria_movimiento(actual, vecino)
    ↓
coste_bateria_camino(camino)
```

Planificación y batería comparten `**coste_base_celda()**`, que lee el mismo `GRID`. La diferencia está en si se aplica factor diagonal (`USAR_FACTOR_DIAGONAL_BATERIA`, por defecto `False`).

**Dónde se usa la batería:**

- `filtrar_objetivos_por_bateria()` — antes de planificar la misión.
- Bucle de `pioneer_TFM.py` — `coste_bateria_camino(CAMINO_CELDAS[:INDICE_OBJETIVO])` y `dibujar_bateria()`.

---

## 9. ARA* anytime simple

Función: `planificar_ara_anytime_simple()` en `planificacion/algoritmos.py`.

### Pasos

1. Obtiene la lista de epsilon con `_epsilons_ara()` (p. ej. 5, 4, 3, 2, 1).
2. Para cada fase `i` y cada `epsilon`:
  - Llama a `actualizar_suelo_cambiante_si_toca(i)` (solo actúa en fase `i=1` si `SUELO_CAMBIANTE=True`).
  - Calcula `nueva_ruta` con `astar_ponderado(..., peso_heuristica=epsilon)`.
  - Evalúa `nuevo_coste = coste_camino(nueva_ruta)`.
  - Actualiza `ruta_activa` si es la primera ruta, si cambió el suelo o si mejora el coste restante.
  - Registra la fase en `historial`.
  - Avanza `PASOS_POR_FASE_ARA` celdas sobre `ruta_activa` (`_avanzar_sobre_ruta`).
3. Si no llegó al objetivo, completa con `_completar_hasta_objetivo()`.
4. Devuelve `ruta_ejecutada`, `historial` y nodos totales.

### Ejemplo con epsilon paso 1

```text
Fase 0: ε = 5.0  →  calcula ruta inicial
         avanza PASOS_POR_FASE_ARA celdas

Fase 1: ε = 4.0  →  (si SUELO_CAMBIANTE) cambia costes de zona
         recalcula desde la posición alcanzada

Fase 2: ε = 3.0  →  recalcula de nuevo
...
Fase 4: ε = 1.0  →  última recalculación (equivalente a A* ponderado con ε=1)
```

El informe queda en `ULTIMO_INFORME_ARA` y, en misiones, en la lista global `INFORME_ARA_MISION`.

---

## 10. Suelo cambiante

Variable: `**SUELO_CAMBIANTE**` en `config.py` / `experimento.json`.

### Qué activa

Si `SUELO_CAMBIANTE = True`, la función `**actualizar_suelo_cambiante_si_toca(indice_fase)**` puede ejecutarse **una sola vez** por ejecución (flag `_SUELO_CAMBIANTE_APLICADO`).

### Cuándo cambia

Solo cuando `**indice_fase == 1`** (segunda fase de ARA* anytime, es decir, la iteración con el segundo epsilon).

### Qué zonas cambian

```text
COSTE_ZONA_1  ←  × 5
COSTE_ZONA_2  ←  ÷ 5
COSTE_ZONA_3  ←  sin cambio
```

Luego se llama a `config.aplicar_costes_zonas(...)`, que actualiza `**GRID**`.

### Valores no válidos (fallback a 1.0)

La función `_coste_suelo_cambiante()` valida el resultado de cada zona. Si la operación falla (`ZeroDivisionError`, `TypeError`, `ValueError`), el resultado no es finito o es ≤ 0, o bien la zona 2 queda con coste &lt; 1 tras dividir entre 5, se usa **coste 1.0** (igual que una celda libre).

En consola aparece un aviso **antes** del bloque `SUELO CAMBIANTE ACTIVADO`:

```text
AVISO suelo cambiante: COSTE_ZONA_2 (1.0 /5) no valido; se usa coste 1.0

=============================================
SUELO CAMBIANTE ACTIVADO
=============================================
COSTE_ZONA_1 x5 = 5.0
COSTE_ZONA_2 /5 = 1.0
COSTE_ZONA_3    = 1.0
=============================================
```

Ejemplo: con costes iniciales `1 / 1 / 1`, la zona 1 pasa a `5`, la zona 2 no baja de `1` (en lugar de `0.2`) y la zona 3 se mantiene en `1`.

### Dónde ocurre en el proyecto


| Momento                         | Archivo                           | Comportamiento                                                                                                                                |
| ------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Planificación ARA* anytime      | `planificar_ara_anytime_simple()` | Suelo cambia en fase 1 de cada tramo (ida/vuelta).                                                                                            |
| Antes de planificar misión real | `planificar_mision()`             | Restaura costes iniciales tras el filtro de batería.                                                                                          |
| Simulación Webots               | `pioneer_TFM.py`                  | Tras planificar, `reiniciar_suelo_cambiante()` deja costes iniciales; al recorrer ≥ `PASOS_POR_FASE_ARA` celdas vuelve a activarse el cambio. |


### Por qué no hay que tocar `_buscar_camino` ni `coste_movimiento`

Esas funciones ya leen el coste desde `**config.GRID*`* vía `coste_base_celda()`. Cuando cambia el GRID, la planificación usa automáticamente el nuevo suelo.

---

## 11. Estado del sistema

No existe una clase `Estado` global. El estado se reparte en estructuras concretas.

### Estado del robot

Función `**leer_estado()**` en `simulacion/robot_io.py` (llamada en el bucle de `pioneer_TFM.py`):


| Campo         | Significado                           |
| ------------- | ------------------------------------- |
| `x`, `y`      | Posición real del robot (supervisor). |
| `orientacion` | Ángulo yaw (rad).                     |
| `tiempo_s`    | Tiempo de simulación Webots.          |


### Estado del entorno


| Elemento       | Dónde vive                                                             |
| -------------- | ---------------------------------------------------------------------- |
| `GRID`         | `config.GRID` — costes y obstáculos.                                   |
| Costes de zona | `COSTE_ZONA_1/2/3` + celdas en `CELDAS_POR_ZONA`.                      |
| Obstáculos     | Valor `1` en `GRID`; geometría en `OBSTACULOS` / `generated_map.json`. |
| Objetivos      | `OBJETIVOS_MUNDO`, `CELDAS_OBJETIVO`.                                  |


### Estado de ARA*

Historial por fases en `**ULTIMO_INFORME_ARA*`* / `**INFORME_ARA_MISION**`. Cada entrada del modo `anytime_simple` puede contener:


| Campo               | Significado                                                        |
| ------------------- | ------------------------------------------------------------------ |
| `epsilon`           | Valor de ε en esa fase.                                            |
| `inicio_fase`       | Celda desde la que se recalculó.                                   |
| `ruta_calculada`    | Ruta devuelta por A* ponderado.                                    |
| `coste`             | `coste_camino(ruta_calculada)`.                                    |
| `nodos`             | Nodos expandidos en esa fase.                                      |
| `accion`            | p. ej. `"ruta inicial"`, `"ruta actualizada por cambio de suelo"`. |
| `costes_suelo`      | Tupla `(COSTE_ZONA_1, COSTE_ZONA_2, COSTE_ZONA_3)` en ese momento. |
| `suelo_actualizado` | `True` si en esa fase se aplicó suelo cambiante.                   |


---

## 12. Visualización y mapas PNG

Script: `**herramientas/mundo_a_grid.py*`*.

### Mapas que genera


| Archivo                        | Contenido                                       |
| ------------------------------ | ----------------------------------------------- |
| `map_ida.png`                  | Ruta de ida (inicio → objetivo).                |
| `map_vuelta.png`               | Ruta de vuelta a base.                          |
| `map_ida_vuelta.png`           | Ida y vuelta superpuestas.                      |
| `map_visualization_simple.png` | Copia de `map_ida_vuelta.png` (compatibilidad). |


### Cuándo se generan

Solo al ejecutar **manualmente**:

```bash
cd controllers/pioneer_TFM
python3 herramientas/mundo_a_grid.py
```

El script:

1. Carga `experimento.json` (`config_menu.cargar_desde_archivo`).
2. Ejecuta `planificar_mision()` con la configuración activa.
3. Guarda los PNG en `herramientas/`.

**Webots no regenera PNG** durante la simulación.

### GRID real vs color visual

- El **GRID** usado para planificar puede cambiar (p. ej. suelo cambiante → nuevos costes en celdas).
- Los **colores** de zona en el PNG vienen del `.wbt` (`COLORES_ZONA_MUNDO`); la leyenda muestra el coste g **actual del GRID** tras planificar.
- Cambiar costes no cambia la geometría ni el color del `.wbt`; solo cambia el valor numérico en `GRID`.

---

## 13. Ejemplo de ejecución didáctico

### Configuración de ejemplo

```text
COSTE_ZONA_1 = 2
COSTE_ZONA_2 = 20
COSTE_ZONA_3 = 5
PASOS_POR_FASE_ARA = 3
SUELO_CAMBIANTE = S
ALGORITMO = ara_star
MODO_ARA = anytime_simple
```

### Costes al inicio


| Zona              | Coste g |
| ----------------- | ------- |
| Azul (zona 1)     | 2       |
| Verde (zona 2)    | 20      |
| Amarilla (zona 3) | 5       |


### Tras el cambio de suelo (fase 1 de ARA*)


| Zona     | Coste g        |
| -------- | -------------- |
| Azul     | 2 × 5 = **10** |
| Verde    | 20 ÷ 5 = **4** |
| Amarilla | **5** (igual)  |


### Qué debería ocurrir

1. **Fase 0** (ε alto): ARA* planifica con el GRID inicial (2 / 20 / 5).
2. **Fase 1**: se activa suelo cambiante → `aplicar_costes_zonas()` → GRID pasa a (10 / 4 / 5).
3. ARA* **recalcula** desde la posición simulada con el nuevo GRID.
4. Si la ruta evitaba la zona verde antes y ahora es más barata, la trayectoria puede cambiar.
5. En Webots, el display `Z:...` y la línea de zona reflejan los costes activos tras el cambio en simulación.

---

## 14. Resumen final

- El proyecto representa el entorno con un `**GRID*`* numérico: obstáculos, celdas libres y costes de zona.
- Los algoritmos **no necesitan conocer internamente** el nombre ni el color de cada zona; solo leen `**coste_base_celda()` → `GRID[celda]`**.
- **ARA**, **A**, **Dijkstra** y **Greedy** comparten el mismo motor de búsqueda y el mismo modelo de coste de movimiento.
- Cuando cambia el **GRID** (manualmente, por `aplicar_costes_zonas` o por **suelo cambiante**), cambia el coste de planificación y de batería.
- Cuando *ARA recalcula** (modo anytime o nuevo epsilon), usa el **estado actual del entorno** leyendo el GRID en ese momento.

---

## Cómo ejecutar

### Simulación en Webots

1. Abrir `worlds/pioneer3at.wbt`.
2. (Opcional) Configurar experimento: `python3 controllers/pioneer_TFM/configuracion/config_menu.py`
3. Ejecutar simulación; elegir algoritmo (1–4), heurística (1–3) y, si ARA*, modo (1 offline / 2 anytime).

### Scripts útiles

```bash
# Mapas PNG
python3 controllers/pioneer_TFM/herramientas/mundo_a_grid.py

# Comparativa experimental → CSV
python3 controllers/pioneer_TFM/experimentos/datos_comparados.py

# Benchmark rápido
python3 controllers/pioneer_TFM/herramientas/metricas.py

# Prueba A* vs ARA*
python3 controllers/pioneer_TFM/herramientas/prueba_ara_astar.py
```

### Requisitos

- Webots (probado con R2025a según el `.wbt`)
- Python 3
- `matplotlib` y `numpy` (solo para `mundo_a_grid.py`)

