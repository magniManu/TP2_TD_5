import sys
import time

from src.io_tp import (
    calcular_metricas,
    escribir_solucion,
    leer_instancia,
    parsear_argumentos,
    validar_solucion_basica,
)
from src.busqueda_local import busqueda_local
from src.constructivas import (
    constructiva_similitud,
    constructiva_temperatura_peso,
)
from src.metaheuristica import metaheuristica

from src.tipos import Instancia, Solucion

# prueba de i/o hecha por ia
def resolver_placeholder(inst: Instancia) -> Solucion:
    """
    Solución trivial de prueba (1 producto por vehículo) para testear I/O y validación.
    Reemplazar con las heurísticas constructivas, búsqueda local y metaheurística del grupo.
    """
    return Solucion(vehiculos=[[i] for i in range(inst.n)])


def main() -> int:
    try:
        # leemos los argumentos y la instancia
        cfg = parsear_argumentos()
        inst = leer_instancia(cfg.archivo_input)
        inst.criterio_temperatura = cfg.temperatura

        if cfg.verbose:
            print(
                f"Instancia cargada: n={inst.n}, "
                f"capacidad_vehiculo={inst.capacidad_vehiculo}"
            )

        inicio = time.perf_counter()

        # leemos el metodo usado
        if cfg.metodo == "placeholder":
            sol = resolver_placeholder(inst)
        elif cfg.metodo == "constructiva1":
            sol = constructiva_temperatura_peso(inst)
        elif cfg.metodo == "constructiva2":
            sol = constructiva_similitud(inst)
        elif cfg.metodo == "bl1":
            sol = busqueda_local(constructiva_temperatura_peso(inst), inst, cfg.alpha, cfg.beta)
        elif cfg.metodo == "bl2":
            sol = busqueda_local(constructiva_similitud(inst), inst, cfg.alpha, cfg.beta)
        elif cfg.metodo == "metaheuristica":
            sol = metaheuristica(inst, cfg.alpha, cfg.beta, cfg.semilla, cfg.max_iter, cfg.top_k)
        else:
            raise ValueError(f"Método desconocido: {cfg.metodo}")

        tiempo_ms = (time.perf_counter() - inicio) * 1000.0

        # nos fijamos que cumpla con las restricciones basicas de Bin Packing
        es_valida, error = validar_solucion_basica(inst, sol)
        if not es_valida:
            print(f"Error: solución inválida -> {error}", file=sys.stderr)
            return 1
        
        
        # escribimos la solucion en el archivo de salida
        escribir_solucion(cfg.archivo_output, sol)

        m = calcular_metricas(inst, sol, cfg.alpha, cfg.beta)
        print(
            f"Metodo={cfg.metodo} "
            f"K={m.cantidad_vehiculos} "
            f"Similitud={m.suma_similitudes:.4f} "
            f"ObjetivoBase={m.objetivo_base:.4f} "
            f"TiempoMs={tiempo_ms:.3f}"
        )
        return 0
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
