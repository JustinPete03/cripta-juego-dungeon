# Pruebas del inventario (4.5) y del retroceso (4.6, 2.11) con el Diario y el Inventario reales.
import random
import unittest

from model.Constantes import *
from model.Acciones import Accion, accionesDesdeTexto
from model.Diario import Diario
from model.Entidades import ObjetoInstancia
from model.Inventario import Inventario, Nodo
from model.Juego import Modelo
from tests.FuentePrueba import FuentePrueba

PERGAMINO = "itm_pergamino"


class FuenteConObjetos(FuentePrueba):
    EXTRA = [
        {"id": PERGAMINO, "clase": "pergamino_retroceso", "nombre": "Pergamino de retroceso",
         "peso": 1, "valor": 50},
        {"id": "itm_armadura", "clase": "armadura", "nombre": "Cota", "peso": 8, "valor": 40,
         "defensa_bonus": 2},
    ]

    def __init__(self, **kw):
        FuentePrueba.__init__(self, **kw)
        self.contenidos[0]["objetos"].extend(["itm_armadura", "itm_pocion"])

    def ficha(self, tipoId):
        for f in self.EXTRA:
            if f["id"] == tipoId:
                return f
        return FuentePrueba.ficha(self, tipoId)


def nuevo(semilla=1, **kw):
    kw.setdefault("vidaJugador", 10000)
    fuente = FuenteConObjetos(**kw)
    modelo = Modelo(fuente, semilla, Inventario(fuente), Diario())
    modelo.iniciarPartida()
    for i in range(modelo.salas.cantidad()):
        modelo._asegurarContenido(modelo.salas.enPosicion(i))
    return modelo


_serie = [100000]


def darPergamino(m):
    """Mete un pergamino directo al inventario, sin diario (como si ya lo tuviera)."""
    _serie[0] += 1
    inv = m.inventario
    inv._enlazarDespues(Nodo(ObjetoInstancia(PERGAMINO, _serie[0])), inv.cola)


def cantidadPergaminos(m):
    n = 0
    for o in m.inventario.objetos():
        if o.tipoId == PERGAMINO:
            n += 1
    return n


def recoger(m, tipoId):
    for i in range(len(m.jugador.sala.objetos)):
        if m.jugador.sala.objetos[i].tipoId == tipoId:
            return m.ejecutar(Accion(ACC_RECOGER, i))
    raise AssertionError("no hay %s en el suelo" % tipoId)


def fotoCompleta(m):
    """Estado observable completo. Excluye pergaminos de retroceso y el cursor (no se revierten)."""
    salas = []
    for i in range(m.salas.cantidad()):
        sa = m.salas.enPosicion(i)
        salas.append((sa.id, sa.rastro,
                      [(e.instancia, e.vida, e.activo, e.vivo, e.sala.id, e.velocidad) for e in sa.enemigos],
                      [o.serie for o in sa.objetos if o.tipoId != PERGAMINO],
                      [(t.instancia, t.armada) for t in sa.trampas],
                      [(x.direccion, x.puerta.cerrada) for x in sa.salidas]))
    eventos = sorted([(e.tiempo, e.seq, e.tipo) for e in m.agenda.pendientesValidos()])
    j = m.jugador
    inv = m.inventario
    ev = m.eventoDecision
    return (m.reloj, m.estado, j.vida, j.sala.id, j.acciones, j.derrotados, j.velocidad,
            j.bonoAtaque, j.bonoDefensa, (ev.tiempo, ev.seq) if ev is not None else None,
            [e.instancia for e in m.enemigosVivos],
            [o.serie for o in inv.objetos() if o.tipoId != PERGAMINO],
            inv.arma.objeto.serie if inv.arma else None,
            inv.armadura.objeto.serie if inv.armadura else None,
            m.puertaSalidaAbierta, m.azar.getstate(), m.agenda.secuencia(), m.siguienteSerieObjeto,
            eventos, salas)


class PruebasInventario(unittest.TestCase):
    def testRecogerLlenoNoConsumeTiempo(self):
        m = nuevo()
        m.inventario.configurar(2)
        self.assertTrue(recoger(m, "itm_daga").ok)
        self.assertTrue(recoger(m, "itm_pocion").ok)
        reloj, acciones = m.reloj, m.jugador.acciones
        r = recoger(m, "itm_armadura")
        self.assertFalse(r.ok)
        self.assertEqual((m.reloj, m.jugador.acciones), (reloj, acciones))

    def testEquiparAlFrenteYReemplazo(self):
        m = nuevo()
        recoger(m, "itm_pocion")
        recoger(m, "itm_daga")
        m.ejecutar(Accion(ACC_EQUIPAR))                       # el cursor está en la poción
        self.assertFalse(m.ejecutar(Accion(ACC_EQUIPAR)).ok)  # una poción no se equipa
        m.ejecutar(Accion(ACC_SIGUIENTE))
        self.assertTrue(m.ejecutar(Accion(ACC_EQUIPAR)).ok)
        self.assertEqual(m.inventario.objetos()[0].tipoId, "itm_daga")
        self.assertEqual(m.jugador.bonoAtaque, 3)

    def testSoltarEquipadoQuitaBono(self):
        m = nuevo()
        recoger(m, "itm_daga")
        m.ejecutar(Accion(ACC_EQUIPAR))
        self.assertEqual(m.jugador.bonoAtaque, 3)
        m.ejecutar(Accion(ACC_SOLTAR))
        self.assertEqual(m.jugador.bonoAtaque, 0)
        self.assertEqual(m.inventario.tamano, 0)

    def testRecorridoCircularEnAmbosSentidos(self):
        m = nuevo()
        for t in ("itm_daga", "itm_pocion", "itm_armadura"):
            recoger(m, t)
        inv = m.inventario
        inicio = inv.actual()
        for _ in range(3):
            inv.avanzar()
        self.assertIs(inv.actual(), inicio)
        inv.retroceder()
        self.assertEqual(inv.actual().tipoId, "itm_armadura")

    def testVistaOrdenadaNoAlteraOrdenReal(self):
        m = nuevo()
        for t in ("itm_armadura", "itm_daga", "itm_pocion"):
            recoger(m, t)
        real = [o.serie for o in m.inventario.objetos()]
        porPeso = [m.nombreDe(o.tipoId) for o in m.inventario.vistaOrdenada("peso")]
        self.assertEqual(porPeso, ["Poción", "Daga", "Cota"])
        porNombre = [m.nombreDe(o.tipoId) for o in m.inventario.vistaOrdenada("nombre")]
        self.assertEqual(porNombre, ["Cota", "Daga", "Poción"])
        self.assertEqual([o.serie for o in m.inventario.objetos()], real)

    def testUsarPocionCuraSinSuperarMaximoYSeConsume(self):
        m = nuevo(vidaJugador=30)
        recoger(m, "itm_pocion")
        m.jugador.vida = 28
        m.ejecutar(Accion(ACC_USAR))
        self.assertEqual(m.jugador.vida, 30)
        self.assertEqual(m.inventario.tamano, 0)


class PruebasRetroceso(unittest.TestCase):
    def testSinPergaminoNoRetrocede(self):
        m = nuevo()
        m.ejecutar(Accion(ACC_ESPERAR))
        antes = fotoCompleta(m)
        self.assertFalse(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        self.assertEqual(fotoCompleta(m), antes)

    def testSinHistorialNoConsumePergamino(self):
        m = nuevo()
        darPergamino(m)
        self.assertFalse(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        self.assertEqual(cantidadPergaminos(m), 1)

    def _deshacerAccion(self, m, texto):
        antes = fotoCompleta(m)
        self.assertTrue(m.ejecutar(accionesDesdeTexto(texto)).ok, texto)
        self.assertNotEqual(fotoCompleta(m), antes)
        darPergamino(m)
        self.assertTrue(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        self.assertEqual(fotoCompleta(m), antes)

    def testEquiparSeDeshace(self):
        m = nuevo()
        recoger(m, "itm_pocion")
        recoger(m, "itm_daga")
        m.inventario.cursor = m.inventario.cola          # viendo la daga
        self._deshacerAccion(m, "equipar")

    def testSoltarSeDeshaceEnCualquierPosicion(self):
        m = nuevo()
        for t in ("itm_pocion", "itm_daga", "itm_armadura"):
            recoger(m, t)
        for _ in range(3):                                # medio, cabeza y cola
            self._deshacerAccion(m, "soltar")
            m.inventario.avanzar()

    def testSoltarEquipadoSeDeshaceConSuBono(self):
        m = nuevo()
        recoger(m, "itm_daga")
        m.ejecutar(Accion(ACC_EQUIPAR))
        self._deshacerAccion(m, "soltar")
        self.assertEqual(m.jugador.bonoAtaque, 3)

    def testUsarPocionSeDeshace(self):
        m = nuevo(vidaJugador=30)
        recoger(m, "itm_pocion")
        m.jugador.vida = 20
        self._deshacerAccion(m, "usar")
        self.assertEqual(m.jugador.vida, 20)

    def testRecogerSeDeshace(self):
        m = nuevo()
        self._deshacerAccion(m, "recoger 2")

    def testRetrocesoDeshaceCombateYAcciones(self):
        m = nuevo(enemigosPorSala=2)
        m.ejecutar(accionesDesdeTexto("mover E"))
        self._deshacerAccion(m, "esperar")
        self._deshacerAccion(m, "atacar 1")

    def testReversibilidadAleatoriaCompleta(self):
        opciones = ["mover N", "mover S", "mover E", "mover O", "esperar", "atacar 1", "atacar 2",
                    "recoger 1", "recoger 2", "recoger 3", "abrir E", "abrir S", "soltar",
                    "equipar", "usar", "sig", "ant", "esperar"]
        for semilla in (1, 2, 3, 4):
            m = nuevo(semilla=semilla, enemigosPorSala=2)
            azar = random.Random(semilla)
            deshechas = 0
            for _ in range(400):
                antes = fotoCompleta(m)
                n = m.jugador.acciones
                r = m.ejecutar(accionesDesdeTexto(azar.choice(opciones)))
                if r.ok and m.jugador.acciones > n and m.estado == EN_CURSO:
                    if azar.randrange(2) == 0:
                        darPergamino(m)
                        self.assertTrue(m.ejecutar(Accion(ACC_RETROCESO)).ok)
                        self.assertEqual(fotoCompleta(m), antes)
                        deshechas += 1
                if m.estado != EN_CURSO:
                    break
            self.assertGreater(deshechas, 20)

    def testRehacerDaLoMismoQueLaPrimeraVez(self):
        # Verifica que el estado del generador aleatorio y la secuencia se restauran (2.6)
        for semilla in range(1, 8):
            m = nuevo(semilla=semilla)
            for texto in ("mover E", "esperar", "esperar"):
                m.ejecutar(accionesDesdeTexto(texto))
            darPergamino(m)
            m.ejecutar(accionesDesdeTexto("atacar 1"))
            primera = (fotoCompleta(m), m.bitacora.ultimos()[-1])
            self.assertTrue(m.ejecutar(Accion(ACC_RETROCESO)).ok)
            m.ejecutar(accionesDesdeTexto("atacar 1"))
            self.assertEqual((fotoCompleta(m), m.bitacora.ultimos()[-1]), primera)

    def testLimiteDeCincoAcciones(self):
        m = nuevo()
        for _ in range(7):
            m.ejecutar(Accion(ACC_ESPERAR))
        for _ in range(5):
            darPergamino(m)
            self.assertTrue(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        darPergamino(m)
        self.assertFalse(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        self.assertEqual(cantidadPergaminos(m), 1)          # el sexto no se consumió

    def testDosPergaminosSeguidosRetroceden_DosAcciones(self):
        m = nuevo()
        inicial = fotoCompleta(m)
        m.ejecutar(Accion(ACC_ESPERAR))
        m.ejecutar(accionesDesdeTexto("mover E"))
        darPergamino(m)
        darPergamino(m)
        acciones = m.jugador.acciones
        self.assertTrue(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        self.assertTrue(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        self.assertEqual(m.jugador.acciones, acciones - 2)
        self.assertEqual(fotoCompleta(m), inicial)
        self.assertEqual(cantidadPergaminos(m), 0)

    def testPergaminoRecogidoEnElIntervaloNoSeDevuelveAlSuelo(self):
        m = nuevo()
        darPergamino(m)                                     # el que se va a gastar
        m.jugador.sala.objetos.append(ObjetoInstancia(PERGAMINO, 555))
        self.assertTrue(recoger(m, PERGAMINO).ok)
        self.assertEqual(cantidadPergaminos(m), 2)
        self.assertTrue(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        self.assertEqual(cantidadPergaminos(m), 1)          # 2 - 1 usado
        for o in m.jugador.sala.objetos:
            self.assertNotEqual(o.tipoId, PERGAMINO)

    def testPergaminoSoltadoEnElIntervaloSigueEnElSuelo(self):
        m = nuevo()
        darPergamino(m)
        darPergamino(m)
        m.inventario.cursor = m.inventario.cola
        self.assertTrue(m.ejecutar(Accion(ACC_SOLTAR)).ok)
        self.assertEqual(cantidadPergaminos(m), 1)
        self.assertTrue(m.ejecutar(Accion(ACC_RETROCESO)).ok)
        self.assertEqual(cantidadPergaminos(m), 0)          # 1 que quedaba - 1 usado
        suelo = 0
        for o in m.jugador.sala.objetos:
            if o.tipoId == PERGAMINO:
                suelo += 1
        self.assertEqual(suelo, 1)


if __name__ == "__main__":
    unittest.main()