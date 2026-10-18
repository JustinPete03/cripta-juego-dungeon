# Veneno originado en trampas del contenido (sección 4.1).
# La ficha de la trampa declara "veneno" (daño por pulso) y el gancho alActivarTrampa lo
# contagia. model/efectos.py es de Jurnier y no se modifica: efectosTrampa solo lo extiende.
from model.Acciones import Accion
from model.Constantes import ACC_ESPERAR, ACC_MOVER
from model.efectos import VENENO
from model.efectosTrampa import efectosTrampa
from model.Inventario import Inventario
from model.Juego import Modelo
from tests.FuentePrueba import FuentePrueba

# Cada acción de esperar avanza 100; el veneno pulsa cada 80 y dura 400 desde que se aplica.
PULSOS = 5


class FuenteConVeneno(FuentePrueba):
    def ficha(self, tipoId):
        ficha = FuentePrueba.ficha(self, tipoId)
        if ficha.get("clase") == "trampa":
            return dict(ficha, veneno=3)
        return ficha


def nuevo(venenoEnFicha=True):
    fuente = FuenteConVeneno(enemigosPorSala=0, vidaJugador=30) if venenoEnFicha \
        else FuentePrueba(enemigosPorSala=0, vidaJugador=30)
    fuente.contenidos[1]["trampas"] = [{"instancia": "t-1", "tipo": "trp_dardos"}]
    efectos = efectosTrampa()
    modelo = Modelo(fuente, 1, Inventario(fuente), None, efectos)
    efectos.registrarEn(modelo)
    modelo.iniciarPartida()
    return modelo, efectos


def testTrampaAplicaVeneno():
    m, ef = nuevo()
    m.ejecutar(Accion(ACC_MOVER, "E"))
    # 30 - 4 de la trampa - 3 del primer pulso: la agenda lo ejecuta antes de devolver el turno.
    assert m.jugador.vida == 23
    veneno = [e for e in ef.activos if e.clase == VENENO]
    assert len(veneno) == 1 and veneno[0].actor is m.jugador
    assert veneno[0].cantidad == 3


def testLosPulsosAgreganDanio():
    m, ef = nuevo()
    m.ejecutar(Accion(ACC_MOVER, "E"))
    for _ in range(4):                                # t=200..500: pulsa en 160,240,320,400,480
        m.ejecutar(Accion(ACC_ESPERAR))
    assert m.jugador.vida == 26 - 3 * PULSOS
    assert ef.activos == []                           # el veneno expiró solo


def testFichaSinVenenoNoLoAplica():
    m, ef = nuevo(False)
    m.ejecutar(Accion(ACC_MOVER, "E"))
    assert m.jugador.vida == 26
    assert ef.activos == []


def testTrampaMortalNoEnvenena():
    m, ef = nuevo()
    m.jugador.vida = 4
    m.ejecutar(Accion(ACC_MOVER, "E"))
    assert not m.jugador.vivo
    assert ef.activos == []
