import os
import time

from adapters.guardadoBinario import GuardadoBinario
from adapters.guardadoJson import GuardadoJSON

def generar(n):
    # Datos sintéticos; ids ordenados por construcción
    return [(i,
             [(f"e-{i}", "ent_rata_gigante", 12)] if i % 3 == 0 else [],
             ["itm_antorcha"] if i % 2 == 0 else [])
            for i in range(1, n + 1)]


def medir_carga(guardador, ruta, sala_id, repeticiones):
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        guardador.cargar_sala(ruta, sala_id)
    return (time.perf_counter() - t0) / repeticiones


def medir(n, repeticiones=200):
    salas = generar(n)
    binario, js = GuardadoBinario(), GuardadoJSON()

    binario.guardar("b.sav", salas)
    js.guardar("b.json", salas)

    objetivo = n // 2
    t_bin = medir_carga(binario, "b.sav", objetivo, repeticiones)
    t_json = medir_carga(js, "b.json", objetivo, repeticiones)

    print(f"n={n:6d} | disco bin={os.path.getsize('b.sav'):8d} B  "
          f"json={os.path.getsize('b.json'):8d} B | "
          f"cargar 1 sala: bin={t_bin * 1e6:8.1f} µs  json={t_json * 1e6:9.1f} µs")
    os.remove("b.sav")
    os.remove("b.json")


def medir_carga_total(n, repeticiones=20):
    salas = generar(n)
    binario, js = GuardadoBinario(), GuardadoJSON()
    binario.guardar("b.sav", salas)
    js.guardar("b.json", salas)

    # Comprobar que ambas cargan lo mismo antes de medir
    assert binario.cargar_todo("b.sav") == js.cargar_todo("b.json")

    t0 = time.perf_counter()
    for _ in range(repeticiones):
        binario.cargar_todo("b.sav")
    t_bin = (time.perf_counter() - t0) / repeticiones

    t0 = time.perf_counter()
    for _ in range(repeticiones):
        js.cargar_todo("b.json")
    t_json = (time.perf_counter() - t0) / repeticiones

    print(f"n={n:6d} | cargar TODO: bin={t_bin * 1e3:8.2f} ms  json={t_json * 1e3:8.2f} ms")
    os.remove("b.sav")
    os.remove("b.json")


def ejecutar(tamanos=(20, 200, 2000, 20000)):
    print("--- cargar UNA sala ---")
    for n in tamanos:
        medir(n)
    print("--- cargar TODAS las salas ---")
    for n in tamanos:
        medir_carga_total(n)


def main():
    ejecutar()


if __name__ == "__main__":
    main()