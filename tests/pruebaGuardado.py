import os
import struct

from adapters.guardadoBinario import guardadoBinario


def testGuardadoSalaConEnemigosYObjetos():
    salas = [
        (1, [], []),
        (2, [("e-201", "ent_rata_gigante", 12), ("e-202", "ent_rata_gigante", 7)],
            ["itm_daga_oxidada", "itm_antorcha"]),
        (5, [], ["itm_antorcha"]),
    ]
    guardado = guardadoBinario()
    guardado.guardar("t.sav", salas)
    assert guardado.cargarSala("t.sav", 2) == salas[1]
    assert guardado.cargarSala("t.sav", 99) is None
    assert guardado.cargarTodo("t.sav") == salas


def testGuardadoVersionIncompatible():
    guardado = guardadoBinario()
    guardado.guardar("t.sav", [(1, [], [])])
    with open("t.sav", "r+b") as archivo:
        archivo.seek(4)                          # justo después de "CRPT"
        archivo.write(struct.pack("<H", 99))
    try:
        guardado.cargarSala("t.sav", 1)
        raise AssertionError("debió rechazar la versión")
    except ValueError as error:
        assert "incompatible" in str(error)


def testGuardadoArchivoInvalido():
    with open("t.sav", "wb") as archivo:
        archivo.write(b"basura" * 10)
    try:
        guardadoBinario().cargarSala("t.sav", 1)
        raise AssertionError("debió rechazar el archivo")
    except ValueError:
        pass


if __name__ == "__main__":
    try:
        testGuardadoSalaConEnemigosYObjetos()
        testGuardadoVersionIncompatible()
        testGuardadoArchivoInvalido()
        print("Guardado OK")
    finally:
        if os.path.exists("t.sav"):
            os.remove("t.sav")