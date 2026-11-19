from src.modelo import es_solucion_factible, grupo_termico, peso_vehiculo, es_vehiculo_valido
from src.tipos import Instancia, Producto, Solucion, Temperatura
from src.io_tp import calcular_metricas

def relocate(sol: Solucion, inst: Instancia, pos_vehiculoA: int, pos_vehiculoB: int, alpha: float, beta: float) -> Solucion:
    vehiculos0 = [list(v) for v in sol.vehiculos]
    mejor_solucion = [list(v) for v in sol.vehiculos]

    if (
        (pos_vehiculoA == pos_vehiculoB) or
        (pos_vehiculoA >= len(vehiculos0)) or
        (pos_vehiculoA < 0) or
        (pos_vehiculoB >= len(vehiculos0)) or
        (pos_vehiculoB < 0) or
        len(vehiculos0[pos_vehiculoA]) == 0 or
        len(vehiculos0[pos_vehiculoB]) == 0 or
        (peso_vehiculo(vehiculos0[pos_vehiculoA], inst) < 0) or
        (peso_vehiculo(vehiculos0[pos_vehiculoB], inst) < 0) or
        not es_vehiculo_valido(vehiculos0[pos_vehiculoA], inst) or
        not es_vehiculo_valido(vehiculos0[pos_vehiculoB], inst) or
        grupo_termico(inst.productos[vehiculos0[pos_vehiculoA][0]], inst.criterio_temperatura) != grupo_termico(inst.productos[vehiculos0[pos_vehiculoB][0]], inst.criterio_temperatura)
    ):
        return sol

    vehiculoA = vehiculos0[pos_vehiculoA]
    vehiculoB = vehiculos0[pos_vehiculoB]

    metricas_iniciales = calcular_metricas(inst, sol, alpha, beta)
    mejor_objetivo = metricas_iniciales.objetivo_base

    for p in list(vehiculoA):
        vehiculoB.append(p)
        vehiculoA.remove(p)
        if es_vehiculo_valido(vehiculoB, inst):
            sol_candidata = Solucion(vehiculos=[v for v in vehiculos0 if len(v) > 0])
            metricas_cambio = calcular_metricas(inst, sol_candidata, alpha, beta)
            if metricas_cambio.objetivo_base < mejor_objetivo - 1e-9:
                mejor_objetivo = metricas_cambio.objetivo_base
                mejor_solucion = [list(v) for v in sol_candidata.vehiculos]
        vehiculoB.pop()
        vehiculoA.append(p)

    return Solucion(vehiculos=mejor_solucion)


def swap(
    sol: Solucion,
    inst: Instancia,
    pos_vehiculoA: int,
    pos_vehiculoB: int,
    alpha: float,
    beta: float,
) -> Solucion:
    """
    Evalúa todos los intercambios (1 producto de vehiculoA por 1 producto de vehiculoB)
    y devuelve la mejor solución factible encontrada si mejora la función objetivo.
    """
    _ = alpha  # K no cambia al intercambiar 1x1 entre dos vehículos no vacíos
    vehiculos = [list(v) for v in sol.vehiculos]

    if (
        pos_vehiculoA == pos_vehiculoB
        or pos_vehiculoA < 0
        or pos_vehiculoA >= len(vehiculos)
        or pos_vehiculoB < 0
        or pos_vehiculoB >= len(vehiculos)
        or len(vehiculos[pos_vehiculoA]) == 0
        or len(vehiculos[pos_vehiculoB]) == 0
        or not es_vehiculo_valido(vehiculos[pos_vehiculoA], inst)
        or not es_vehiculo_valido(vehiculos[pos_vehiculoB], inst)
        or grupo_termico(inst.productos[vehiculos[pos_vehiculoA][0]], inst.criterio_temperatura)
        != grupo_termico(inst.productos[vehiculos[pos_vehiculoB][0]], inst.criterio_temperatura)
    ):
        return Solucion(vehiculos=vehiculos)

    vehiculoA = vehiculos[pos_vehiculoA]
    vehiculoB = vehiculos[pos_vehiculoB]

    pesoA = peso_vehiculo(vehiculoA, inst)
    pesoB = peso_vehiculo(vehiculoB, inst)

    mejor_delta_obj = 0.0
    mejor_par: tuple[int, int] | None = None

    for idx_a, p in enumerate(vehiculoA):
        peso_p = inst.productos[p].peso
        for idx_b, q in enumerate(vehiculoB):
            peso_q = inst.productos[q].peso

            nuevo_pesoA = pesoA - peso_p + peso_q
            nuevo_pesoB = pesoB - peso_q + peso_p
            if (
                nuevo_pesoA > inst.capacidad_vehiculo + 1e-9
                or nuevo_pesoB > inst.capacidad_vehiculo + 1e-9
            ):
                continue

            # Cambio en la suma de similitudes intra-vehículo en A y B
            sim_p_en_A = sum(inst.similitud[p][u] for u in vehiculoA if u != p)
            sim_q_en_A = sum(inst.similitud[q][u] for u in vehiculoA if u != p)
            sim_q_en_B = sum(inst.similitud[q][v] for v in vehiculoB if v != q)
            sim_p_en_B = sum(inst.similitud[p][v] for v in vehiculoB if v != q)

            delta_sim = (sim_q_en_A - sim_p_en_A) + (sim_p_en_B - sim_q_en_B)
            delta_obj = -beta * delta_sim

            if delta_obj < mejor_delta_obj - 1e-9:
                mejor_delta_obj = delta_obj
                mejor_par = (idx_a, idx_b)

    if mejor_par is not None:
        idx_a, idx_b = mejor_par
        vehiculoA[idx_a], vehiculoB[idx_b] = vehiculoB[idx_b], vehiculoA[idx_a]

    return Solucion(vehiculos=vehiculos)


def busqueda_local(sol: Solucion, inst: Instancia, alpha: float, beta: float) -> Solucion:
    sol_actual = Solucion(vehiculos=[list(v) for v in sol.vehiculos])
    objetivo_actual = calcular_metricas(inst, sol_actual, alpha, beta).objetivo_base
    mejoro = True

    while mejoro:
        mejoro = False
        for i in range(len(sol_actual.vehiculos)):
            for j in range(len(sol_actual.vehiculos)):
                if i == j:
                    continue
                candidato = relocate(sol_actual, inst, i, j, alpha, beta)
                obj_candidato = calcular_metricas(inst, candidato, alpha, beta).objetivo_base
                if obj_candidato < objetivo_actual - 1e-9:
                    sol_actual = candidato
                    objetivo_actual = obj_candidato
                    mejoro = True
                    break
            if mejoro:
                break

        if not mejoro:
            for i in range(len(sol_actual.vehiculos)):
                for j in range(i + 1, len(sol_actual.vehiculos)):
                    candidato = swap(sol_actual, inst, i, j, alpha, beta)
                    obj_candidato = calcular_metricas(inst, candidato, alpha, beta).objetivo_base
                    if obj_candidato < objetivo_actual - 1e-9:
                        sol_actual = candidato
                        objetivo_actual = obj_candidato
                        mejoro = True
                        break
                if mejoro:
                    break

    return sol_actual