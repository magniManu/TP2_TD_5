import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.io_tp import calcular_metricas, leer_instancia, validar_solucion_basica
from src.modelo import (
    es_solucion_factible,
    es_vehiculo_valido,
    grupo_termico,
    peso_vehiculo_valida,
    temperatura_producto,
    temperatura_vehiculo_valida,
)
from src.tipos import Instancia, Producto, Solucion, Temperatura


class TestTemperaturaProducto(unittest.TestCase):
    def test_rangos_y_bordes(self) -> None:
        casos = [
            (-99.9, Temperatura.CONGELADO),
            (-18.0, Temperatura.CONGELADO),
            (-5.1, Temperatura.CONGELADO),
            (-5.0, Temperatura.REFRIGERADO),
            (4.0, Temperatura.REFRIGERADO),
            (9.9, Temperatura.REFRIGERADO),
            (10.0, Temperatura.AMBIENTE),
            (20.0, Temperatura.AMBIENTE),
            (34.9, Temperatura.AMBIENTE),
            (35.0, Temperatura.CALIENTE),
            (60.0, Temperatura.CALIENTE),
            (149.9, Temperatura.CALIENTE),
            (-100.0, Temperatura.INCORRECTA),
            (-150.0, Temperatura.INCORRECTA),
            (150.0, Temperatura.INCORRECTA),
            (200.0, Temperatura.INCORRECTA),
        ]
        for temp, esperado in casos:
            with self.subTest(temp=temp):
                prod = Producto(id=0, peso=1.0, temperatura=temp)
                self.assertEqual(temperatura_producto(prod), esperado)


class TestValidacionesVehiculo(unittest.TestCase):
    def setUp(self) -> None:
        self.productos = [
            Producto(id=0, peso=4.0, temperatura=-18.0),   # Congelado
            Producto(id=1, peso=6.0, temperatura=-10.0),   # Congelado
            Producto(id=2, peso=5.0, temperatura=4.0),     # Refrigerado
            Producto(id=3, peso=5.0, temperatura=20.0),    # Ambiente
            Producto(id=4, peso=3.0, temperatura=45.0),    # Caliente
            Producto(id=5, peso=2.0, temperatura=200.0),   # Incorrecta
            Producto(id=6, peso=0.0, temperatura=20.0),    # Peso invalido (<= 0)
            Producto(id=7, peso=11.0, temperatura=20.0),   # Excede capacidad 10
        ]
        n = len(self.productos)
        similitud = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        self.inst = Instancia(
            n=n,
            capacidad_vehiculo=10.0,
            productos=self.productos,
            similitud=similitud,
        )

    def test_temperatura_vehiculo_valida(self) -> None:
        self.assertTrue(temperatura_vehiculo_valida([], self.inst))
        self.assertTrue(temperatura_vehiculo_valida([0, 1], self.inst))
        self.assertFalse(temperatura_vehiculo_valida([0, 2], self.inst))
        self.assertFalse(temperatura_vehiculo_valida([5], self.inst))
        self.assertFalse(temperatura_vehiculo_valida([3, 5], self.inst))

    def test_criterios_temperatura(self) -> None:
        """Cada criterio define qué categorías pueden compartir vehículo."""
        import dataclasses
        casos = {
            # criterio: (congelado+refrigerado, ambiente+caliente, congelado+caliente)
            "4cat": (False, False, False),
            "3cat_frio": (True, False, False),
            "3cat_amb": (False, True, False),
            "2cat": (True, True, False),
            "sin_temp": (True, True, True),
        }
        for criterio, (frio, no_frio, extremos) in casos.items():
            inst = dataclasses.replace(self.inst, criterio_temperatura=criterio)
            with self.subTest(criterio=criterio):
                self.assertEqual(temperatura_vehiculo_valida([0, 2], inst), frio)
                self.assertEqual(temperatura_vehiculo_valida([3, 4], inst), no_frio)
                self.assertEqual(temperatura_vehiculo_valida([0, 4], inst), extremos)
                # Un producto con temperatura incorrecta nunca es válido
                self.assertFalse(temperatura_vehiculo_valida([5], inst))
        self.assertIsNone(grupo_termico(self.productos[5]))
        with self.assertRaises(ValueError):
            grupo_termico(self.productos[0], "criterio_inexistente")

    def test_peso_vehiculo_valida(self) -> None:
        self.assertTrue(peso_vehiculo_valida([], self.inst))
        self.assertTrue(peso_vehiculo_valida([0, 1], self.inst))   # 4 + 6 = 10 == C
        self.assertFalse(peso_vehiculo_valida([0, 1, 2], self.inst))  # 15 > 10
        self.assertFalse(peso_vehiculo_valida([6], self.inst))     # peso <= 0
        self.assertFalse(peso_vehiculo_valida([7], self.inst))     # 11 > 10

    def test_es_vehiculo_valido(self) -> None:
        self.assertTrue(es_vehiculo_valido([0, 1], self.inst))
        self.assertFalse(es_vehiculo_valido([0, 2], self.inst))  # peso 9 <= 10 pero distinta temp
        self.assertFalse(es_vehiculo_valido([3, 7], self.inst))  # misma temp pero peso 16 > 10
        self.assertFalse(es_vehiculo_valido([5], self.inst))     # temp incorrecta


class TestInstanciasReales(unittest.TestCase):
    def test_ejemplo_enunciado(self) -> None:
        inst = leer_instancia(ROOT / "data" / "ejemplo_enunciado.txt")
        # 0: w=4 t=4 (Ref), 1: w=5 t=4 (Ref), 2: w=3 t=20 (Amb), 3: w=6 t=-18 (Cong), C=10
        sol_optima = Solucion(vehiculos=[[0, 1], [2], [3]])
        valida_basica, err = validar_solucion_basica(inst, sol_optima)
        self.assertTrue(valida_basica, err)
        self.assertTrue(es_solucion_factible(inst, sol_optima))

        # Si mezclamos producto 0 (Ref) con producto 2 (Amb), cumple peso (7 <= 10) pero falla temp
        sol_invalida_temp = Solucion(vehiculos=[[0, 2], [1], [3]])
        self.assertFalse(es_solucion_factible(inst, sol_invalida_temp))

    def test_ejemplo_chico_8(self) -> None:
        inst = leer_instancia(ROOT / "data" / "ejemplo_chico_8.txt")
        self.assertEqual(inst.n, 8)

        sol_logica = Solucion(vehiculos=[[0, 1], [2, 3], [4, 5], [6, 7]])
        valida_basica, err = validar_solucion_basica(inst, sol_logica)
        self.assertTrue(valida_basica, err)
        self.assertTrue(es_solucion_factible(inst, sol_logica))

        metricas = calcular_metricas(inst, sol_logica, alpha=1.0, beta=1.0)
        self.assertEqual(metricas.cantidad_vehiculos, 4)
        self.assertAlmostEqual(metricas.suma_similitudes, 0.95 + 0.90 + 0.85 + 0.92)

        # Mezclar grupos de temperatura distintos debe dar solucion no factible
        sol_mezclada = Solucion(vehiculos=[[0, 2], [1, 3], [4, 5], [6, 7]])
        self.assertFalse(es_solucion_factible(inst, sol_mezclada))

    def test_ejemplo_chico_10(self) -> None:
        inst = leer_instancia(ROOT / "data" / "ejemplo_chico_10.txt")
        self.assertEqual(inst.n, 10)

        # Solucion esperada logica: [0,1], [2], [3,4,5], [6,7], [8], [9]
        sol_logica = Solucion(vehiculos=[[0, 1], [2], [3, 4, 5], [6, 7], [8], [9]])
        valida_basica, err = validar_solucion_basica(inst, sol_logica)
        self.assertTrue(valida_basica, err)
        self.assertTrue(es_solucion_factible(inst, sol_logica))

        # Si juntamos [8, 9] tienen misma temperatura (Caliente), pero pesan 6 + 7 = 13 > 12
        sol_exceso_peso = Solucion(vehiculos=[[0, 1], [2], [3, 4, 5], [6, 7], [8, 9]])
        self.assertFalse(es_solucion_factible(inst, sol_exceso_peso))


if __name__ == "__main__":
    unittest.main(verbosity=2)
