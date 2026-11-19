# TP2 - Armado de cargas para entregas de supermercado (*Todiafour*)
k = #vehiculos
C = capacidad del vehiculo
n = #productos
t_i = temperatura producto
w_i = peso producto
s_ij = similitud de productos

## Archivo de entrada: 
1. n C
2. w_1 t_1
3. ...
4. w_n t_n
5. s_11 ... s_1n
6.      ...
7. s_1n ... s_nn

## Requisitos

* Python 3.10 o superior (usa únicamente la librería estándar, sin dependencias externas).

## Ejecución

```bash
python3 main.py <archivo_input> <archivo_output> [--metodo M] [--alpha A] [--beta B] [--semilla S] [--max_iter I] [--top_k K] [--temperatura T] [--verbose]
```

### Parámetros
* `<archivo_input>`: ruta al archivo de instancia con el formato del enunciado.
* `<archivo_output>`: ruta donde se escribirá la solución (una línea por vehículo, índices base 0).
* `--metodo M`: algoritmo a ejecutar (por defecto `metaheuristica`). Opciones disponibles:
  * `placeholder`: solución trivial de prueba (1 producto por vehículo).
  * `constructiva1`: heurística constructiva por categoría térmica y First Fit Decreasing por peso.
  * `constructiva2`: heurística constructiva vehículo por vehículo guiada por similitud.
  * `bl1`: `constructiva1` seguida de búsqueda local (`relocate` + `swap`).
  * `bl2`: `constructiva2` seguida de búsqueda local (`relocate` + `swap`).
  * `metaheuristica`: GRASP usando `constructiva2` aleatorizada + búsqueda local.
* `--alpha A`: peso $\alpha \ge 0$ de la cantidad de vehículos $K$ en la función objetivo (por defecto `1.0`).
* `--beta B`: peso $\beta \ge 0$ de la suma de similitudes en la función objetivo (por defecto `1.0`).
* `--semilla S`: semilla entera no negativa para métodos aleatorios (por defecto `18`).
* `--max_iter I`: cantidad de iteraciones de GRASP en `--metodo metaheuristica` (por defecto `20`).
* `--top_k K`: tamaño de la lista restringida de candidatos (RCL) en GRASP (por defecto `3`).
* `--temperatura T`: criterio de compatibilidad térmica (por defecto `4cat`). Dos productos sólo pueden viajar juntos si están en el mismo grupo:
  * `4cat`: congelado (< −5 °C) | refrigerado (< 10 °C) | ambiente (< 35 °C) | caliente.
  * `3cat_frio`: congelado + refrigerado | ambiente | caliente.
  * `3cat_amb`: congelado | refrigerado | ambiente + caliente.
  * `2cat`: frío (congelado + refrigerado) | no frío (ambiente + caliente).
  * `sin_temp`: sin restricción térmica (BPP clásico, sólo como línea de base).
* `--verbose` / `-v`: imprime información adicional de la instancia cargada.

### Ejemplos de prueba

```bash
python3 main.py data/ejemplo_enunciado.txt salida_ejemplo.txt --metodo metaheuristica --alpha 1.0 --beta 0.5 --verbose
```

## Tests, generación de instancias y experimentos

* **Correr tests unitarios:**
  ```bash
  python3 -m unittest discover -s tests -v
  ```
* **Generar instancias sintéticas en `data/generadas/`:**
  ```bash
  python3 scripts/generar_instancias.py
  ```
* **Correr los 3 experimentos (genera CSVs en `resultados/`):**
  ```bash
  python3 scripts/experimentos.py
  # O por separado: --solo exp1 | exp2 | exp3 | exp4
  ```

## Estructura del proyecto

* `src/tipos.py`: dataclasses `Producto`, `Instancia` (`capacidad_vehiculo`), `Solucion`, `Metricas` y enum `Temperatura`.
* `src/io_tp.py`: parseo de argumentos, lectura de instancias, escritura de soluciones, validación básica y cálculo de métricas.
* `src/modelo.py`: clasificación térmica (4 categorías), validación de temperatura, peso y factibilidad completa.
* `src/constructivas.py`: `constructiva_temperatura_peso` y `constructiva_similitud`.
* `src/busqueda_local.py`: operadores `relocate` y `swap`, y ciclo `busqueda_local`.
* `src/metaheuristica.py`: metaheurística GRASP (`metaheuristica`).
* `main.py`: punto de entrada y despacho por `--metodo`.
* `scripts/`: generador de instancias y script de experimentación.
* `tests/`: suite de tests unitarios (`test_modelo.py`, `test_constructivas.py`, `test_busqueda_local.py`).
* `data/`: instancias de ejemplo y carpeta `data/generadas/`.
* `resultados/`: archivos CSV generados por `scripts/experimentos.py`.
