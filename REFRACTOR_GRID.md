# Refactorización: extracción de la rejilla a `planificacion/grid.py`

## Funciones movidas a `planificacion/grid.py`

| Función | Descripción |
| ------- | ----------- |
| `celda_ocupada()` | Comprueba si el centro de una celda cae dentro de un obstáculo |
| `aplicar_margen_contorno()` | Dilatación 8-vecinos del muro físico |
| `coste_de_zona()` | Resuelve el coste g de `COST_ZONE_1/2/3` |
| `celda_bloqueada()` | Consulta si una celda es transitable (versión pura con parámetros) |
| `actualizar_costes_zonas()` | Reescribe `GRID` tras cambiar costes de zona |
| `construir_grid()` | Orquesta creación de `_GRID_BASE`, `GRID`, `CELDAS_POR_ZONA`, `CELDAS_COSTE` |

## Variables que siguen expuestas desde `config.py`

- `_GRID_BASE`
- `GRID`
- `CELDAS_POR_ZONA`
- `CELDAS_COSTE`
- `ZONAS_COSTE`
- `celda_bloqueada()` — envoltorio que delega en `grid.celda_bloqueada()`
- `aplicar_costes_zonas()` — envoltorio que actualiza `COSTE_ZONA_*` y delega en `grid.actualizar_costes_zonas()`

## Archivos modificados

1. **Nuevo:** `controllers/pioneer_TFM/planificacion/grid.py`
2. **Modificado:** `controllers/pioneer_TFM/configuracion/config.py`
   - Eliminadas las funciones y bucles de construcción de rejilla
   - Añadido `from planificacion.grid import ...`
   - Llamada a `construir_grid(...)` con los parámetros ya disponibles en `config`
   - Envoltorios finos para `celda_bloqueada` y `aplicar_costes_zonas`
   - Eliminado import `re` (solo lo usaba `coste_de_zona`, ahora en `grid.py`)

**Ningún otro archivo del proyecto fue modificado.**

## Importación circular

**Evitada:** `grid.py` **no importa** `config.py`. Recibe todos los datos necesarios como argumentos de `construir_grid()` (`obstaculos`, `zonas_coste`, dimensiones, costes, `centro_celda`, etc.).

Flujo:

```text
config.py → importa grid.py → construir_grid(...)
grid.py   → no importa config.py
```

## Pruebas realizadas

### Referencia guardada antes del cambio

| Métrica | Valor |
| ------- | ----- |
| Dimensiones GRID | 48 × 48 |
| Celdas bloqueadas | 603 |
| Celdas de margen | 446 |
| Celdas por zona | COST_ZONE_1: 36, COST_ZONE_2: 78, COST_ZONE_3: 24 |
| CELDA_INICIO | (4, 15) |
| CELDAS_OBJETIVO | [(9, 22)] |
| A* + Octil — longitud | 108 celdas |
| A* + Octil — coste g | 109.07 |
| A* + Octil — nodos | 1448 |
| ARA* anytime — longitud | 223 celdas |
| ARA* anytime — coste g | 238.57 |
| ARA* anytime — nodos | 8577 |
| hash(GRID) | idéntico |
| hash(_GRID_BASE) | idéntico |

### Comparación después del cambio

**Todos los valores anteriores son idénticos.**

Las rutas completas (listas de celdas) también coinciden celda a celda.

### Ejecución de mapas PNG

```bash
python3 controllers/pioneer_TFM/herramientas/MAPAS/mundo_a_grid.py
```

Resultado: sin errores de importación. Generados correctamente:

- `map_ida.png`
- `map_vuelta.png`
- `map_ida_vuelta.png`

Resumen consola: `longitud=223 | coste_g=238.6 | nodos=8577` (igual que antes).

## Dudas o riesgos detectados

- **`centro_celda` permanece en `config.py`** y se pasa como callback a `construir_grid()`. Es la opción con menos cambios; no hay dependencia circular.
- **`distancia_a_obstaculo()` y `distancia_al_contorno()` permanecen en `config.py`** porque solo se usan para validar inicio/objetivo, no para construir la rejilla.
- **`aplicar_costes_zonas()` sigue en `config.py`** como envoltorio porque debe modificar las variables globales `COSTE_ZONA_1/2/3`; la lógica de reescritura del `GRID` está en `grid.actualizar_costes_zonas()`.
