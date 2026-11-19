"""Script de experimentación sistemática y tuning de parámetros para el TP2.

Genera archivos CSV en `resultados/` y resúmenes por consola para:
  1. exp1_alpha_beta.csv: sensibilidad de alpha y beta (trade-off entre K y similitud).
  2. exp2_tuning_grasp.csv: tuning de top_k y max_iter en GRASP.
  3. exp3_comparacion_metodos.csv: comparación de constructivas, búsqueda local y GRASP.
  4. exp4_criterios_temperatura.csv: costo (en vehículos) y calidad de cada criterio térmico.

Uso:
    python3 scripts/experimentos.py
    python3 scripts/experimentos.py --solo exp1
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.busqueda_local import busqueda_local
from src.constructivas import constructiva_similitud, constructiva_temperatura_peso
from src.io_tp import calcular_metricas, leer_instancia
from src.metaheuristica import metaheuristica
from src.modelo import CRITERIOS_TEMPERATURA, es_solucion_factible, grupo_termico, temperatura_producto
from src.tipos import Instancia, Solucion, Temperatura


def contar_pares_intra_vehiculo(sol: Solucion) -> int:
    total = 0
    for v in sol.vehiculos:
        m = len(v)
        total += m * (m - 1) // 2
    return total


def correr_metodo(
    metodo: str,
    inst: Instancia,
    alpha: float,
    beta: float,
    semilla: int = 18,
    max_iter: int = 15,
    top_k: int = 3,
) -> tuple[Solucion, float]:
    inicio = time.perf_counter()
    if metodo == "constructiva1":
        sol = constructiva_temperatura_peso(inst)
    elif metodo == "constructiva2":
        sol = constructiva_similitud(inst)
    elif metodo == "bl1":
        sol = busqueda_local(constructiva_temperatura_peso(inst), inst, alpha, beta)
    elif metodo == "bl2":
        sol = busqueda_local(constructiva_similitud(inst), inst, alpha, beta)
    elif metodo == "metaheuristica":
        sol = metaheuristica(
            inst, alpha=alpha, beta=beta, semilla=semilla, max_iter=max_iter, top_k=top_k
        )
    else:
        raise ValueError(f"Método desconocido: {metodo}")
    tiempo_ms = (time.perf_counter() - inicio) * 1000.0
    return sol, tiempo_ms


def guardar_csv(ruta: Path, columnas: list[str], filas: list[dict[str, object]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)


def exp1_alpha_beta(carpeta_data: Path, carpeta_res: Path) -> None:
    print("\n=== Experimento 1: Sensibilidad de alpha y beta ===")
    instancias = [
        "inst_n30_mix.txt",
        "inst_n50_ambiente_quimicos.txt",
        "inst_n50_pesados.txt",
    ]
    alpha = 1.0
    betas = [0.0, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
    metodos = ["bl2", "metaheuristica"]

    filas: list[dict[str, object]] = []
    for nombre in instancias:
        inst = leer_instancia(carpeta_data / nombre)
        for metodo in metodos:
            for beta in betas:
                sol, tiempo_ms = correr_metodo(
                    metodo, inst, alpha=alpha, beta=beta, semilla=18, max_iter=10, top_k=3
                )
                m = calcular_metricas(inst, sol, alpha, beta)
                pares = contar_pares_intra_vehiculo(sol)
                sim_prom = m.suma_similitudes / pares if pares > 0 else 0.0
                filas.append(
                    {
                        "instancia": nombre,
                        "n": inst.n,
                        "metodo": metodo,
                        "alpha": alpha,
                        "beta": beta,
                        "K": m.cantidad_vehiculos,
                        "suma_similitudes": round(m.suma_similitudes, 4),
                        "similitud_promedio_par": round(sim_prom, 4),
                        "objetivo_base": round(m.objetivo_base, 4),
                        "pares_similitud_baja": metricas_calidad_carga(inst, sol)["pares_similitud_baja"],
                        "tiempo_ms": round(tiempo_ms, 2),
                    }
                )
                print(
                    f"{nombre:30s} {metodo:14s} beta={beta:4.2f} -> "
                    f"K={m.cantidad_vehiculos:2d} sim_prom={sim_prom:.3f} obj={m.objetivo_base:8.2f}"
                )

    ruta = carpeta_res / "exp1_alpha_beta.csv"
    guardar_csv(
        ruta,
        [
            "instancia",
            "n",
            "metodo",
            "alpha",
            "beta",
            "K",
            "suma_similitudes",
            "similitud_promedio_par",
            "objetivo_base",
            "pares_similitud_baja",
            "tiempo_ms",
        ],
        filas,
    )
    print(f"Guardado: {ruta.relative_to(ROOT)}")


def exp2_tuning_grasp(carpeta_data: Path, carpeta_res: Path) -> None:
    print("\n=== Experimento 2: Tuning de GRASP (top_k y max_iter) ===")
    instancias = ["inst_n40_mix.txt", "inst_n50_ambiente_quimicos.txt"]
    alpha, beta = 1.0, 0.5
    top_ks = [1, 2, 3, 5]
    max_iters = [5, 10, 20, 30]
    semillas = [18, 9, 54]

    filas: list[dict[str, object]] = []
    for nombre in instancias:
        inst = leer_instancia(carpeta_data / nombre)
        for top_k in top_ks:
            for max_iter in max_iters:
                for semilla in semillas:
                    sol, tiempo_ms = correr_metodo(
                        "metaheuristica",
                        inst,
                        alpha=alpha,
                        beta=beta,
                        semilla=semilla,
                        max_iter=max_iter,
                        top_k=top_k,
                    )
                    m = calcular_metricas(inst, sol, alpha, beta)
                    filas.append(
                        {
                            "instancia": nombre,
                            "n": inst.n,
                            "alpha": alpha,
                            "beta": beta,
                            "top_k": top_k,
                            "max_iter": max_iter,
                            "semilla": semilla,
                            "K": m.cantidad_vehiculos,
                            "suma_similitudes": round(m.suma_similitudes, 4),
                            "objetivo_base": round(m.objetivo_base, 4),
                            "tiempo_ms": round(tiempo_ms, 2),
                        }
                    )
                subset = [
                    f for f in filas
                    if f["instancia"] == nombre
                    and f["top_k"] == top_k
                    and f["max_iter"] == max_iter
                ]
                obj_prom = sum(float(f["objetivo_base"]) for f in subset) / len(subset)
                t_prom = sum(float(f["tiempo_ms"]) for f in subset) / len(subset)
                print(
                    f"{nombre:30s} top_k={top_k} max_iter={max_iter:2d} -> "
                    f"obj_prom={obj_prom:8.3f} tiempo_prom={t_prom:7.1f} ms"
                )

    ruta = carpeta_res / "exp2_tuning_grasp.csv"
    guardar_csv(
        ruta,
        [
            "instancia",
            "n",
            "alpha",
            "beta",
            "top_k",
            "max_iter",
            "semilla",
            "K",
            "suma_similitudes",
            "objetivo_base",
            "tiempo_ms",
        ],
        filas,
    )
    print(f"Guardado: {ruta.relative_to(ROOT)}")


def exp3_comparacion_metodos(carpeta_data: Path, carpeta_res: Path) -> None:
    print("\n=== Experimento 3: Comparación de todos los métodos ===")
    archivos = sorted(p.name for p in carpeta_data.glob("*.txt"))
    metodos = ["constructiva1", "constructiva2", "bl1", "bl2", "metaheuristica"]
    alpha, beta = 1.0, 0.5

    filas: list[dict[str, object]] = []
    for nombre in archivos:
        inst = leer_instancia(carpeta_data / nombre)
        for metodo in metodos:
            sol, tiempo_ms = correr_metodo(
                metodo, inst, alpha=alpha, beta=beta, semilla=18, max_iter=15, top_k=3
            )
            m = calcular_metricas(inst, sol, alpha, beta)
            factible = es_solucion_factible(inst, sol)
            filas.append(
                {
                    "instancia": nombre,
                    "n": inst.n,
                    "capacidad": inst.capacidad_vehiculo,
                    "metodo": metodo,
                    "alpha": alpha,
                    "beta": beta,
                    "K": m.cantidad_vehiculos,
                    "suma_similitudes": round(m.suma_similitudes, 4),
                    "objetivo_base": round(m.objetivo_base, 4),
                    "tiempo_ms": round(tiempo_ms, 2),
                    "factible": factible,
                }
            )
            print(
                f"{nombre:30s} {metodo:14s} -> "
                f"K={m.cantidad_vehiculos:2d} sim={m.suma_similitudes:7.2f} "
                f"obj={m.objetivo_base:8.2f} t={tiempo_ms:7.1f} ms"
            )

    ruta = carpeta_res / "exp3_comparacion_metodos.csv"
    guardar_csv(
        ruta,
        [
            "instancia",
            "n",
            "capacidad",
            "metodo",
            "alpha",
            "beta",
            "K",
            "suma_similitudes",
            "objetivo_base",
            "tiempo_ms",
            "factible",
        ],
        filas,
    )
    print(f"Guardado: {ruta.relative_to(ROOT)}")


def cota_inferior_vehiculos(inst: Instancia) -> int:
    """Cota inferior de K: en cada grupo térmico hacen falta al menos
    ceil(peso_total_grupo / C) vehículos (con sin_temp es la cota clásica del BPP)."""
    pesos: dict[str, float] = {}
    for p in inst.productos:
        g = grupo_termico(p, inst.criterio_temperatura)
        pesos[g] = pesos.get(g, 0.0) + p.peso
    return sum(math.ceil(w / inst.capacidad_vehiculo - 1e-9) for w in pesos.values())


def metricas_calidad_carga(inst: Instancia, sol: Solucion) -> dict[str, int]:
    """Cuenta pares de productos que viajan juntos y que Todiafour probablemente
    no aceptaría (independiente del criterio usado para construir la solución)."""
    mezcla_cat = cong_cal = dif_15 = baja_sim = 0
    for v in sol.vehiculos:
        for a in range(len(v)):
            pa = inst.productos[v[a]]
            for b in range(a + 1, len(v)):
                pb = inst.productos[v[b]]
                ca, cb = temperatura_producto(pa), temperatura_producto(pb)
                if ca != cb:
                    mezcla_cat += 1
                if {ca, cb} == {Temperatura.CONGELADO, Temperatura.CALIENTE}:
                    cong_cal += 1
                if abs(pa.temperatura - pb.temperatura) > 15.0:
                    dif_15 += 1
                if inst.similitud[v[a]][v[b]] < 0.2:
                    baja_sim += 1
    return {
        "pares_distinta_categoria": mezcla_cat,
        "pares_congelado_caliente": cong_cal,
        "pares_dif_temp_mayor_15": dif_15,
        "pares_similitud_baja": baja_sim,
    }


def exp4_criterios_temperatura(carpeta_data: Path, carpeta_res: Path) -> None:
    print("\n=== Experimento 4: Criterios de temperatura ===")
    archivos = sorted(p.name for p in carpeta_data.glob("*.txt"))
    criterios = list(CRITERIOS_TEMPERATURA.keys())
    metodos = ["bl1", "bl2", "metaheuristica"]
    alpha, beta = 1.0, 0.5

    filas: list[dict[str, object]] = []
    for nombre in archivos:
        base = leer_instancia(carpeta_data / nombre)
        for criterio in criterios:
            inst = dataclasses.replace(base, criterio_temperatura=criterio)
            cota = cota_inferior_vehiculos(inst)
            for metodo in metodos:
                sol, tiempo_ms = correr_metodo(
                    metodo, inst, alpha=alpha, beta=beta, semilla=18, max_iter=15, top_k=3
                )
                m = calcular_metricas(inst, sol, alpha, beta)
                pares = contar_pares_intra_vehiculo(sol)
                calidad = metricas_calidad_carga(inst, sol)
                filas.append(
                    {
                        "instancia": nombre,
                        "n": inst.n,
                        "criterio": criterio,
                        "metodo": metodo,
                        "K": m.cantidad_vehiculos,
                        "cota_inferior_K": cota,
                        "suma_similitudes": round(m.suma_similitudes, 4),
                        "similitud_promedio_par": round(
                            m.suma_similitudes / pares if pares else 0.0, 4
                        ),
                        "objetivo_base": round(m.objetivo_base, 4),
                        **calidad,
                        "tiempo_ms": round(tiempo_ms, 2),
                        "factible": es_solucion_factible(inst, sol),
                    }
                )
                print(
                    f"{nombre:30s} {criterio:9s} {metodo:14s} -> K={m.cantidad_vehiculos:2d} "
                    f"(LB={cota:2d}) cong-cal={calidad['pares_congelado_caliente']:3d} "
                    f"sim<0.2={calidad['pares_similitud_baja']:4d} t={tiempo_ms:7.1f} ms"
                )

    ruta = carpeta_res / "exp4_criterios_temperatura.csv"
    guardar_csv(ruta, list(filas[0].keys()), filas)
    print(f"Guardado: {ruta.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Corre experimentos del TP2.")
    parser.add_argument(
        "--solo",
        choices=["exp1", "exp2", "exp3", "exp4"],
        default=None,
        help="Ejecuta únicamente uno de los 3 experimentos.",
    )
    args = parser.parse_args()

    carpeta_data = ROOT / "data" / "generadas"
    carpeta_res = ROOT / "resultados"

    if not carpeta_data.exists() or not any(carpeta_data.glob("*.txt")):
        raise FileNotFoundError(
            "No hay instancias en data/generadas/. Ejecutá primero: "
            "python3 scripts/generar_instancias.py"
        )

    if args.solo in (None, "exp1"):
        exp1_alpha_beta(carpeta_data, carpeta_res)
    if args.solo in (None, "exp2"):
        exp2_tuning_grasp(carpeta_data, carpeta_res)
    if args.solo in (None, "exp3"):
        exp3_comparacion_metodos(carpeta_data, carpeta_res)
    if args.solo in (None, "exp4"):
        exp4_criterios_temperatura(carpeta_data, carpeta_res)


if __name__ == "__main__":
    main()
