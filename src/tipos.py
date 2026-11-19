from dataclasses import dataclass, field
from enum import StrEnum


@dataclass(frozen=True)
class Producto:
    """Representa un producto a transportar en la flota de Todiafour."""

    id: int             # Índice del producto (0 .. n-1)
    peso: float         # w_i > 0
    temperatura: float  # t_i en grados Celsius


@dataclass
class Instancia:
    """Contiene todos los datos de una instancia del problema."""

    n: int
    capacidad_vehiculo: float  # Capacidad máxima de cada vehículo (nombre obligatorio)
    productos: list[Producto]
    similitud: list[list[float]]  # Matriz simétrica n x n con valores en [0, 1]
    criterio_temperatura: str = "4cat"  # ver src/modelo.py: CRITERIOS_TEMPERATURA


@dataclass
class Solucion:
    """Representa una asignación de productos a vehículos (índices base 0)."""

    vehiculos: list[list[int]] = field(default_factory=list)


@dataclass(frozen=True)
class Metricas:
    """Métricas base de evaluación de una solución (sin penalizaciones de temperatura)."""

    cantidad_vehiculos: int    # K
    suma_similitudes: float    # Sumatoria de s_ij para pares i < j en el mismo vehículo
    objetivo_base: float       # alpha * K - beta * suma_similitudes

class Temperatura(StrEnum):
    CONGELADO = "Congelado"
    REFRIGERADO = "Refrigerado"
    AMBIENTE = "Ambiente"
    CALIENTE = "Caliente"
    INCORRECTA = "Temperatura Incorrecta"