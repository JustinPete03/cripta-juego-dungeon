# El reporte de red y caché (sección 5.1) debe verse al terminar, también en la interfaz gráfica.
# Lo imprime Controlador._cerrarPartida usando la función que le pasa el adaptador, así que se puede
# probar sin pygame: la vista es una captura de texto.

from controller.ControladorJuego import Controlador
from model.Acciones import Accion
from model.Constantes import ACC_ESPERAR, DERROTA
from model.Juego import Modelo
from model.Inventario import Inventario
from model.Diario import Diario
from model.efectosTrampa import efectosTrampa
from tests.FuentePrueba import FuentePrueba


class VistaQueAnota:
    def __init__(self):
        self.textos = []

    def leerComando(self):
        return None

    def mostrar(self, modelo):
        pass

    def mostrarFinal(self, modelo):
        pass

    def mostrarTexto(self, texto):
        self.textos.append(texto)


def _controlador(vista):
    # FuentePrueba no gasta red; el reporte es una constante para observar a quién se le entrega.
    proveedor = FuentePrueba(ancho=1, alto=1, enemigosPorSala=0, trampas=False)
    efectos = efectosTrampa()
    modelo = Modelo(proveedor, 7, Inventario(proveedor), Diario(), efectos)
    efectos.registrarEn(modelo)
    modelo.iniciarPartida()
    controlador = Controlador(modelo, vista, registro=None, puntajes=None, guardado=None,
                              reporte=lambda: "REPORTE: 3 / 20 solicitudes")
    return controlador, modelo


def testElReporteSalePorLaVistaAlTerminarLaPartida():
    vista = VistaQueAnota()
    controlador, modelo = _controlador(vista)
    modelo.estado = DERROTA                     # cerrar la partida por el camino del controlador
    controlador.ejecutarAccion(Accion(ACC_ESPERAR))
    assert controlador.termino
    assert any("REPORTE: 3 / 20" in texto for texto in vista.textos)


def testSinReporteNoHayNadaQueImprimir():
    # El modo --replay y la demo local no traen adaptador de red: no se les puede exigir reporte.
    vista = VistaQueAnota()
    controlador, modelo = _controlador(vista)
    controlador.reporte = None
    modelo.estado = DERROTA
    controlador.ejecutarAccion(Accion(ACC_ESPERAR))
    assert controlador.termino
    assert all("REPORTE" not in texto for texto in vista.textos)
