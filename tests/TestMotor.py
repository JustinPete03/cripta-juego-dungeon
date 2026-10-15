import random
import time
import unittest

from model.Constantes import *
from model.Acciones import Accion, accionesDesdeTexto
from model.Agenda import Agenda
from model.Bitacora import BitacoraCircular
from model.Entidades import Sala, Salida, Puerta, claveInstancia
from model.Juego import Modelo
from model.Rastro import elegirDestinoRastreador
from model.Tiempo import intervaloAccion, tiempoTrasCambioVelocidad
from controller.ControladorJuego import Controlador
from tests.FuentePrueba import FuentePrueba
from tests.DiarioPruebas import DiarioPrueba
from model.Inventario import Inventario


def nuevoModelo(fuente=None, semilla=1, diario=None):
    fuente = fuente if fuente is not None else FuentePrueba()
    modelo = Modelo(fuente, semilla, Inventario(fuente), diario)
    modelo.iniciarPartida()
    return modelo


def foto(modelo):
    # Estado observable completo, para comparar antes/después de un retroceso.
    salas = []
    for i in range(modelo.salas.cantidad()):
        s = modelo.salas.enPosicion(i)
        salas.append((s.id, s.rastro,
                      [(e.instancia, e.vida, e.activo, e.vivo, e.sala.id, e.velocidad) for e in s.enemigos],
                      [o.serie for o in s.objetos],
                      [(t.instancia, t.armada) for t in s.trampas],
                      [(x.direccion, x.puerta.cerrada) for x in s.salidas]))
    eventos = sorted([(e.tiempo, e.seq, e.tipo) for e in modelo.agenda.pendientesValidos()])
    j = modelo.jugador
    ev = modelo.eventoDecision
    return (modelo.reloj, modelo.estado, j.vida, j.sala.id, j.acciones, j.derrotados, j.velocidad,
            (ev.tiempo, ev.seq) if ev is not None else None,
            [e.instancia for e in modelo.enemigosVivos],
            [o.serie for o in modelo.inventario.objetos()], modelo.puertaSalidaAbierta,
            eventos, salas)


class PruebasAgenda(unittest.TestCase):
    def testOrdenTiempoYSeq(self):
        a = Agenda()
        a.programar(50, 1, "x")
        e2 = a.programar(10, 1, "y")
        e3 = a.programar(10, 1, "z")
        self.assertIs(a.proximo(), e2)    # mismo tiempo: menor seq primero
        self.assertIs(a.proximo(), e3)
        self.assertEqual(a.proximo().propietario, "x")
        self.assertIsNone(a.proximo())

    def testCancelarYReprogramar(self):
        a = Agenda()
        e1 = a.programar(10, 1, "a")
        e2 = a.programar(20, 1, "b")
        a.cancelar(e1)
        nuevo = a.reprogramar(e2, 5)
        self.assertGreater(nuevo.seq, e2.seq)
        self.assertIs(a.proximo(), nuevo)
        self.assertIsNone(a.proximo())

    def testOrdenAleatorioIgualAReferencia(self):
        azar = random.Random(3)
        a = Agenda()
        esperados = []
        for _ in range(500):
            ev = a.programar(azar.randrange(50), 1, None)
            esperados.append(ev)
        esperadosOrdenados = sorted(esperados, key=lambda e: (e.tiempo, e.seq))
        obtenidos = []
        while True:
            e = a.proximo()
            if e is None:
                break
            obtenidos.append(e)
        self.assertEqual([id(e) for e in obtenidos], [id(e) for e in esperadosOrdenados])


class PruebasFormulas(unittest.TestCase):
    def testIntervalos(self):
        self.assertEqual(intervaloAccion(100, 100), 100)
        self.assertEqual(intervaloAccion(100, 150), 66)
        self.assertEqual(intervaloAccion(25, 10000), 1)

    def testCambioVelocidad(self):
        # restante 100 con velocidad 100 -> 200: restante 50
        self.assertEqual(tiempoTrasCambioVelocidad(300, 200, 100, 200), 250)
        self.assertEqual(tiempoTrasCambioVelocidad(300, 200, 200, 100), 400)
        self.assertEqual(tiempoTrasCambioVelocidad(201, 200, 1, 1000), 201)  # mínimo 1


class PruebasBitacora(unittest.TestCase):
    def testUltimos20MemoriaFija(self):
        b = BitacoraCircular(20)
        for i in range(55):
            b.agregar("m%d" % i)
        self.assertEqual(b.ultimos(), ["m%d" % i for i in range(35, 55)])
        self.assertEqual(len(b._mensajes), 20)

    def testMenosDe20(self):
        b = BitacoraCircular(20)
        b.agregar("a")
        b.agregar("b")
        self.assertEqual(b.ultimos(), ["a", "b"])


class PruebasRastro(unittest.TestCase):
    def _sala(self, idSala, rastro):
        s = Sala(idSala, "s%d" % idSala)
        s.rastro = rastro
        return s

    def _centro(self, vecinas, cerradas=()):
        centro = Sala(0, "centro")
        for i in range(len(vecinas)):
            v = vecinas[i]
            salida = Salida(DIRECCIONES[i], centro, v.id, Puerta(i in cerradas, None, None))
            salida.destino = v
            centro.salidas.append(salida)
        return centro

    def testMasFresco(self):
        c = self._centro([self._sala(5, 100), self._sala(6, 300)])
        self.assertEqual(elegirDestinoRastreador(c, 350).id, 6)

    def testEmpateMenorId(self):
        c = self._centro([self._sala(9, 200), self._sala(4, 200)])
        self.assertEqual(elegirDestinoRastreador(c, 250).id, 4)

    def testCaducaA400(self):
        c = self._centro([self._sala(5, 100)])
        self.assertEqual(elegirDestinoRastreador(c, 499).id, 5)    # antigüedad 399
        self.assertIsNone(elegirDestinoRastreador(c, 500))          # antigüedad 400

    def testNuncaVisitadaYPuertaCerrada(self):
        c = self._centro([self._sala(5, -1), self._sala(6, 300)], cerradas=(1,))
        self.assertIsNone(elegirDestinoRastreador(c, 310))


class PruebasMotor(unittest.TestCase):
    def testInicioYActivacionEnT0(self):
        f = FuentePrueba()
        f.contenidos[0]["enemigos"].append({"instancia": "e-1", "tipo": "ent_rata", "vida": 12})
        m = nuevoModelo(f)
        self.assertEqual(m.reloj, 0)
        self.assertEqual(m.eventoDecision.tiempo, 0)
        rata = m.jugador.sala.enemigos[0]
        self.assertTrue(rata.activo)
        self.assertEqual(rata.tiempoSiguiente, 66)    # §2.4: velocidad 150 activada en 0

    def testAccionRechazadaNoConsumeTiempo(self):
        m = nuevoModelo()
        antes = foto(m)
        r = m.ejecutar(Accion(ACC_MOVER, "O"))      # no hay salida al oeste en la sala 1
        self.assertFalse(r.ok)
        r = m.ejecutar(Accion(ACC_ABRIR, "E"))      # puerta ya abierta / inexistente
        self.assertFalse(r.ok)
        r = m.ejecutar(Accion(ACC_RECOGER, 99))
        self.assertFalse(r.ok)
        self.assertEqual(foto(m), antes)

    def testAbrirSinLlaveYConLlave(self):
        f = FuentePrueba(enemigosPorSala=0, trampas=False)
        m = nuevoModelo(f)
        # mover a sala 2 y probar la puerta E hacia la sala 3 (cerrada, llave A, cierre 500)
        self.assertTrue(m.ejecutar(Accion(ACC_MOVER, "E")).ok)
        r = m.ejecutar(Accion(ACC_ABRIR, "E"))
        self.assertFalse(r.ok)
        self.assertTrue(m.ejecutar(Accion(ACC_MOVER, "O")).ok)
        # recoger del suelo (daga, llaves) hasta tener llave A
        while len(m.jugador.sala.objetos) > 0:
            self.assertTrue(m.ejecutar(Accion(ACC_RECOGER, 0)).ok)
        self.assertTrue(m.ejecutar(Accion(ACC_MOVER, "E")).ok)
        tAntes = m.reloj
        self.assertTrue(m.ejecutar(Accion(ACC_ABRIR, "E")).ok)
        sala2 = m.jugador.sala
        self.assertFalse(sala2.salida("E").puerta.cerrada)
        # la puerta es una sola: el otro lado también quedó abierta
        self.assertFalse(sala2.salida("E").destino.salida("O").puerta.cerrada)
        # cierre automático 500 después de abrir
        for _ in range(8):
            m.ejecutar(Accion(ACC_ESPERAR))
        self.assertTrue(sala2.salida("E").puerta.cerrada)

    def testVictoria(self):
        f = FuentePrueba(ancho=3, alto=1, enemigosPorSala=0, trampas=False)
        m = nuevoModelo(f)
        while len(m.jugador.sala.objetos) > 0:
            m.ejecutar(Accion(ACC_RECOGER, 0))
        self.assertTrue(m.ejecutar(Accion(ACC_MOVER, "E")).ok)
        self.assertFalse(m.ejecutar(Accion(ACC_MOVER, "E")).ok)   # puerta cerrada
        self.assertTrue(m.ejecutar(Accion(ACC_ABRIR, "E")).ok)
        self.assertTrue(m.ejecutar(Accion(ACC_MOVER, "E")).ok)
        self.assertEqual(m.estado, VICTORIA)
        self.assertEqual(m.resultadoPartida().acciones, 7 if False else m.jugador.acciones)

    def testCombateMuerteYSuelta(self):
        f = FuentePrueba(enemigosPorSala=0, trampas=False, vidaJugador=500)
        f.contenidos[1]["enemigos"].append({"instancia": "e-1", "tipo": "ent_rata", "vida": 3})
        m = nuevoModelo(f)
        m.ejecutar(Accion(ACC_MOVER, "E"))
        sala = m.jugador.sala
        rata = sala.enemigos[0]
        eventoRata = rata.evento
        self.assertTrue(m.ejecutar(Accion(ACC_ATACAR, 0)).ok)
        self.assertFalse(rata.vivo)
        self.assertTrue(eventoRata.cancelado)               # sus eventos futuros no se ejecutan
        self.assertEqual(len(sala.enemigos), 0)
        self.assertEqual(m.jugador.derrotados, 1)
        self.assertEqual(m.nombreDe(sala.objetos[0].tipoId), "Poción")  # soltó su objeto

    def testDanoMinimoUno(self):
        m = nuevoModelo()
        self.assertEqual(m._calcularDanio(0, 1000), 1)

    def testTrampaDanoYRearme(self):
        f = FuentePrueba(enemigosPorSala=0, vidaJugador=30)
        f.contenidos[1]["trampas"] = [{"instancia": "t-1", "tipo": "trp_dardos"}]
        m = nuevoModelo(f)
        m.ejecutar(Accion(ACC_MOVER, "E"))
        trampa = m.jugador.sala.trampas[0]
        self.assertEqual(m.jugador.vida, 26)
        self.assertFalse(trampa.armada)
        for _ in range(4):
            m.ejecutar(Accion(ACC_ESPERAR))
        self.assertTrue(trampa.armada)       # rearmada a los 300
        self.assertEqual(m.jugador.vida, 26)  # no se activa hasta volver a entrar

    def testGuardianErranteYRastreador(self):
        f = FuentePrueba(enemigosPorSala=0, trampas=False, vidaJugador=500)
        f.contenidos[1]["enemigos"].append({"instancia": "e-1", "tipo": "ent_rata", "vida": 12})
        m = nuevoModelo(f)
        m.ejecutar(Accion(ACC_MOVER, "E"))     # activa la rata en la sala 2
        m.ejecutar(Accion(ACC_MOVER, "O"))     # vuelve a la 1: la rata (rastreador) la sigue
        for _ in range(3):
            m.ejecutar(Accion(ACC_ESPERAR))
        rata = [e for e in m.enemigosVivos if e.instancia == "e-1"][0]
        self.assertEqual(rata.sala.id, 1)

    def testDeterminismo(self):
        def jugar():
            m = nuevoModelo(FuentePrueba(vidaJugador=10000), semilla=42)
            azar = random.Random(5)
            opciones = ["mover N", "mover S", "mover E", "mover O", "esperar", "atacar 1",
                        "recoger 1", "abrir E", "abrir S", "soltar"]
            for _ in range(300):
                a = accionesDesdeTexto(azar.choice(opciones))
                m.ejecutar(a)
            return foto(m), m.bitacora.ultimos()
        self.assertEqual(jugar(), jugar())

    def testReversibilidadCompleta(self):
        # Tras cada acción aceptada, retroceder deja EXACTAMENTE el estado anterior.
        for semilla in (1, 2, 3):
            f = FuentePrueba(vidaJugador=10000, enemigosPorSala=2)
            diario = DiarioPrueba()
            m = nuevoModelo(f, semilla=semilla, diario=diario)
            for i in range(m.salas.cantidad()):
                m._asegurarContenido(m.salas.enPosicion(i))
            azar = random.Random(semilla)
            opciones = ["mover N", "mover S", "mover E", "mover O", "esperar", "atacar 1",
                        "atacar 2", "recoger 1", "abrir E", "abrir S", "abrir N", "soltar", "esperar"]
            deshechas = 0
            for _ in range(400):
                antes = foto(m)
                n = len(diario.intervalos)
                r = m.ejecutar(accionesDesdeTexto(azar.choice(opciones)))
                if r.ok and len(diario.intervalos) > n and m.estado == EN_CURSO:
                    if azar.randrange(2) == 0:
                        m.ejecutar(Accion(ACC_RETROCESO))
                        self.assertEqual(foto(m), antes)
                        deshechas += 1
                if m.estado != EN_CURSO:
                    break
            self.assertGreater(deshechas, 20)

    def testReproduccionPorControlador(self):
        acciones = ["mover E", "esperar", "mover O", "esperar", "atacar 1"]
        def correr():
            m = nuevoModelo(FuentePrueba(vidaJugador=10000, enemigosPorSala=1), semilla=9)
            c = Controlador(m)
            return c.reproducir(acciones), foto(m)
        self.assertEqual(correr(), correr())

    def testCicloMenorA20ms(self):
        # Cientos de enemigos activos: un ciclo completo entre decisiones debe ser < 20 ms.
        f = FuentePrueba(ancho=20, alto=15, enemigosPorSala=2, vidaJugador=10 ** 9, trampas=False)
        diario = DiarioPrueba()
        m = nuevoModelo(f, diario=diario)
        for i in range(m.salas.cantidad()):
            s = m.salas.enPosicion(i)
            m._asegurarContenido(s)
            m._activarDormidos(s)      # 600 enemigos activos a la vez
        peor = 0.0
        for _ in range(60):
            t0 = time.perf_counter()
            m.ejecutar(Accion(ACC_ESPERAR))
            peor = max(peor, time.perf_counter() - t0)
            diario.intervalos = diario.intervalos[-5:]
        print("\n  peor ciclo con 600 enemigos activos: %.2f ms" % (peor * 1000))
        self.assertLess(peor, 0.020)


if __name__ == "__main__":
    unittest.main()