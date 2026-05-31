# Proyecto TFM - Planificación de rutas con A* y ARA*

Este proyecto forma parte del Trabajo Fin de Máster y tiene como objetivo estudiar la **planificación de rutas de un robot móvil** en un entorno simulado con **Webots**.

El robot utilizado es un **Pioneer 3-AT**. El escenario de Webots se transforma en una **rejilla o grid**, donde cada celda representa una parte del espacio: suelo libre, obstáculo o zona especial con coste. Sobre esa representación se aplican algoritmos de búsqueda heurística, principalmente **A*** y **ARA***.

La finalidad del proyecto no es solo que el robot llegue desde un punto inicial hasta un objetivo, sino analizar cómo cambia la ruta cuando se modifican algunos factores del entorno, como el coste de ciertas zonas, el margen de seguridad o los parámetros del algoritmo.

---

## 1. Funcionamiento general

El flujo básico del proyecto es:

1. Se define un mundo en Webots.
2. El mundo se convierte en una matriz de celdas.
3. Cada celda se clasifica como suelo libre, muro o zona especial.
4. Se selecciona un algoritmo de planificación.
5. El algoritmo calcula una ruta desde el inicio hasta el objetivo.
6. La ruta se visualiza y puede compararse con otras configuraciones.

Los dos algoritmos principales son:

- **A***: calcula una ruta combinando el coste acumulado y una heurística hacia el objetivo.
- **ARA***: parte de una solución rápida con un valor alto de `epsilon` y permite mejorar la ruta reduciendo progresivamente ese valor.

---

## 2. Representación del mapa

El escenario de Webots se transforma en un `GRID`, es decir, una matriz de celdas.

La codificación usada debe mantenerse separada del coste:

```text
0 = suelo libre transitable
1 = muro u obstáculo no transitable
2 = zona especial transitable

```

Esta separación evita que el algoritmo confunda un muro con una zona transitable de coste bajo.

---

## 3. Estructura principal del proyecto

La organización general del proyecto es la siguiente:

```text
pioneer_TFM/
│
├── worlds/
│   └── pioneer3at.wbt
│
├── controllers/
│   └── pioneer_TFM/
│       ├── pioneer_TFM.py
│       │
│       ├── configuracion/
│       │   ├── config.py
│       │   ├── config_menu.py
│       │   ├── experimento.json
│       │   └── generated_map.json
│       │
│       ├── planificacion/
│       │   ├── algoritmos.py
│       │   ├── mapa.py
│       │   └── heuristicas.py
│       │
│       ├── simulacion/
│       │   ├── menu_heuristica.py
│       │   ├── robot_io.py
│       │   └── seguimiento.py
│       │
│       ├── herramientas/
│       │   ├── mundo_a_grid.py
│       │   ├── extract_wbt_to_json.py
│       │   └── metricas.py
│       │
│       └── experimentos/
│           ├── datos_comparados.py
│           └── resultados_experimentos.csv
│
└── README.md

```

---

## 4. Archivos principales

### `worlds/pioneer3at.wbt`

Es el mundo principal de Webots. Contiene el escenario donde se mueve el robot, incluyendo muros, zonas especiales, posición inicial y objetivos.

Cuando se modifica la geometría del mundo, normalmente es necesario volver a generar el mapa en formato grid.

---

### `controllers/pioneer_TFM/pioneer_TFM.py`

Es el archivo principal del controlador del robot.

Se encarga de:

- cargar la configuración;
- iniciar la simulación;
- pedir o aplicar la configuración del algoritmo;
- planificar la ruta;
- hacer que el robot siga el camino calculado.

Es el punto de entrada principal cuando el proyecto se ejecuta desde Webots.

---

## 5. Carpeta `configuracion/`

Esta carpeta contiene los archivos que definen los parámetros generales del proyecto.

### `config.py`

Es uno de los archivos más importantes. Centraliza la configuración del mapa, del algoritmo y de los costes.

Aquí se definen o se cargan elementos como:

- el `GRID`;
- el tamaño de celda;
- el inicio y los objetivos;
- los costes de las zonas;
- el margen de seguridad;
- el algoritmo seleccionado;
- los parámetros de ARA*;
- las constantes de celda: libre, muro y zona.

También contiene funciones de conversión entre coordenadas del mundo y coordenadas del grid.

---

### `config_menu.py`

Gestiona la configuración mediante archivo o menú.

Sirve para cargar parámetros desde `experimento.json` y aplicarlos al programa sin tener que modificar siempre el código principal.

---

### `experimento.json`

Guarda valores de configuración del experimento.

Puede contener parámetros como:

- algoritmo elegido;
- heurística;
- valores de `epsilon`;
- costes de zonas;
- batería;
- suelo cambiante.

Es útil para repetir pruebas con la misma configuración.

---

### `generated_map.json`

Es el archivo intermedio donde se guarda el mapa extraído desde Webots.

Contiene información como:

- dimensiones del grid;
- tamaño de celda;
- obstáculos;
- zonas especiales;
- inicio;
- objetivos.

No suele editarse manualmente. Lo normal es regenerarlo a partir del mundo `.wbt`.

---

## 6. Carpeta `planificacion/`

Contiene la parte lógica de la planificación de rutas.

### `algoritmos.py`

Implementa los algoritmos de búsqueda y la lógica principal de planificación.

Incluye la planificación con A*, ARA* y otras variantes si están activadas en el proyecto. También calcula costes de ruta y gestiona la planificación de una misión completa, por ejemplo ir al objetivo y volver a la base.

Es el archivo central para estudiar el comportamiento de los algoritmos.

---

### `mapa.py`

Contiene funciones auxiliares para trabajar con el mapa.

Sirve para:

- comprobar si una celda es transitable;
- convertir posiciones del mundo a celdas del grid;
- convertir celdas del grid a posiciones del mundo;
- trabajar con las coordenadas del mapa.

---

### `heuristicas.py`

Define las heurísticas utilizadas por los algoritmos.

Por ejemplo:

- Manhattan;
- Euclídea;
- Octil;
- heurística nula.

La heurística influye en cómo el algoritmo estima la distancia hasta el objetivo.

---

## 7. Carpeta `simulacion/`

Contiene archivos relacionados con la ejecución del robot dentro de Webots.

### `menu_heuristica.py`

Permite seleccionar el algoritmo y la heurística desde la simulación.

Sirve para probar distintas configuraciones sin tener que cambiar manualmente el código.

---

### `robot_io.py`

Gestiona la comunicación con Webots y con el robot.

Se encarga de leer el estado del robot, controlar elementos de la simulación y mostrar información visual, como la batería o ciertos indicadores.

---

### `seguimiento.py`

Contiene la lógica para que el robot siga la ruta calculada.

A partir del camino generado por el algoritmo, decide cómo debe moverse el robot para avanzar hacia los puntos de la trayectoria.

---

## 8. Carpeta `herramientas/`

Incluye scripts auxiliares para generar mapas, visualizar resultados o extraer información.

### `mundo_a_grid.py`

Genera una representación visual del mapa en forma de grid.

Permite comprobar si los muros, zonas especiales, inicio, objetivo y rutas se están representando correctamente.

Es especialmente útil para revisar si el mapa que usa el algoritmo coincide con el escenario esperado.

---

### `extract_wbt_to_json.py`

Extrae información del mundo `.wbt` y la convierte en un archivo `generated_map.json`.

Se utiliza cuando se modifica el mundo de Webots y se necesita actualizar la representación del mapa.

---

### `metricas.py`

Sirve para realizar comprobaciones o mediciones auxiliares del comportamiento de las rutas.

Puede usarse para revisar costes, longitudes o resultados de planificación en pruebas concretas.

---

## 9. Carpeta `experimentos/`

Contiene archivos destinados a comparar resultados.

### `datos_comparados.py`

Ejecuta comparaciones entre algoritmos o configuraciones.

Puede utilizarse para obtener datos sobre:

- coste de la ruta;
- nodos expandidos;
- tiempo de cálculo;
- diferencias entre algoritmos;
- efecto de cambiar costes o heurísticas.

---

### `resultados_experimentos.csv`

Guarda los resultados de las pruebas realizadas.

Es útil para recoger datos que luego pueden utilizarse en la memoria del TFM.

---

## 11. Zonas especiales y costes

Las zonas especiales permiten estudiar cómo cambia la planificación cuando una parte del terreno tiene un coste distinto.

Una zona puede representar, por ejemplo:

- terreno más difícil;
- mayor consumo de batería;
- una zona que conviene evitar;
- un área cuyo coste cambia durante la ejecución.

La regla que debe mantenerse es:

```text
La celda indica el tipo de terreno.
La variable de coste indica cuánto cuesta pasar por ella.

```

Ejemplo:

```text
0 = libre
1 = muro
2 = zona especial

COSTE_ZONA_1 = coste de atravesar una zona concreta

```

Esto permite cambiar el coste de una zona sin modificar la estructura básica del mapa.

---

