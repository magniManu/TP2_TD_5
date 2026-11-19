import random

from src.modelo import es_solucion_factible, grupo_termico, grupos_ordenados
from src.tipos import Instancia, Producto, Solucion


def agrupar_por_temperatura(inst: Instancia) -> dict[str, list[Producto]]:
    """Separa los productos según su grupo térmico (inst.criterio_temperatura).
    Devuelve los grupos ordenados de frío a caliente."""
    grupos: dict[str, list[Producto]] = {g: [] for g in grupos_ordenados(inst.criterio_temperatura)}
    invalidos = []
    for producto in inst.productos:
        g = grupo_termico(producto, inst.criterio_temperatura)
        if g is None:
            invalidos.append(producto.id)
        else:
            grupos[g].append(producto)
    if invalidos:
        raise ValueError(f"Hay productos con temperatura fuera de rango: {invalidos}")
    return grupos

def constructiva_temperatura_peso(inst:Instancia) -> Solucion:
    """Primero separamos por temperatura y despues ordenamos por peso"""
    sol = Solucion()
    temperaturas_dict = agrupar_por_temperatura(inst)

    for cat, productos_cat in temperaturas_dict.items():
        productos_ordenados = sorted(productos_cat, key=lambda p: p.peso, reverse=True)
        vehiculos_cat: list[list[int]] = []
        pesos_cat: list[float] = []

        for producto in productos_ordenados:
            if producto.peso > inst.capacidad_vehiculo + 1e-9:
                raise ValueError(
                    f"El producto {producto.id} excede la capacidad del vehículo."
                )

            ubicado = False
            for k in range(len(vehiculos_cat)):
                if pesos_cat[k] + producto.peso <= inst.capacidad_vehiculo + 1e-9:
                    vehiculos_cat[k].append(producto.id)
                    pesos_cat[k] += producto.peso
                    ubicado = True
                    break

            if not ubicado:
                vehiculos_cat.append([producto.id])
                pesos_cat.append(producto.peso)

        sol.vehiculos.extend(vehiculos_cat)

    if not es_solucion_factible(inst, sol):
        raise ValueError("La solución construida no es factible.")
    return sol



def constructiva_similitud(
    inst: Instancia,
    top_k: int = 1,
    rng: random.Random | None = None,
) -> Solucion:
    """
    Construye una solución vehículo por vehículo dentro de cada categoría térmica.
    Abre cada vehículo con el producto libre más pesado (semilla) y agrega
    sucesivamente el producto compatible que maximiza la suma de similitudes
    con los productos ya cargados en ese vehículo.

    Si top_k > 1, elige aleatoriamente entre los top_k mejores candidatos
    (útil como construcción aleatorizada para metaheurísticas como GRASP).
    """
    if top_k < 1:
        raise ValueError("top_k debe ser >= 1.")
    if top_k > 1 and rng is None:
        rng = random.Random()

    sol = Solucion()
    for producto in inst.productos:
        if producto.peso <= 0 or producto.peso > inst.capacidad_vehiculo + 1e-9:
            raise ValueError(
                f"El producto {producto.id} tiene peso inválido ({producto.peso}) "
                f"para capacidad_vehiculo={inst.capacidad_vehiculo}."
            )
    temperaturas_dict = agrupar_por_temperatura(inst)

    for cat, productos_cat in temperaturas_dict.items():
        # Ordenamos por peso descendente para tomar semillas pesadas primero.
        libres = sorted(productos_cat, key=lambda p: (-p.peso, p.id))

        while libres:
            semilla = libres.pop(0)
            vehiculo = [semilla.id]
            peso_actual = semilla.peso

            while True:
                candidatos: list[tuple[float, float, int, int]] = []
                for idx, prod in enumerate(libres):
                    if peso_actual + prod.peso <= inst.capacidad_vehiculo + 1e-9:
                        sim_con_vehiculo = sum(
                            inst.similitud[prod.id][u] for u in vehiculo
                        )
                        # Ordenar por mayor similitud acumulada, luego mayor peso, luego menor id
                        candidatos.append((sim_con_vehiculo, prod.peso, -prod.id, idx))

                if not candidatos:
                    break

                candidatos.sort(reverse=True)
                limite = min(top_k, len(candidatos))
                elegido = candidatos[0] if limite == 1 else rng.choice(candidatos[:limite])
                idx_libre = elegido[3]
                prod_elegido = libres.pop(idx_libre)

                vehiculo.append(prod_elegido.id)
                peso_actual += prod_elegido.peso

            sol.vehiculos.append(vehiculo)

    if not es_solucion_factible(inst, sol):
        raise ValueError("La solución construida no es factible.")
    return sol