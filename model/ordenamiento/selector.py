from .insertion import insertion_sort
from .merge import merge_sort

MAX_INSERTION_SORT_SIZE = 32 # Bench 11 oct 2026, semilla 2026: en aleatorio inserción gana hasta n=32; merge desde n=64.
DESCENT_LIMIT = 0.05 # Mismo bench: con ~5 % de desorden inserción ganó hasta n=256.


def analizar(pares, descendente=False, contador=None):
    n = len(pares)
    descensos = 0
    for i in range(n - 1):
        if contador is not None:
            contador.incrementar()
        a, b = pares[i][0], pares[i + 1][0]
        desordenado = a < b if descendente else a > b
        if desordenado:
            descensos += 1
    return {"n": n, "descensos": descensos}


def seleccionar(propiedades):
    n = propiedades["n"]
    descensos = propiedades["descensos"]
    if n <= MAX_INSERTION_SORT_SIZE:
        return insertion_sort
    if descensos <= DESCENT_LIMIT * n:
        return insertion_sort
    return merge_sort


def ordenar(entrada, clave=None, descendente=False, contador=None):
    if clave is None:
        clave = lambda x: x
    elementos = list(entrada)
    pares = [(clave(x), x) for x in elementos]
    propiedades = analizar(pares, descendente, contador)
    algoritmo = seleccionar(propiedades)
    return algoritmo(elementos, clave, descendente, contador)