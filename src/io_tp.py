import argparse
from pathlib import Path

from src.tipos import Instancia, Metricas, Producto, Solucion


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="TP2 - Armado de cargas para entregas de supermercado (Todiafour)"
    )
    parser.add_argument("archivo_input", help="Ruta al archivo de instancia de entrada")
    parser.add_argument("archivo_output", help="Ruta al archivo de salida con la solución")
    parser.add_argument(
        "--metodo",
        default="metaheuristica",
        help="Método a ejecutar (por defecto: metaheuristica)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="Peso alpha >= 0 de la cantidad de vehículos K (por defecto: 1.0)",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=1.0,
        help="Peso beta >= 0 de la suma de similitudes (por defecto: 1.0)",
    )
    parser.add_argument(
        "--semilla",
        type=int,
        default=18,
        help="Semilla entera para métodos aleatorios (por defecto: 18)",
    )
    parser.add_argument(
        "--max_iter",
        type=int,
        default=20,
        help="Cantidad de iteraciones de la metaheurística GRASP (por defecto: 20)",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=3,
        help="Tamaño de la lista restringida de candidatos en GRASP (por defecto: 3)",
    )
    parser.add_argument(
        "--temperatura",
        default="4cat",
        choices=["4cat", "3cat_frio", "3cat_amb", "2cat", "sin_temp"],
        help="Criterio de compatibilidad térmica entre productos (por defecto: 4cat)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Imprime información detallada de la instancia",
    )

    args = parser.parse_args(argv)
    if args.alpha < 0 or args.beta < 0:
        parser.error("Los parámetros --alpha y --beta deben ser >= 0.")
    if args.semilla < 0:
        parser.error("El parámetro --semilla debe ser >= 0.")
    if args.max_iter < 1:
        parser.error("El parámetro --max_iter debe ser >= 1.")
    if args.top_k < 1:
        parser.error("El parámetro --top_k debe ser >= 1.")
    return args


def leer_instancia(ruta_archivo: str | Path) -> Instancia:
    """Lee y valida una instancia desde un archivo con el formato del enunciado."""
    ruta = Path(ruta_archivo)
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {ruta}")

    tokens = ruta.read_text(encoding="utf-8").split()
    if len(tokens) < 2:
        raise ValueError(f"Archivo inválido o vacío: {ruta}")

    try:
        n = int(tokens[0])
        capacidad_vehiculo = float(tokens[1])
    except ValueError as err:
        raise ValueError(f"Error al parsear n y C en la primera línea de {ruta}") from err

    if n <= 0:
        raise ValueError(f"La cantidad de productos n debe ser positiva (recibido: {n}).")
    if capacidad_vehiculo <= 0:
        raise ValueError(
            f"La capacidad del vehículo debe ser positiva (recibido: {capacidad_vehiculo})."
        )

    cantidad_esperada = 2 + 2 * n + n * n
    if len(tokens) != cantidad_esperada:
        raise ValueError(
            f"Cantidad de valores inesperada en {ruta}: "
            f"esperados {cantidad_esperada}, encontrados {len(tokens)}."
        )

    idx = 2
    productos: list[Producto] = []
    for i in range(n):
        try:
            peso = float(tokens[idx])
            temperatura = float(tokens[idx + 1])
        except ValueError as err:
            raise ValueError(f"Peso o temperatura inválidos para el producto {i}.") from err
        idx += 2

        if peso <= 0:
            raise ValueError(f"El peso del producto {i} debe ser > 0 (recibido: {peso}).")
        if peso > capacidad_vehiculo + 1e-9:
            raise ValueError(
                f"El producto {i} pesa más que capacidad_vehiculo "
                f"({peso} > {capacidad_vehiculo})."
            )
        productos.append(Producto(id=i, peso=peso, temperatura=temperatura))

    similitud: list[list[float]] = []
    for i in range(n):
        fila: list[float] = []
        for j in range(n):
            try:
                s = float(tokens[idx])
            except ValueError as err:
                raise ValueError(f"Similitud inválida en ({i}, {j}).") from err
            idx += 1

            if s < -1e-9 or s > 1.0 + 1e-9:
                raise ValueError(f"Similitud fuera de [0, 1] en ({i}, {j}): {s}.")
            fila.append(s)
        similitud.append(fila)

    for i in range(n):
        if abs(similitud[i][i] - 1.0) > 1e-6:
            raise ValueError(f"La diagonal de similitudes debe valer 1 en s[{i}][{i}].")
        for j in range(i + 1, n):
            if abs(similitud[i][j] - similitud[j][i]) > 1e-6:
                raise ValueError(f"La matriz de similitudes no es simétrica en ({i}, {j}).")

    return Instancia(
        n=n,
        capacidad_vehiculo=capacidad_vehiculo,
        productos=productos,
        similitud=similitud,
    )


def escribir_solucion(ruta_archivo: str | Path, sol: Solucion) -> None:
    """Escribe la solución: una línea por vehículo con índices base 0 separados por espacio."""
    lineas = [
        " ".join(str(prod_id) for prod_id in vehiculo)
        for vehiculo in sol.vehiculos
        if vehiculo
    ]
    contenido = "\n".join(lineas) + ("\n" if lineas else "")
    Path(ruta_archivo).write_text(contenido, encoding="utf-8")


def validar_solucion_basica(inst: Instancia, sol: Solucion) -> tuple[bool, str]:
    """
    Verifica las restricciones básicas de Bin Packing:
      1. No hay vehículos vacíos.
      2. Todos los índices están en [0, n-1].
      3. Cada producto aparece en exactamente un vehículo.
      4. La suma de pesos de cada vehículo no supera inst.capacidad_vehiculo.
    """
    apariciones = [0] * inst.n

    for k, vehiculo in enumerate(sol.vehiculos):
        if not vehiculo:
            return False, f"El vehículo {k} está vacío."

        carga_total = 0.0
        for prod_id in vehiculo:
            if prod_id < 0 or prod_id >= inst.n:
                return False, f"Índice de producto inválido ({prod_id}) en vehículo {k}."
            apariciones[prod_id] += 1
            carga_total += inst.productos[prod_id].peso

        if carga_total > inst.capacidad_vehiculo + 1e-9:
            return (
                False,
                f"El vehículo {k} excede capacidad_vehiculo "
                f"({carga_total:.4f} > {inst.capacidad_vehiculo:.4f}).",
            )
    for i, count in enumerate(apariciones):
        if count == 0:
            return False, f"El producto {i} no fue asignado a ningún vehículo."
        if count > 1:
            return False, f"El producto {i} aparece asignado {count} veces."

    return True, ""


def calcular_metricas(
    inst: Instancia, sol: Solucion, alpha: float, beta: float
) -> Metricas:
    """Calcula K, suma de similitudes intra-vehículo y función objetivo base."""
    vehiculos_no_vacios = [v for v in sol.vehiculos if v]
    k = len(vehiculos_no_vacios)
    suma_similitudes = 0.0

    for vehiculo in vehiculos_no_vacios:
        m = len(vehiculo)
        for a in range(m):
            u = vehiculo[a]
            for b in range(a + 1, m):
                v = vehiculo[b]
                suma_similitudes += inst.similitud[u][v]

    objetivo_base = alpha * k - beta * suma_similitudes
    return Metricas(
        cantidad_vehiculos=k,
        suma_similitudes=suma_similitudes,
        objetivo_base=objetivo_base,
    )
