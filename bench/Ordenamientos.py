import random
import time

from model.ordenamiento.Contador import Contador
from model.ordenamiento.Insertion import insertionSort
from model.ordenamiento.Merge import mergeSort
from model.ordenamiento.Selection import selectionSort

SEMILLA = 2026
REPETICIONES = 7
TAMANOS = (8, 16, 32, 64, 128, 256, 512, 1024, 2048)
REPETICIONES_COSTOSA = 15
TAMANOS_COSTOSA = (4, 8, 12, 16, 24, 32, 48, 64, 128)
LETRAS = "abcdefghijklmnopqrstuvwxyz"

def construir(n, modo, azar):
    if modo == "Aleatorio":
        return [azar.randint(0, n) for _ in range(n)]
    if modo == "Ordenado":
        return list(range(n))
    if modo == "Invertido":
        return list(range(n, 0, -1))
    if modo == "Casi":
        datos = list(range(n))
        intercambios = max(1, n // 20)
        for _ in range(intercambios):
            i = azar.randrange(n)
            j = azar.randrange(n)
            datos[i], datos[j] = datos[j], datos[i]
        return datos
    if modo == "Mitades": #Un solo descenso (caso malo para insercion)
        return (list(range(n // 2, n)) + list(range(n // 2)))
    if modo == "Vecinos": #Intercambio entre posiciones contiguas.
        datos = list(range(n))
        for _ in range(max(1, n // 20)):
            i = azar.randrange(n-1)
            datos[i], datos[i+1] = datos[i+1], datos[i]
        return datos
    raise ValueError(f"Modo desconocido: {modo}")

def mediana(valores):
    ordenados = insertionSort(valores)
    return ordenados[len(ordenados) // 2]

def medir(fn, datos):
    t0 = time.perf_counter() #Para tiempo sin contador
    fn(list(datos))
    ms = (time.perf_counter() - t0) * 1000

    contador = Contador() #Para contar comparaciones
    fn(list(datos), contador=contador)
    return ms, contador.comparaciones

algoritmos = (
    ("insertion", insertionSort),
    ("merge", mergeSort),
    ("selection", selectionSort),
)
modos = ("Aleatorio", "Ordenado", "Invertido", "Casi", "Mitades", "Vecinos")

class ClaveCostosa:
    #Simula una comparación costosa: compara los nombres carácter por carácter.
    def __init__(self, texto):
        self.texto = texto

    def comparar(self, otro):
        a = self.texto
        b = otro.texto
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                return -1 if a[i] < b[i] else 1
        return (len(a) > len(b)) - (len(a) < len(b))

    def __lt__(self, otro):
        return self.comparar(otro) < 0

    def __gt__(self, otro):
        return self.comparar(otro) > 0

def construirNombres(n, azar):
    nombres = []
    for _ in range(n):
        sufijo = "".join(azar.choice(LETRAS) for _ in range(azar.randint(3, 8)))
        nombres.append("espada de " + sufijo)
    return nombres

def medirCostosa(fn, nombres):
    t0 = time.perf_counter()
    fn(list(nombres), clave=ClaveCostosa)
    ms = (time.perf_counter() - t0) * 1000

    contador = Contador()
    fn(list(nombres), clave=ClaveCostosa, contador=contador)
    return ms, contador.comparaciones

def benchCostosa():
    azar = random.Random(SEMILLA)   #generador propio: no altera los otros resultados
    print("\n--- Comparación costosa (nombres comparados carácter por carácter) ---")
    print(f"{'n':>6}{'Ins ms':>10}{'Mer ms':>10}{'Ins comps':>11}{'Mer comps':>11}  Gana")
    for n in TAMANOS_COSTOSA:
        tiemposIns, tiemposMer, compsIns, compsMer = [], [], [], []
        for _ in range(REPETICIONES_COSTOSA):
            nombres = construirNombres(n, azar)
            ms, comps = medirCostosa(insertionSort, nombres)
            tiemposIns.append(ms)
            compsIns.append(comps)
            ms, comps = medirCostosa(mergeSort, nombres)
            tiemposMer.append(ms)
            compsMer.append(comps)
        ins = mediana(tiemposIns)
        mer = mediana(tiemposMer)
        gana = "insertion" if ins <= mer else "merge"
        print(f"{n:>6}{ins:>10.3f}{mer:>10.3f}{mediana(compsIns):>11}{mediana(compsMer):>11}  {gana}")

def main():
    azar = random.Random(SEMILLA)
    print(f"Semilla={SEMILLA}  Repeticiones={REPETICIONES}")
    print(f"{'Algo':<12}{'Modo':<12}{'n':>6}{'Ms':>12}{'Comps':>10}")
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
    benchCostosa()
if __name__ == "__main__":
    main()