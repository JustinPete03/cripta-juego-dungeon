import os
import struct

import adapters.guardadoPartida as moduloGuardado
from adapters.guardadoBinario import guardadoBinario
from adapters.guardadoPartida import guardadoPartida
from model.Acciones import Accion
from model.Constantes import ACC_ESPERAR, ACC_MOVER, EN_CURSO
from model.Diario import Diario
from tests.FuentePrueba import FuentePrueba
from tests.TestMotor import foto, nuevoModelo
from adapters.guardadoBinario import guardadoBinario


def testGuardadoSalaConEnemigosYObjetos():
    salas = [
        (1, [], [], []),
        (2, [("e-201", "ent_rata_gigante", 12), ("e-202", "ent_rata_gigante", 7)],
            ["itm_daga_oxidada", "itm_antorcha"], [("t-17", "trp_dardos")]),
        (5, [], ["itm_antorcha"], []),
    ]
    guardado = guardadoBinario()
    guardado.guardar("t.sav", salas)
    assert guardado.cargarSala("t.sav", 2) == salas[1]
    assert guardado.cargarSala("t.sav", 99) is None
    assert guardado.cargarTodo("t.sav") == salas


def testGuardadoVersionIncompatible():
    guardado = guardadoBinario()
    guardado.guardar("t.sav", [(1, [], [], [])])
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


# ---------------------------------------------------------------- partida completa
PRIMERA = [(ACC_MOVER, "S"), (ACC_ESPERAR, None), (ACC_MOVER, "E"), (ACC_MOVER, "S"),
           (ACC_ESPERAR, None), (ACC_MOVER, "E"), (ACC_ESPERAR, None), (ACC_MOVER, "N")]
SEGUNDA = [(ACC_ESPERAR, None), (ACC_MOVER, "E"), (ACC_ESPERAR, None), (ACC_MOVER, "S"),
           (ACC_ESPERAR, None), (ACC_MOVER, "O"), (ACC_ESPERAR, None), (ACC_MOVER, "S")]


def _partida(fuente=None):
    fuente = fuente if fuente is not None else FuentePrueba(
        ancho=5, alto=4, enemigosPorSala=2, vidaJugador=10 ** 6)
    return nuevoModelo(fuente, diario=Diario())


def _jugar(modelo, acciones):
    for tipo, argumento in acciones:
        if modelo.estado == EN_CURSO:
            modelo.ejecutar(Accion(tipo, argumento))


def _incorporadas(modelo):
    return sum(1 for i in range(modelo.salas.cantidad())
               if modelo.salas.enPosicion(i).contenidoIncorporado)


def testPartidaIdaYVuelta(tmp_path):
    guardado = guardadoPartida("c", "v1", "k1")
    ruta = str(tmp_path / "a.sav")
    base = _partida()
    _jugar(base, PRIMERA)
    alGuardar = (foto(base), base.azar.getstate())
    guardado.guardar(base, ruta)

    otro = _partida()
    guardado.cargar(otro, ruta)
    assert (foto(otro), otro.azar.getstate()) == alGuardar        # justo tras cargar

    _jugar(base, SEGUNDA)                                         # sin interrupción
    _jugar(otro, SEGUNDA)                                         # desde lo cargado
    assert (foto(otro), otro.azar.getstate()) == (foto(base), base.azar.getstate())


class _FuenteContada(FuentePrueba):
    pedidos = 0

    def contenidoSala(self, salaId):
        self.pedidos += 1
        return FuentePrueba.contenidoSala(self, salaId)


def testCargarNoPideContenidoYaGuardado(tmp_path):
    guardado = guardadoPartida("c", "v1", "k1")
    ruta = str(tmp_path / "b.sav")
    base = _partida()
    _jugar(base, PRIMERA)
    assert _incorporadas(base) >= 2                  # hay salas visitadas que restaurar
    guardado.guardar(base, ruta)

    fuente = _FuenteContada(ancho=5, alto=4, enemigosPorSala=2, vidaJugador=10 ** 6)
    otro = _partida(fuente)
    fuente.pedidos = 0
    guardado.cargar(otro, ruta)
    assert fuente.pedidos == 0


def testCargarRechazaOtraVersionDeCripta(tmp_path):
    ruta = str(tmp_path / "c.sav")
    base = _partida()
    guardadoPartida("c", "v1", "k1").guardar(base, ruta)
    for guardado in (guardadoPartida("c", "v2", "k1"),      # otra versión de cripta
                     guardadoPartida("c", "v1", "k2"),      # otra versión de catálogo
                     guardadoPartida("otra", "v1", "k1")):  # otra cripta
        try:
            guardado.cargar(_partida(), ruta)
            raise AssertionError("debió rechazar una partida de otra versión")
        except ValueError as error:
            assert "otra cripta" in str(error)


def testCargarRechazaArchivoAjenoYFormatoViejo(tmp_path):
    guardado = guardadoPartida("c", "v1", "k1")
    ajeno = str(tmp_path / "ajeno.sav")
    with open(ajeno, "wb") as archivo:
        archivo.write(b"basura" * 20)
    try:
        guardado.cargar(_partida(), ajeno)
        raise AssertionError("debió rechazar un archivo ajeno")
    except ValueError as error:
        assert "no es una partida" in str(error)

    viejo = str(tmp_path / "viejo.sav")
    guardado.guardar(_partida(), viejo)
    with open(viejo, "r+b") as archivo:
        archivo.seek(4)                                   # justo después de la firma
        archivo.write(struct.pack("<H", 1))               # formato antiguo
    try:
        guardado.cargar(_partida(), viejo)
        raise AssertionError("debió rechazar el formato viejo")
    except ValueError as error:
        assert "incompatible" in str(error)


def testLeerSalaLeeUnaFraccionDelArchivo(tmp_path, monkeypatch):
    fuente = FuentePrueba(ancho=30, alto=20, enemigosPorSala=2, vidaJugador=10 ** 6)
    modelo = _partida(fuente)
    for i in range(modelo.salas.cantidad()):
        modelo._asegurarContenido(modelo.salas.enPosicion(i))
    guardado = guardadoPartida("c", "v1", "k1")
    ruta = str(tmp_path / "grande.sav")
    guardado.guardar(modelo, ruta)
    tamano = os.path.getsize(ruta)

    class Contando:                      # cuenta los bytes que se leen del archivo
        leidos = 0

        def __init__(self, archivo):
            self.archivo = archivo

        def read(self, n=-1):
            datos = self.archivo.read(n)
            Contando.leidos += len(datos)
            return datos

        def __getattr__(self, nombre):
            return getattr(self.archivo, nombre)

        def __enter__(self):
            return self

        def __exit__(self, *datos):
            self.archivo.close()

    import builtins
    monkeypatch.setattr(moduloGuardado, "open",
                        lambda r, modo="r": Contando(builtins.open(r, modo)), raising=False)
    contenido = guardado.leerSala(ruta, 7)
    assert contenido == fuente.contenidoSala(7)
    assert Contando.leidos < tamano * 0.05
    assert guardado.leerSala(ruta, 99999) is None

if __name__ == "__main__":
    try:
        testGuardadoSalaConEnemigosYObjetos()
        testGuardadoVersionIncompatible()
        testGuardadoArchivoInvalido()
        print("Guardado OK")
    finally:
        if os.path.exists("t.sav"):
            os.remove("t.sav")