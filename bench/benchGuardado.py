import os
import time

from adapters.guardadoBinario import guardadoBinario
from adapters.guardadoJson import guardadoJson


def generar(n):
    # Datos sintéticos; ids ordenados por construcción
    return [(i,
             [(f"e-{i}", "ent_rata_gigante", 12)] if i % 3 == 0 else [],
             ["itm_antorcha"] if i % 2 == 0 else [])
            for i in range(1, n + 1)]


def medirCarga(guardador, ruta, salaId, repeticiones):
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        guardador.cargarSala(ruta, salaId)
    return (time.perf_counter() - inicio) / repeticiones


def medir(n, repeticiones=200):
    salas = generar(n)
    binario, json = guardadoBinario(), guardadoJson()

    binario.guardar("b.sav", salas)
    json.guardar("b.json", salas)

    objetivo = n // 2
    tBinario = medirCarga(binario, "b.sav", objetivo, repeticiones)
    tJson = medirCarga(json, "b.json", objetivo, repeticiones)

    print(f"n={n:6d} | disco bin={os.path.getsize('b.sav'):8d} B  "
          f"json={os.path.getsize('b.json'):8d} B | "
          f"cargar 1 sala: bin={tBinario * 1e6:8.1f} µs  json={tJson * 1e6:9.1f} µs")
    os.remove("b.sav")
    os.remove("b.json")


def medirCargaTotal(n, repeticiones=20):
    salas = generar(n)
    binario, json = guardadoBinario(), guardadoJson()
    binario.guardar("b.sav", salas)
    json.guardar("b.json", salas)

    # Comprobar que ambas cargan lo mismo antes de medir
    assert binario.cargarTodo("b.sav") == json.cargarTodo("b.json")

    inicio = time.perf_counter()
    for _ in range(repeticiones):
        binario.cargarTodo("b.sav")
    tBinario = (time.perf_counter() - inicio) / repeticiones

    inicio = time.perf_counter()
    for _ in range(repeticiones):
        json.cargarTodo("b.json")
    tJson = (time.perf_counter() - inicio) / repeticiones

    print(f"n={n:6d} | cargar TODO: bin={tBinario * 1e3:8.2f} ms  json={tJson * 1e3:8.2f} ms")
    os.remove("b.sav")
    os.remove("b.json")


def ejecutar(tamanos=(20, 200, 2000, 20000)):
    print("--- cargar UNA sala ---")
    for n in tamanos:
        medir(n)
    print("--- cargar TODAS las salas ---")
    for n in tamanos:
        medirCargaTotal(n)


def main():
    ejecutar()


if __name__ == "__main__":
    main()