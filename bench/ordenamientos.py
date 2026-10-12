import random
import time

from model.ordenamiento.contador import Contador
from model.ordenamiento.insertion import insertion_sort
from model.ordenamiento.merge import merge_sort
from model.ordenamiento.selection import selection_sort

SEMILLA = 2026
REPETICIONES = 7
TAMANOS = (8, 16, 32, 64, 128, 256, 512, 1024, 2048)

def construir(n, modo, azar):
    if modo == "aleatorio":
        return [azar.randint(0, n) for _ in range(n)]
    if modo == "ordenado":
        return list(range(n))
    if modo == "invertido":
        return list(range(n, 0, -1))
    if modo == "casi":
        datos = list(range(n))
        intercambios = max(1, n // 20)
        for _ in range(intercambios):
            i = azar.randrange(n)
            j = azar.randrange(n)
            datos[i], datos[j] = datos[j], datos[i]
        return datos
    if modo == "mitades": #Un solo decenso (caso malo para insercion)
        return (list(range(n // 2, n)) + list(range(n // 2)))
    if modo == "vecinos": #Intercambio entre posiciones contiguas.
        datos = list(range(n))
        for _ in range(max(1, n // 20)):
            i = azar.randrange(n-1)
            datos[i], datos[i+1] = datos[i+1], datos[i]
        return datos
    raise ValueError(f"modo desconocido: {modo}")

def mediana(valores):
    ordenados = insertion_sort(valores)
    return ordenados[len(ordenados) // 2]

def medir(fn, datos):
    t0 = time.perf_counter() #Para tiempo sin contador
    fn(list(datos))
    ms = (time.perf_counter() - t0) * 1000

    contador = Contador() #Para contar comparaciones
    fn(list(datos), contador=contador)
    return ms, contador.comparaciones

algoritmos = (
    ("insertion", insertion_sort),
    ("merge", merge_sort),
    ("selection", selection_sort),
)
modos = ("aleatorio", "ordenado", "invertido", "casi", "mitades", "vecinos")

def main():
    azar = random.Random(SEMILLA)
    print(f"semilla={SEMILLA}  repeticiones={REPETICIONES}")
    print(f"{'algo':<12}{'modo':<12}{'n':>6}{'ms':>12}{'comps':>10}")
    for nombre, fn in algoritmos:
        for modo in modos:
            for n in TAMANOS:
                tiempos = []
                comparaciones = []
                for _ in range(REPETICIONES):
                    datos = construir(n, modo, azar)
                    ms, comps = medir(fn, datos)
                    tiempos.append(ms)
                    comparaciones.append(comps)
                print(
                    f"{nombre:<12}{modo:<12}{n:>6}"
                    f"{mediana(tiempos):>12.3f}{mediana(comparaciones):>10}"
                )

if __name__ == "__main__":
    main()