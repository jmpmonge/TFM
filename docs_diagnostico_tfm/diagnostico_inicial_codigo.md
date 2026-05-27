# Diagnóstico inicial del código del TFM

**Proyecto:** Búsqueda heurística aplicada a la planificación de rutas  
**Entorno:** Pioneer 3-AT en Webots  
**Fecha del análisis:** mayo 2026  
**Alcance:** lectura del repositorio actual, sin modificación de código fuente.

---

## 1. Estructura actual del proyecto

### Raíz del repositorio

| Elemento | Función aparente |
|----------|------------------|
| `README.md` | Documentación general: objetivos, estructura, ejecución, comparativa experimental. |
| `.gitignore` | Exclusiones de control de versiones. |
| `subir_a_github.txt` | Notas auxiliares para publicación (no es código ejecutable). |
| `worlds/pioneer3at.wbt` | Mundo Webots: arena, obstáculos, objetivos, robot Pioneer 3-AT. |
| `worlds/.pioneer3at.wbproj` | Metadatos de interfaz de Webots (perspectivas, paneles); no afecta la lógica del TFM. |

### Controlador `controllers/pioneer_TFM/`

| Elemento | Función aparente |
|----------|------------------|
| **`pioneer_TFM.py`** | **Punto de entrada principal** exigido por Webots. Orquesta menú, planificación, colocación del robot y bucle de simulación. |
| `planificacion/algoritmos.py` | Núcleo de búsqueda: Dijkstra, A*, Greedy, misión multiobjetivo, batería. |
| `planificacion/heuristicas.py` | Definición y resolución de heurísticas (`nula`, `manhattan`, `euclidiana`). |
| `planificacion/mapa.py` | Consulta del grid (`es_libre`), conversión celda ↔ mundo. |
| `planificacion/__init__.py` | Paquete vacío (marcador de módulo). |
| `configuracion/config.py` | Parámetros, lectura de JSON, construcción de `GRID`, celdas de inicio/objetivo. |
| `configuracion/generated_map.json` | Mapa derivado del `.wbt`: límites, obstáculos, goals. |
| `configuracion/__init__.py` | Paquete vacío. |
| `simulacion/robot_io.py` | Supervisor Webots: ruedas, pose, display de batería, paso de simulación. |
| `simulacion/seguimiento.py` | Control proporcional para seguir waypoints de la ruta planificada. |
| `simulacion/menu_heuristica.py` | Menú por teclado para elegir algoritmo y heurística al arrancar. |
| `simulacion/__init__.py` | Paquete vacío. |
| `experimentos/datos_comparados.py` | Script ejecutable offline: comparativa sistemática y exportación CSV. |
| `experimentos/resultados_experimentos.csv` | Salida de la última ejecución de `datos_comparados.py`. |
| `experimentos/__init__.py` | Paquete vacío. |
| `herramientas/extract_wbt_to_json.py` | Extrae obstáculos y goals del `.wbt` hacia `generated_map.json`. |
| `herramientas/dump_map_simple.py` | Visualización estática de la rejilla y la misión (PNG). |
| `herramientas/metricas.py` | Benchmark rápido en consola (un solo par inicio→objetivo). |
| `herramientas/map_visualization_simple.png` | Imagen generada por `dump_map_simple.py`. |

**Nota:** el `README.md` menciona `herramientas/dump_map.py`, pero **ese archivo no está presente** en el repositorio actual; solo existe `dump_map_simple.py`.

### Punto de entrada principal

- **En Webots:** `controllers/pioneer_TFM/pioneer_TFM.py` (nombre obligatorio: carpeta del controlador = nombre del script).
- **No existe `main.py`** en la raíz ni en el controlador.
- **Scripts offline con `if __name__ == "__main__"`:** `experimentos/datos_comparados.py`, `herramientas/extract_wbt_to_json.py`, `herramientas/dump_map_simple.py`, `herramientas/metricas.py` (este último ejecuta código al importar, sin bloque `main` explícito).

---

## 2. Representación del mapa, grid o grafo

### Dónde se define el mapa

1. **Fuente geométrica:** `worlds/pioneer3at.wbt` (obstáculos como sólidos `DEF OBSTACLE_*`, goals como `DEF GOAL_*`).
2. **Intermedio:** `configuracion/generated_map.json` (generado por `herramientas/extract_wbt_to_json.py`).
3. **Representación de planificación:** matriz `GRID` en `configuracion/config.py`, construida al importar el módulo.

### Tipo de representación

- **No hay grafo explícito** (no se usa `networkx` ni listas de adyacencia materializadas).
- **Sí hay grid (matriz 2D):** `GRID[fila][col]` con valores booleanos (`True` = libre, `False` = bloqueado).
- El grafo es **implícito:** cada celda libre es un nodo; las aristas se generan al expandir vecinos en `_vecinos()`.

### Nodos

- Un nodo es una **tupla `(fila, col)`** (índices enteros en la rejilla).
- El centro físico de la celda se obtiene con `centro_celda(row, col)` o `celda_a_mundo(celda)` en coordenadas del mundo (metros).

### Obstáculos

- **Paredes:** borde exterior de `GRID` marcado como `False`.
- **Cilindros del mundo:** para cada celda se calcula el centro en metros y se compara la distancia euclídea a cada obstáculo del JSON. Si `dist <= RADIO_OBSTACULO + MARGEN_SEGURIDAD`, la celda queda bloqueada.
- El radio del obstáculo viene de `generated_map.json` (`obstacle_radius`, típicamente 0.4 m). El margen de seguridad está en `config.py` (`MARGEN_SEGURIDAD = 0.6`).

### Vecinos

- Función `_vecinos(celda)` en `planificacion/algoritmos.py`.
- Constante `MOVIMIENTOS = [(-1, 0), (1, 0), (0, -1), (0, 1)]`.
- **Solo 4 direcciones** (norte, sur, este, oeste). **No hay movimiento diagonal (8-conectividad).**
- Un vecino es válido si `es_libre(fila, col)` en `planificacion/mapa.py` devuelve `True`.

### Conversión Webots ↔ grid

| Función | Ubicación | Dirección |
|---------|-----------|-----------|
| `mundo_a_rejilla(x, y)` | `config.py` y `mapa.py` (duplicada) | Metros → `(row, col)` con `int((coord - ORIGEN) / CELL_SIZE)` y clampeo a límites. |
| `centro_celda(row, col)` | `config.py` y `mapa.py` | Celda → centro en metros (`+ CENTRO_CELDA`). |
| `celda_a_mundo(celda)` | `mapa.py` | Celda → centro en metros (misma fórmula que `centro_celda`). |

`ORIGEN_MAPA_X/Y` y `CELL_SIZE` (0.17 m) definen la discretización. La rejilla resultante es del orden de **352×352** celdas para un mapa de 60×60 m.

---

## 3. Coste de movimiento

### Dónde se calcula

- En `_buscar_camino()` (`planificacion/algoritmos.py`), línea conceptual: `nuevo_coste = coste[actual] + 1` por cada paso a un vecino.

### Naturaleza del coste

| Tipo | ¿Presente? | Detalle |
|------|------------|---------|
| Coste uniforme por paso | **Sí** | Cada arista vale **1** (un paso de grid 4-conectado). |
| Distancia euclídea real entre celdas | No | Solo se usa en la heurística, no en g(n). |
| Pendiente / rugosidad / terreno variable | **No** | Todas las celdas libres cuestan igual. |
| Energía como g(n) | **No** | No hay coste energético en la búsqueda. |
| Penalización por zona difícil | **No** | |
| Batería en g(n) | **No** | La batería no modifica el coste de cada arista. |
| Retorno a base | **No como coste de arista** | La vuelta a base es un **tramo más** de la misión (`planificar_mision` planifica hasta `base` al final). |

### Separación g(n) / h(n)

- **g(n):** diccionario `coste` en `_buscar_camino`, acumula +1 por paso. Correctamente separado del resto.
- **h(n):** función pasada como parámetro `heuristica(inicio, objetivo)` o `heuristica(vecino, objetivo)`.
- **Batería (`filtrar_objetivos_por_bateria`):** usa `h_manhattan` como **estimación de distancia en pasos** para decidir cuántos objetivos caben en `BATERIA_MAX`. **No es g(n) del algoritmo de búsqueda** ni h(n) admisible hacia el goal; es una capa de planificación de misión aparte.
- **Display de batería en simulación:** en `pioneer_TFM.py` se decrementa de forma simplificada según el índice del waypoint (`BATERIA_MAX - (INDICE_OBJETIVO - 1)`), no según distancia real recorrida.

---

## 4. Algoritmos implementados

Todos comparten el núcleo `_buscar_camino()` en `planificacion/algoritmos.py`.

### Tabla resumen

| Algoritmo | Función | Parámetros | Devuelve | Reconstruye ruta | Coste total | Nodos expandidos | Tiempo | Guarda resultados |
|-----------|---------|------------|----------|------------------|-------------|------------------|--------|-------------------|
| **Dijkstra** | `dijkstra(inicio, objetivo, heuristica=None)` | Celda inicio, celda objetivo; heurística ignorada | `(camino: list[(f,c)], nodos_explorados: int)` | Sí (`_reconstruir_camino`) | Implícito en longitud del camino; no se devuelve como campo separado | Sí (cuenta al hacer `heappop`) | No internamente | Solo vía scripts externos |
| **A\*** | `astar(inicio, objetivo, heuristica)` | + función heurística | Igual | Sí | Igual | Sí | No | Igual |
| **Greedy** | `greedy(inicio, objetivo, heuristica)` | + función heurística | Igual | Sí | Igual | Sí | No | Igual |

### Funciones de planificación de alto nivel

| Función | Rol |
|---------|-----|
| `preparar_ruta(inicio, objetivo, heuristica, algoritmo=None)` | Un tramo; devuelve celdas, puntos mundo, índice y nodos. |
| `planificar_mision(origen, objetivos, base, bateria, ...)` | Misión completa: filtra objetivos, planifica tramos, vuelta a base. |
| `aplanar_mision(rutas)` | Une tramos en un solo camino. |
| `filtrar_objetivos_por_bateria(...)` | Selección de subconjunto de goals por presupuesto. |

### Uso de g(n), h(n) y f(n) en `_buscar_camino`

- **Cola de prioridad:** tupla `(prioridad, coste_actual, nodo)`.
- Si `usar_coste=True` (A*, Dijkstra): `prioridad = g + h` con `g = coste[vecino]`.
- Si `usar_coste=False` (Greedy): `prioridad = h` únicamente.
- **Nodos repetidos:** si al sacar de la cola `coste_actual != coste[nodo]`, se descarta (implementación estándar con re-inserciones).
- **No hay conjunto cerrado explícito**; la poda se basa en mejorar `coste[vecino]`.

---

## 5. Revisión específica de Dijkstra

### Implementación

- Función dedicada `dijkstra()` que llama a `_buscar_camino(..., usar_coste=True, heuristica=h_nula)`.
- **`h_nula` siempre devuelve 0**, por lo que `prioridad = g + 0 = g`.
- **Conceptualmente es A\* con heurística nula**, no un algoritmo Dijkstra separado con cola solo por `g`. En grids con costes uniformes positivos el comportamiento es equivalente al Dijkstra clásico.

### ¿Usa solo g(n)?

- **Sí en la práctica**, porque h=0.

### Posibles problemas conceptuales

1. **Nomenclatura:** se expone como "Dijkstra" pero internamente es el mismo motor que A\*.
2. **Comparativa experimental:** Dijkstra, A\*+nula y Greedy+nula producen los **mismos nodos expandidos** en el CSV (133067 en la última ejecución registrada), coherente con h=0 en ambos modos de coste para Greedy vs A\*+nula (Greedy con h=0 también ordena por 0 constante → degeneración).
3. El parámetro `heuristica` de `dijkstra()` existe por uniformidad de API pero **se ignora**.

---

## 6. Revisión específica de A*

### Implementación

- `astar()` → `_buscar_camino(..., usar_coste=True, heuristica=heuristica)`.
- **f(n) = g(n) + h(n)** con g acumulado en pasos unitarios.

### Heurística

- **Configurable** vía argumento `heuristica` (función) y vía `config.HEURISTICA` / menú de teclado.
- Opciones en código: `h_nula`, `h_manhattan`, `h_euclidiana`.

### Gestión de nodos repetidos y camino

- Mejora de camino si `nuevo_coste < coste[vecino]`: correcto para costes uniformes.
- Reconstrucción con `viene_de` y `_reconstruir_camino`: correcta.
- **Manhattan es admisible** con movimiento 4-conectado y coste 1 → A\*+Manhattan encuentra camino óptimo en cada tramo (confirmado en CSV: coste 580, referencia "igual").
- **Euclidiana** puede ser admisible con coste 1 en 4-dir (h_eucl ≤ h_manhattan en muchos casos, pero no garantizado estrictamente en todos los casos de grid; en la práctica aquí también da coste óptimo 580).

---

## 7. Revisión específica de Greedy

### ¿Existe?

- **Sí:** función `greedy()` en `planificacion/algoritmos.py`.

### ¿Usa f(n) = h(n)?

- **Sí:** `usar_coste=False` → `prioridad = h` sin sumar g.
- Es **búsqueda voraz (Greedy Best-First)**, no Uniform Cost Search.

### Comportamiento observado (CSV)

- Greedy + Manhattan: **590 pasos** (+10 respecto a óptimo), **598 nodos** expandidos (muy rápido).
- Greedy + Euclidiana: **586 pasos** (+6), **589 nodos**.
- Greedy + nula: degenera (misma expansión masiva que Dijkstra/A\*+nula).

### Si no existiera (referencia conceptual)

No aplica; ya está. Para ampliar el TFM conceptualmente se podría documentar que Greedy **no garantiza optimalidad** y analizar el trade-off nodos/tiempo vs coste, como ya muestran los datos.

---

## 8. Revisión específica de A* ponderado

### ¿Existe?

- **No.** No hay función `astar_ponderado`, `weighted_astar`, ni parámetro `w` en el código actual.
- Búsqueda en el repositorio: sin referencias a `weighted`, `ponderad`, `w * h`, etc.

### Qué habría que añadir (solo a nivel conceptual)

1. Variante de `_buscar_camino` o función nueva con `prioridad = g(n) + w * h(n)`.
2. Parámetro `w >= 1` configurable (archivo de config o menú).
3. Entrada en `ALGORITMOS_DISPONIBLES` y en el menú de teclado.
4. Filas nuevas en `datos_comparados.py` para medir el efecto de `w` en nodos expandidos vs suboptimalidad.
5. Discusión en memoria: `w > 1` relaja admisibilidad → caminos más rápidos de encontrar pero no necesariamente óptimos.

---

## 9. Heurísticas existentes

**Archivo:** `planificacion/heuristicas.py`

| Heurística | Clave | Fórmula | ¿Presente? |
|------------|-------|---------|------------|
| Nula | `nula` | `0` | Sí |
| Manhattan | `manhattan` | `\|Δfila\| + \|Δcol\|` | Sí |
| Euclidiana | `euclidiana` | `√(Δfila² + Δcol²)` | Sí |
| Chebyshev | — | — | **No** |
| Energía | — | — | **No** |
| Ponderada (w·h) | — | — | **No** |
| Otras | — | — | **No** |

### Selector

- `HEURISTICAS_DISPONIBLES`: diccionario clave → función.
- `resolver_heuristica(nombre=None)`: devuelve la función según `config.HEURISTICA` o nombre explícito.

### Mezcla indebida g/h

- Las heurísticas en `heuristicas.py` **solo dependen de coordenadas de celdas**, no del coste acumulado. **No mezclan g(n) con h(n).**
- **Excepción conceptual:** `filtrar_objetivos_por_bateria` reutiliza `h_manhattan` como proxy de **coste de misión**, pero eso ocurre **antes** de la búsqueda por tramos, no dentro de la función heurística del A\*.

### Inconsistencia documental

- Comentario en `config.py` línea 25: menciona `"cero"` y `"agresiva"` como opciones de `HEURISTICA`, pero las claves reales son `"nula"`, `"manhattan"`, `"euclidiana"`.

---

## 10. Evaluación y métricas

### Módulos de evaluación

| Módulo | Tipo | Alcance |
|--------|------|---------|
| `experimentos/datos_comparados.py` | Comparativa formal | Misión completa multiobjetivo |
| `herramientas/metricas.py` | Benchmark ligero | Un solo par `CELDA_INICIO` → `CELDA_OBJETIVO` |
| `pioneer_TFM.py` | Impresión en consola al simular | Algoritmo, heurística, longitud en celdas, nodos totales |

### Métricas registradas

| Métrica | datos_comparados | metricas.py | pioneer_TFM (sim) |
|---------|------------------|-------------|-------------------|
| Algoritmo usado | Sí | Sí (parcial) | Sí (print) |
| Heurística usada | Sí | Parcial (solo bloque A\*) | Sí (print) |
| Inicio | Implícito (`CELDA_INICIO`) | Sí | Sí (mundo) |
| Objetivo(s) | Subconjunto filtrado por batería | Solo primer objetivo | Sí (lista mundo) |
| Ruta (celdas) | No (solo coste en pasos) | Sí (`longitud`) | Sí (`len(CAMINO_CELDAS)`) |
| Coste total (pasos) | Sí | No explícito | No |
| Nodos expandidos | Sí | Sí | Sí |
| Tiempo ejecución | Sí | Sí | No |
| Éxito/fracaso | No explícito (camino vacío → coste 0) | No | No |
| Diferencia vs A\*+Manhattan | Sí | No | No |
| Eficiencia coste/nodos | Sí | No | No |
| Factor expansión | Sí | No | No |
| Consumo energético real | No | No | No |
| Batería restante | No en CSV | No | Aproximación visual en display |

### Formatos de salida

- **CSV:** `experimentos/resultados_experimentos.csv` (8 columnas de datos + cabecera).
- **Consola:** tablas en `datos_comparados.py` y líneas en `metricas.py`.
- **JSON:** solo como entrada de mapa (`generated_map.json`), no como salida de experimentos.
- **PNG:** visualización de mapa (`map_visualization_simple.png`).

---

## 11. Relación con Webots

### ¿Controlador Webots?

- **Sí.** `pioneer_TFM.py` se ejecuta como controlador; `robot_io.py` instancia `Supervisor`.
- En `pioneer3at.wbt`: `DEF PIONEER_3AT Pioneer3at` con `controller "pioneer_TFM"`.

### Archivos world / configuración

- `worlds/pioneer3at.wbt` — mundo principal.
- `worlds/.pioneer3at.wbproj` — preferencias de IDE Webots.
- `configuracion/generated_map.json` — puente offline entre `.wbt` y Python.

### Pioneer 3-AT

- Presente en el mundo y referenciado por `DEF "PIONEER_3AT"` en `robot_io.py`.

### ¿Solo planifica o también mueve?

- **Ambas cosas:** planifica offline al inicio del script; luego en el bucle `while paso()` aplica velocidades a las ruedas siguiendo waypoints (`seguimiento.py`).

### Sensores

- **No se usan sensores** (lidar, cámara, GPS del robot) en el código del controlador para la planificación.
- La pose se lee del **supervisor** (`getPosition`, `getOrientation`), no de navegación reactiva basada en percepción.
- El mapa se considera **conocido a priori** vía `GRID` construido desde JSON.

---

## 12. main.py o punto de entrada

### No hay `main.py`

El rol de "main" lo cumplen:

1. **`pioneer_TFM.py`** (simulación Webots).
2. **`experimentos/datos_comparados.py`** (experimentación batch).
3. Scripts auxiliares en `herramientas/`.

### Qué hace `pioneer_TFM.py` actualmente

1. Al importar `simulacion.menu_heuristica`, se ejecuta **`elegir_configuracion()`** (menú por teclado en Webots).
2. Convierte objetivos mundo → celdas.
3. Llama a **`planificar_mision(..., devolver_nodos=True)`** con algoritmo/heurística ya elegidos en `config`.
4. Aplana rutas, convierte a puntos mundo, coloca el robot.
5. Imprime resumen (algoritmo, heurística, inicio, objetivos, celdas, nodos).
6. Bucle de simulación: leer estado → `decidir` → velocidades → batería en display.

### Elección de algoritmo y heurística

- **Sí**, vía teclado en Webots (`menu_heuristica.py`): teclas 1–3 para algoritmo; heurística según algoritmo.

### Comparación automática

- **No** en el controlador. La comparación sistemática está en `datos_comparados.py` (ejecución manual fuera de Webots).

### Guardado de resultados en simulación

- **No** guarda CSV ni logs estructurados; solo `print` por consola de Webots.

### Conexión con Webots

- **Total** para ejecución en tiempo real; depende de `controller.Supervisor` y del mundo cargado.

---

## 13. Problemas detectados

### 13.1 Problemas conceptuales

1. **A\* ponderado ausente** respecto al alcance declarado del TFM.
2. **Dijkstra = A\* + h nula** en un único motor; correcto pero conviene documentarlo para la memoria.
3. **Greedy con heurística nula** no tiene sentido práctico (prioridad constante).
4. **Sin costes de terreno variables**; toda la comparación es sobre topología y heurística, no sobre rugosidad/energía.
5. **Batería** usada como filtro de misión con Manhattan, no integrada en g(n); la barra de batería en simulación es **heurística de visualización**, no modelo energético.
6. **Orden de objetivos** fijado por cercanía Manhattan antes de planificar; no se compara con otros órdenes (TSP simplificado).

### 13.2 Problemas de organización

1. **Duplicación** de `mundo_a_rejilla` / `centro_celda` en `config.py` y `mapa.py` (motivo histórico: evitar import circular).
2. **`README` desactualizado** respecto a `dump_map.py` (no existe).
3. **`metricas.py`** ejecuta experimentos al importar el archivo, sin `if __name__ == "__main__"`.
4. **`herramientas/` vs `experimentos/`:** dos scripts de medición con roles solapados (`metricas.py` vs `datos_comparados.py`).
5. Comentarios en `config.py` (`HEURISTICA`: "cero", "agresiva") no coinciden con claves reales.

### 13.3 Problemas de métricas

1. **CSV no guarda** inicio/objetivo explícitos, ni identificador de ejecución/fecha.
2. **Éxito/fracaso** no codificado (solo inferible si coste=0).
3. **`metricas.py`** usa un solo objetivo (`CELDA_OBJETIVO`) mientras la misión real es multiobjetivo.
4. **Simulación** no persiste métricas; solo la comparativa offline genera CSV reproducible.
5. Greedy con heurística "Nula" en `datos_comparados.py` aparece en pruebas de A\* y Greedy pero es **degenerada** (misma fila que Dijkstra).

### 13.4 Problemas de extensibilidad

1. Añadir A\* ponderado requiere tocar `_buscar_camino` o crear rama nueva y registrar en `ALGORITMOS_DISPONIBLES`, menú y `datos_comparados.py`.
2. Añadir heurística nueva: `heuristicas.py` + menú + pruebas en comparativa.
3. **8-conectividad** o costes por celda exigirían cambiar `MOVIMIENTOS`, `nuevo_coste` y posiblemente admisibilidad de h.
4. No hay interfaz unificada de "experimento" (config JSON de batería de pruebas).

### 13.5 Problemas de integración con Webots

1. **`robot_io` no se puede importar** fuera de Webots (falla sin módulo `controller`); `menu_heuristica` depende de supervisor → el menú solo funciona dentro de Webots.
2. Orden de imports: el menú se ejecuta al importar `menu_heuristica`, **antes** de que terminen otros imports en `pioneer_TFM.py` (funciona, pero es frágil).
3. Warnings históricos de `maxVelocity` mitigados con saturación en `robot_io.py` (estado actual razonable).

### 13.6 Problemas de nomenclatura o claridad

1. `mundo_a_rejilla` vs nombres anteriores `mundo_a_celda` en documentación externa.
2. `RUEDAS` en `config.py` parece ser el radio de rueda (typo semántico: debería ser `RADIO_RUEDA`).
3. "Nodos expandidos" cuenta **extracciones de la cola abierta**, no inserciones ni generaciones de vecinos.
4. `OBSTACLE_RADIUS` en `config.py` vs `RADIO_OBSTACULO` del JSON (duplicidad de fuentes de verdad).

---

## 14. Recomendación de siguiente paso

### Primer archivo a tocar (cuando se autorice implementación)

**`planificacion/algoritmos.py`**

### Por qué

- Es el **núcleo único** de todos los algoritmos actuales.
- Cualquier A\* ponderado, coste variable o ajuste fino de conteo de nodos pasa necesariamente por `_buscar_camino`.
- Los demás módulos (`datos_comparados.py`, menú, `pioneer_TFM.py`) ya consumen esta API; un cambio bien acotado aquí se propaga con poco riesgo.

### Objetivo del primer cambio

1. Añadir **A\* ponderado** como cuarta variante (`f = g + w·h`) con `w` configurable.
2. Registrar la variante en `ALGORITMOS_DISPONIBLES` y documentar en memoria la relación Dijkstra / A\* / Greedy / WA\*.
3. Opcional en la misma fase: parámetro `w` en `config.py` sin tocar aún Webots.

### Qué NO tocar todavía

- `worlds/pioneer3at.wbt` (geometría del mundo).
- `simulacion/seguimiento.py` (no es planificación).
- Refactor masivo de carpetas o unificación de `config`/`mapa` (mejora organizativa, no bloqueante para el objetivo experimental).
- Integración de sensores o SLAM (fuera del alcance de esta fase).
- Sustitución por `networkx` (se descartó previamente por control de métricas).

### Segundo paso natural (después)

**`experimentos/datos_comparados.py`**: añadir filas para A\* ponderado con varios valores de `w`, regenerar CSV para la memoria del TFM.

---

## 15. Resumen ejecutivo final

### Estado general

El proyecto **ya constituye una base funcional sólida** para un TFM de planificación en grid conocido: tres algoritmos clásicos, tres heurísticas, misión multiobjetivo con batería, integración Webots, y pipeline experimental con CSV. Está **alineado con mapa conocido y sin sensores**, como exige la fase actual.

### Qué está razonablemente bien

- Representación grid clara y reproducible desde Webots vía JSON.
- Núcleo de búsqueda unificado con conteo de nodos expandidos.
- Separación por capas (`configuracion`, `planificacion`, `simulacion`, `experimentos`).
- Menú interactivo de algoritmo/heurística en simulación.
- `datos_comparados.py` reutiliza `planificar_mision` real (no lógica duplicada).
- CSV con métricas útiles y diferencia respecto a A\*+Manhattan.
- Resultados coherentes: óptimo con A\* admisible; Greedy más rápido pero subóptimo.

### Qué falta para una base experimental completa

| Elemento del TFM declarado | Estado |
|----------------------------|--------|
| Dijkstra | Implementado (vía h=0) |
| Greedy | Implementado |
| A\* | Implementado |
| **A\* ponderado** | **No implementado** |
| Heurísticas seleccionables | Parcial (3 de varias posibles del enunciado) |
| Costes de terreno variables | No |
| Métricas + CSV | Sí (comparativa offline) |
| Webots | Sí |

### Primer paso recomendado

Implementar **A\* ponderado en `planificacion/algoritmos.py`** y extender la batería de pruebas en `experimentos/datos_comparados.py`, manteniendo intactos el mundo Webots y el seguimiento del robot hasta cerrar el capítulo experimental de planificación.

---

*Documento generado por análisis estático del repositorio. No se ha modificado ningún archivo de código fuente del proyecto.*
