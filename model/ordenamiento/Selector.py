from .Insertion import insertionSort
from .Merge import mergeSort

# Umbrales calibrados con bench/Ordenamientos.py (12 oct 2026, semilla 2026, mediana de 7 repeticiones).

# Modo "aleatorio": inserción gana hasta n=32, empata en n=64 (0.200 vs 0.204 ms) y merge gana desde n=128.
MAX_INSERTION_SORT_SIZE = 32

# Proporción de descensos hasta la cual inserción sigue ganando (modo "casi": ~5 % de desorden).
LIMITE_DESCENSOS = 0.05

# Modo "casi" (n//20 intercambios al azar): inserción gana hasta n=256 y merge desde n=512.
# Tope necesario: en "mitades" (1 descenso pero ~n²/4 inversiones) inserción tarda 172 ms
# contra 4.6 ms de merge en n=2048, y los descensos no distinguen ese caso de "vecinos".
MAX_ALMOST_SORTED = 256


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
        return insertionSort
    if descensos == 0:         # ya ordenada: inserción aquí sería O(n)
        return insertionSort
    if n <= MAX_ALMOST_SORTED and descensos <= LIMITE_DESCENSOS * n:
        return insertionSort
    return mergeSort


def ordenar(entrada, clave=None, descendente=False, contador=None):
    if clave is None:
        clave = lambda x: x
    pares = [(clave(x),x) for x in entrada]
    propiedades = analizar(pares, descendente, contador)
    algoritmo = seleccionar(propiedades)
    resultado = algoritmo(pares, lambda par: par[0], descendente, contador)
    return [par[1] for par in resultado]