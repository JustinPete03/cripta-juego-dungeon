# Pruebas del guardado de la partida completa: formato binario propio, acceso aleatorio por sala
# e ida y vuelta del estado (model/estado.py) a traves del archivo.

import os
import struct

from adapters.codBinary import codificar, decodificar
from adapters.guardadoBinario import Contenedor
from adapters.guardadoPartida import guardadoPartida, MAGIC, VERSION_FORMATO
from model.Acciones import Accion
from model.Constantes import ACC_MOVER, ACC_RECOGER, ACC_USAR
from model.Diario import Diario
from model.Inventario import Inventario
from model.Juego import Modelo
from model.efectosTrampa import efectosTrampa
from tests.FuentePrueba import FuentePrueba
from tests.TestMotor import foto

RUTA = "tmp_partida.sav"
ID_CRIPTA = "cripta-prueba"
VERSION_CRIPTA = "v1"


def _modelo():
    fuente = FuentePrueba(ancho=8, alto=5, semillaCripta=11)
    efectos = efectosTrampa()
    modelo = Modelo(fuente, 3, Inventario(fuente), Diario(), efectos)
    efectos.registrarEn(modelo)
    modelo.iniciarPartida()
    return modelo


def _guardado():
    return guardadoPartida(ID_CRIPTA, VERSION_CRIPTA, None)


def _jugarUnRato(modelo):
    for direccion in ("N", "E", "S", "E", "N", "O"):
        modelo.ejecutar(Accion(ACC_MOVER, direccion))
    for _ in range(2):
        modelo.ejecutar(Accion(ACC_RECOGER, 0))
    modelo.ejecutar(Accion(ACC_USAR, 0))


class ContenedorContable(Contenedor):
    """Mide cuantos bloques lee el acceso aleatorio; la prueba exige que sean pocos."""

    def __init__(self):
        super().__init__(MAGIC, VERSION_FORMATO)
        self.bytesLeidos = 0

    def _bytes(self, archivo, posicion, largo):
        self.bytesLeidos += largo
        return super()._bytes(archivo, posicion, largo)


def testIdaYVueltaDelEstado():
    modelo = _modelo()
    _jugarUnRato(modelo)
    esperado = foto(modelo)
    _guardado().guardar(modelo, RUTA)
    try:
        recargado = _modelo()
        _guardado().cargar(recargado, RUTA)
        assert foto(recargado) == esperado
    finally:
        os.remove(RUTA)


def testSalaSeCargaSinLeerElArchivoCompleto():
    modelo = _modelo()
    _jugarUnRato(modelo)
    _guardado().guardar(modelo, RUTA)
    try:
        contenedor = ContenedorContable()
        tamano = os.path.getsize(RUTA)
        sala = max(i for i in range(1, modelo.salas.cantidad() + 1)
                   if modelo.salas.buscar(i).contenidoIncorporado)
        bloque = contenedor.cargarSala(RUTA, sala)
        assert bloque["sala"] == sala
        assert bloque == modelo.proveedor.contenidoSala(sala)
        assert contenedor.bytesLeidos < tamano * 0.25, (contenedor.bytesLeidos, tamano)
    finally:
        os.remove(RUTA)


def testSalaInexistenteDevuelveNada():
    modelo = _modelo()
    _guardado().guardar(modelo, RUTA)
    try:
        assert _guardado().cargarSala(RUTA, 9999) is None
    finally:
        os.remove(RUTA)


def testRechazaOtraVersionDeCripta():
    modelo = _modelo()
    _guardado().guardar(modelo, RUTA)
    try:
        otro = guardadoPartida(ID_CRIPTA, "v2", None)
        try:
            otro.cargar(_modelo(), RUTA)
            raise AssertionError("debió rechazar la versión de otra cripta")
        except ValueError as error:
            assert "otra cripta" in str(error)
    finally:
        os.remove(RUTA)


def testCodificadorBinarioIdaYVuelta():
    datos = {"reloj": 300, "vida": 30, "velocidad": 100, "flotante": 2.5,
             "grande": 1 << 40, "vacio": None, "abierto": True, "cerrada": False,
             "enemigos": [["e-1", "ent_rata", 12], ["e-2", "ent_guardian", 20]],
             "salas": [{"id": 1, "salidas": {"N": {"sala": 6, "cerrada": True}}}]}
    crudo = codificar(datos)
    assert isinstance(crudo, bytes)
    assert decodificar(crudo)[1] == len(crudo)          # el bloque se consume justo entero
    assert decodificar(crudo)[0] == datos
    # una tupla viaja como lista: es el unico cambio de tipo que admite el formato
    assert decodificar(codificar(("e-1", 12)))[0] == ["e-1", 12]


def testCodificadorRechazaBasura():
    try:
        decodificar(bytes([250, 0, 0, 0]))
        raise AssertionError("debió rechazar un tag desconocido")
    except ValueError as error:
        assert "tag desconocido" in str(error)


def testVersionDeFormatoIncompatible():
    modelo = _modelo()
    _guardado().guardar(modelo, RUTA)
    try:
        with open(RUTA, "r+b") as archivo:
            archivo.seek(4)                          # justo después del magic
            archivo.write(struct.pack("<H", 99))
        try:
            _guardado().cargar(_modelo(), RUTA)
            raise AssertionError("debió rechazar el formato desconocido")
        except ValueError as error:
            assert "incompatible" in str(error)
    finally:
        os.remove(RUTA)
