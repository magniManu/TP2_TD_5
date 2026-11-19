from pathlib import Path

from src.tipos import Instancia, Metricas, Producto, Solucion, Temperatura
from src.io_tp import validar_solucion_basica

def temperatura_producto(producto: Producto) -> Temperatura:
    """A partir de un producto, determinamos su temperatura."""
    if producto.temperatura > -100.0 and producto.temperatura < 150.0:
        if producto.temperatura < -5.0:
            return Temperatura.CONGELADO    # si el producto esta a menos de -5° => esta congelado
        elif producto.temperatura < 10.0:
            return Temperatura.REFRIGERADO  # si el producto esta a menos de 10° => esta refrigerado
        elif producto.temperatura < 35.0:
            return Temperatura.AMBIENTE     # si el producto esta a menos de 35° => esta a temp ambiente
        else:
            return Temperatura.CALIENTE     # si el producto esta a mas de 35° => esta caliente
    else:
        return Temperatura.INCORRECTA       #  # si el producto no esta entre -100 y 150 grados no lo podemos transportar, seria irreal. lo marcamos como incorrecto

# Criterios de temperatura que comparamos experimentalmente (exp4).
# Cada criterio agrupa las 4 categorías térmicas en "grupos": dos productos
# pueden viajar en el mismo vehículo sólo si pertenecen al mismo grupo.
#   4cat     : congelado | refrigerado | ambiente | caliente   (criterio por defecto)
#   3cat_frio: congelado+refrigerado | ambiente | caliente
#   3cat_amb : congelado | refrigerado | ambiente+caliente
#   2cat     : congelado+refrigerado | ambiente+caliente
#   sin_temp : todos juntos (BPP clásico, sirve como línea de base)
CRITERIOS_TEMPERATURA: dict[str, dict[Temperatura, str]] = {
    "4cat": {
        Temperatura.CONGELADO: "congelado",
        Temperatura.REFRIGERADO: "refrigerado",
        Temperatura.AMBIENTE: "ambiente",
        Temperatura.CALIENTE: "caliente",
    },
    "3cat_frio": {
        Temperatura.CONGELADO: "frio",
        Temperatura.REFRIGERADO: "frio",
        Temperatura.AMBIENTE: "ambiente",
        Temperatura.CALIENTE: "caliente",
    },
    "3cat_amb": {
        Temperatura.CONGELADO: "congelado",
        Temperatura.REFRIGERADO: "refrigerado",
        Temperatura.AMBIENTE: "no_frio",
        Temperatura.CALIENTE: "no_frio",
    },
    "2cat": {
        Temperatura.CONGELADO: "frio",
        Temperatura.REFRIGERADO: "frio",
        Temperatura.AMBIENTE: "no_frio",
        Temperatura.CALIENTE: "no_frio",
    },
    "sin_temp": {
        Temperatura.CONGELADO: "unico",
        Temperatura.REFRIGERADO: "unico",
        Temperatura.AMBIENTE: "unico",
        Temperatura.CALIENTE: "unico",
    },
}


def grupo_termico(producto: Producto, criterio: str = "4cat") -> str | None:
    """Devuelve el grupo térmico del producto según el criterio, o None si su
    temperatura es INCORRECTA (fuera de rango, no se puede transportar)."""
    if criterio not in CRITERIOS_TEMPERATURA:
        raise ValueError(f"Criterio de temperatura desconocido: {criterio}")
    categoria = temperatura_producto(producto)
    if categoria == Temperatura.INCORRECTA:
        return None
    return CRITERIOS_TEMPERATURA[criterio][categoria]


def grupos_ordenados(criterio: str) -> list[str]:
    """Grupos del criterio en orden de frío a caliente (sin repetidos)."""
    return list(dict.fromkeys(CRITERIOS_TEMPERATURA[criterio].values()))


def temperatura_vehiculo_valida(vehiculo, inst: Instancia) -> bool:
    """ En base a un vehiculo y una instancia, nos fijamos si las temperaturas del
        vehiculo son compatibles: todos los productos tienen que pertenecer al mismo
        grupo térmico según inst.criterio_temperatura (por defecto, las 4 categorías).
    """
    # vehiculo es una lista de numeros, cada numero es un id de un producto
    if len(vehiculo)>0:
        grupo_vehiculo = grupo_termico(inst.productos[vehiculo[0]], inst.criterio_temperatura)
        for producto in vehiculo:
            grupo = grupo_termico(inst.productos[producto], inst.criterio_temperatura)
            if grupo is None or grupo != grupo_vehiculo:
                return False
        return True
    else: return True

def peso_vehiculo(vehiculo, inst:Instancia) -> int:
    peso_vehiculo = 0
    for producto in vehiculo:
        if inst.productos[producto].peso <= 0:
            return -1
        peso_vehiculo += inst.productos[producto].peso 
    return peso_vehiculo

def peso_vehiculo_valida(vehiculo, inst: Instancia) -> bool:
    """ A partir de un vehiculo y una instancia, chequea que el peso de los productos
        de ese vehiculo sean validos
    """
    peso_vehiculo = 0
    for producto in vehiculo:
        if inst.productos[producto].peso <= 0:
            return False
        peso_vehiculo += inst.productos[producto].peso      # sumamos el peso de los productos del vehiculo
        
    if peso_vehiculo > inst.capacidad_vehiculo + 1e-9:
        return False
    return True

def es_vehiculo_valido(vehiculo, inst: Instancia) -> bool:
    return temperatura_vehiculo_valida(vehiculo, inst) and peso_vehiculo_valida(vehiculo, inst)

def es_solucion_factible(inst:Instancia, sol: Solucion) -> bool:
    if not validar_solucion_basica(inst, sol)[0]: return False
    for vehiculo in sol.vehiculos:
        if es_vehiculo_valido(vehiculo, inst)!=True:
            return False
    return True
