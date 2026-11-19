import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.constructivas import constructiva_similitud, constructiva_temperatura_peso
from src.io_tp import calcular_metricas, leer_instancia
from src.modelo import es_solucion_factible
from src.tipos import Instancia, Producto


class TestConstructivas(unittest.TestCase):
    def test_factibilidad_en_instancias_data(self) -> None:
        archivos = [
            "ejemplo_enunciado.txt",
            "ejemplo_chico_8.txt",
            "ejemplo_chico_10.txt",
        ]
        for nombre in archivos:
            inst = leer_instancia(ROOT / "data" / nombre)
            for fn in (constructiva_temperatura_peso, constructiva_similitud):
                with self.subTest(archivo=nombre, metodo=fn.__name__):
                    sol = fn(inst)
                    self.assertTrue(es_solucion_factible(inst, sol))

    def test_factibilidad_con_todos_los_criterios_de_temperatura(self) -> None:
        import dataclasses
        from src.modelo import CRITERIOS_TEMPERATURA
        base = leer_instancia(ROOT / "data" / "ejemplo_chico_10.txt")
        for criterio in CRITERIOS_TEMPERATURA:
            inst = dataclasses.replace(base, criterio_temperatura=criterio)
            for fn in (constructiva_temperatura_peso, constructiva_similitud):
                with self.subTest(criterio=criterio, metodo=fn.__name__):
                    self.assertTrue(es_solucion_factible(inst, fn(inst)))

    def test_similitud_supera_peso_cuando_hay_afinidad_fuerte(self) -> None:
        # 4 congelados, capacidad 10:
        # 0 (w=5) y 1 (w=4) son muy similares (0.95)
        # 2 (w=5) y 3 (w=4) son muy similares (0.95)
        # Entre {0,1} y {2,3} la similitud es 0.05.
        productos = [
            Producto(id=0, peso=5.0, temperatura=-18.0),
            Producto(id=1, peso=4.0, temperatura=-18.0),
            Producto(id=2, peso=5.0, temperatura=-18.0),
            Producto(id=3, peso=4.0, temperatura=-18.0),
        ]
        similitud = [
            [1.00, 0.95, 0.05, 0.05],
            [0.95, 1.00, 0.05, 0.05],
            [0.05, 0.05, 1.00, 0.95],
            [0.05, 0.05, 0.95, 1.00],
        ]
        inst = Instancia(
            n=4,
            capacidad_vehiculo=10.0,
            productos=productos,
            similitud=similitud,
        )

        sol_peso = constructiva_temperatura_peso(inst)
        sol_sim = constructiva_similitud(inst)

        self.assertTrue(es_solucion_factible(inst, sol_peso))
        self.assertTrue(es_solucion_factible(inst, sol_sim))

        m_peso = calcular_metricas(inst, sol_peso, alpha=1.0, beta=1.0)
        m_sim = calcular_metricas(inst, sol_sim, alpha=1.0, beta=1.0)

        self.assertEqual(m_peso.cantidad_vehiculos, 2)
        self.assertEqual(m_sim.cantidad_vehiculos, 2)
        self.assertGreater(m_sim.suma_similitudes, m_peso.suma_similitudes)
        self.assertAlmostEqual(m_sim.suma_similitudes, 1.90)

    def test_constructiva_similitud_aleatorizada_con_semilla(self) -> None:
        inst = leer_instancia(ROOT / "data" / "ejemplo_chico_10.txt")
        sol_a = constructiva_similitud(inst, top_k=2, rng=random.Random(123))
        sol_b = constructiva_similitud(inst, top_k=2, rng=random.Random(123))

        self.assertTrue(es_solucion_factible(inst, sol_a))
        self.assertEqual(sol_a.vehiculos, sol_b.vehiculos)


if __name__ == "__main__":
    unittest.main(verbosity=2)
