# Escala del mapa

## Parejas de ficheros

| Uso | Config | Mundo Webots | JSON |
|-----|--------|--------------|------|
| Activo | `config.py` | `worlds/pioneer3at.wbt` | `generated_map.json` |
| Reserva | `config1.py` | `worlds/pioneer3at1.wbt` | `generated_map1.json` |

Para usar la reserva: renombra la pareja reserva sobre la activa y abre el `.wbt` correspondiente en Webots.

## Dónde cambiar la escala (siempre en la misma pareja)

1. **`config.py`** (o `config1.py`): `CELL_SIZE`
2. **`worlds/pioneer3at.wbt`** (o `pioneer3at1.wbt`):
   - Una sola línea `# Mapa lógico NxN` (informativa; no repetir en otros comentarios)
   - `RectangleArena` → `floorSize`, `floorTileSize`
   - Coordenadas de START, GOAL, Pioneer y obstáculos
3. **JSON**: se regenera al importar config o con `python herramientas/extract_wbt_to_json.py`

Los límites del JSON salen de **`floorSize`** del `.wbt`, no del comentario del grid.

## Después de editar

1. Guarda el `.wbt`
2. Reinicia la simulación en Webots
3. Comprueba: `python configuracion/prueba_config.py`

Si hay error de coordenadas, el mensaje indica si el punto queda fuera de la arena o fuera de la rejilla (desajuste entre `CELL_SIZE` y `floorSize`).
