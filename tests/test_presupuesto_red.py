# Pruebas del presupuesto de solicitudes (sección 2.3 y sección 3.3): el máximo de la cripta se
# respeta antes de viajar y, cuando se acaba, el juego se degrada en vez de romperse.
import pytest

from adapters.ProveedorRed import ProveedorRed
from adapters.estrategiaRed import GestorRedPrecarga
from model.Acciones import Accion
from model.Constantes import ACC_MOVER
from model.Interfaces import PresupuestoAgotado
from model.cache_estructuras import CacheCatalogo
from tests.FuentePrueba import FuentePrueba
from tests.test_cache_catalogo import ClienteFalso
from tests.TestMotor import nuevoModelo


class ClienteCotizado(ClienteFalso):
    def __init__(self, fuente, presupuesto):
        ClienteFalso.__init__(self, fuente)
        self.presupuesto = presupuesto

    def obtenerDatosGenerales(self, idCripta):
        datos = ClienteFalso.obtenerDatosGenerales(self, idCripta)
        datos["presupuesto_solicitudes"] = self.presupuesto
        return datos


class ClienteSinRed(ClienteCotizado):
    def cuentaComoRed(self):
        return False        # como ClienteOffline: una lectura local no gasta presupuesto


class FuenteCorta:
    """Sirve todo menos la sala bloqueada, donde el adaptador ya no tiene presupuesto (sección 2.3)."""

    def __init__(self, real, idSalaBloqueada):
        self._real = real
        self._bloqueada = idSalaBloqueada

    def __getattr__(self, nombre):
        return getattr(self._real, nombre)

    def contenidoSala(self, salaId):
        if salaId == self._bloqueada:
            raise PresupuestoAgotado("quedan 0 de 9 solicitudes")
        return self._real.contenidoSala(salaId)


def testLaPrecargaNoSuperaElMaximoDeLaCripta(tmp_path):
    fuente = FuentePrueba(ancho=4, alto=4, semillaCripta=3)
    cliente = ClienteCotizado(fuente, 3)

    proveedor = ProveedorRed(cliente, "cripta-prueba", capacidadCache=25,
                             directorioCache=str(tmp_path))

    assert cliente.viajes <= 3               # se frenó solo: la precarga es opcional
    with pytest.raises(PresupuestoAgotado):
        proveedor.contenidoSala(16)          # una sala que quedó fuera de la vecindad cargada
    assert cliente.viajes <= 3               # se frena antes de viajar, nunca después


def testElPresupuestoNoAplicaEnModoOffline(tmp_path):
    fuente = FuentePrueba(ancho=4, alto=4, semillaCripta=3)
    cliente = ClienteSinRed(fuente, 1)       # un solo viaje permitido, pero ninguno cuenta

    proveedor = ProveedorRed(cliente, "cripta-prueba", capacidadCache=25,
                             directorioCache=str(tmp_path))

    assert proveedor.contenidoSala(16) is not None
    assert cliente.viajes > 1


def testSinPresupuestoRechazaElMovimientoSinGastarTiempo():
    fuente = FuenteCorta(FuentePrueba(ancho=3, alto=2, semillaCripta=6), 2)
    modelo = nuevoModelo(fuente)
    relojAntes = modelo.reloj

    resultado = modelo.ejecutar(Accion(ACC_MOVER, "E"))

    assert not resultado.ok
    assert "No se puede entrar" in resultado.mensaje
    assert modelo.reloj == relojAntes                    # rechazada: no consume tiempo (sección 2.1)
    assert modelo.jugador.sala.id == 1
    assert len(modelo.salas.buscar(2).enemigos) == 0     # la sala no quedó a medio poblar


def testElGestorReservaAntesDeCadaLoteDeCatalogo():
    cliente = ClienteCotizado(FuentePrueba(), 2)
    gestor = GestorRedPrecarga(cliente, CacheCatalogo(50))
    gestor.presupuestoMaximo = 2

    ids = ["id_%02d" % i for i in range(25)]     # 25 ids son 3 lotes y solo caben 2
    with pytest.raises(PresupuestoAgotado):
        gestor.asegurarCatalogo(ids)

    assert len(cliente.lotesCatalogo) == 2
    assert cliente.viajes == 2
