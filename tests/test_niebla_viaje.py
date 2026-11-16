# Pruebas automatizadas de la Capacidad 2: Niebla de Guerra y Viaje Automático «ir a» (§3.3, §3.4, Apéndice B).
# Trazabilidad con requisitos FR-011 a FR-020.

import unittest
from model.Constantes import ACC_MOVER, ACC_ESPERAR, ACC_USAR, ACC_RETROCESO
from model.Acciones import Accion
from model.Entidades import Sala, Salida, Puerta, Jugador, Enemigo, ObjetoInstancia
from model.Salas import IndiceOrdenado
from model.Tabla import Tabla
from model.MapaConocido import MapaConocido, ESTADO_EXPLORADA, ESTADO_AVISTADA, ESTADO_DESCONOCIDA
from model.Dijkstra import dijkstraSubgrafoConocido, elegirPasoViajeAutomatico
from model.Juego import Modelo
from model.Inventario import Inventario
from model.Diario import Diario
from model.efectos import efectosJuego
from controller.ControladorJuego import Controlador


class ProveedorNiebla:
    def __init__(self, esqueleto, contenidos, fichas, datosGen=None):
        self._esqueleto = esqueleto
        self._contenidos = contenidos
        self._fichas = {f["id"]: f for f in fichas}
        self._datosGen = datosGen or {
            "sala_inicial": 1,
            "sala_salida": 99,
            "llave_salida": "llave_fin",
            "inventario_max": 10,
            "jugador": {"vida_max": 50, "ataque": 10, "defensa": 5, "velocidad": 100}
        }

    def datosGenerales(self):
        return self._datosGen

    def esqueleto(self):
        return self._esqueleto

    def contenidoSala(self, salaId):
        for c in self._contenidos:
            if c["sala"] == salaId:
                return c
        return {"sala": salaId, "enemigos": [], "objetos": [], "trampas": []}

    def ficha(self, tipoId):
        return self._fichas[tipoId]

    def fijarFichasEnUso(self, f):
        pass

    def anticipar(self, s):
        pass

    def asegurarFichas(self, ids):
        pass


class TestNieblaYViaje(unittest.TestCase):

    def test_T004_mapa_conocido_estados_iniciales(self):
        """[FR-011, FR-012] La sala inicial está explorada, sus vecinas avistadas, las demás desconocidas."""
        s1 = Sala(1, "Entrada")
        s2 = Sala(2, "Pasillo")
        s3 = Sala(3, "Cueva Lejana")

        p12 = Puerta(False, None, None)
        p23 = Puerta(False, None, None)

        s1.salidas.append(Salida("E", s1, 2, p12))
        s2.salidas.extend([Salida("O", s2, 1, p12), Salida("E", s2, 3, p23)])
        s3.salidas.append(Salida("O", s3, 2, p23))

        salas = IndiceOrdenado()
        salas.insertar(1, s1)
        salas.insertar(2, s2)
        salas.insertar(3, s3)

        mapa = MapaConocido()
        mapa.explorarSala(s1)

        self.assertEqual(mapa.estadoSala(1, salas), ESTADO_EXPLORADA)
        self.assertEqual(mapa.estadoSala(2, salas), ESTADO_AVISTADA)
        self.assertEqual(mapa.estadoSala(3, salas), ESTADO_DESCONOCIDA)

    def test_escenario_ir_a_sala_no_explorada_rechazada_sin_tiempo(self):
        """[FR-016, Apéndice B] ir a hacia una sala no explorada: se rechaza y no consume tiempo."""
        esqueleto = [
            {"id": 1, "nombre": "Sala 1", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "Sala 2", "salidas": {"O": {"sala": 1}, "E": {"sala": 3}}},
            {"id": 3, "nombre": "Sala 3", "salidas": {"O": {"sala": 2}}},
            {"id": 99, "nombre": "Salida", "salidas": {}}
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 2, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 99, "enemigos": [], "objetos": [], "trampas": []}
        ]
        fichas = []
        prov = ProveedorNiebla(esqueleto, contenidos, fichas)
        modelo = Modelo(prov, semilla=1, inventario=Inventario(prov), diario=Diario())
        controlador = Controlador(modelo)
        modelo.iniciarPartida()

        self.assertEqual(modelo.reloj, 0)
        self.assertEqual(modelo.jugador.sala.id, 1)

        # Sala 3 no está explorada
        mensajes = []
        controlador._decir = lambda m: mensajes.append(m)
        controlador.procesar("ir a 3")

        # No se movió y el reloj no avanzó
        self.assertEqual(modelo.jugador.sala.id, 1)
        self.assertEqual(modelo.reloj, 0)
        self.assertTrue(any("se rechaza y no consume tiempo" in m for m in mensajes))

    def test_escenario_antorcha_explora_vecinas_sin_activar_enemigos(self):
        """[FR-014, Apéndice B] Con la antorcha encendida, entrar a una sala explora sus vecinas
        sin activar sus enemigos ni sus trampas."""
        esqueleto = [
            {"id": 1, "nombre": "Inicio", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "Sala Antorcha", "salidas": {"O": {"sala": 1}, "E": {"sala": 3}}},
            {"id": 3, "nombre": "Guarida", "salidas": {"O": {"sala": 2}}},
            {"id": 99, "nombre": "Salida", "salidas": {}}
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 2, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 3, "enemigos": [{"instancia": "e-1", "tipo": "ent_rata", "vida": 10}],
             "objetos": [], "trampas": [{"instancia": "t-1", "tipo": "trp_dardos"}]},
            {"sala": 99, "enemigos": [], "objetos": [], "trampas": []}
        ]
        fichas = [
            {"id": "ent_rata", "clase": "enemigo", "nombre": "Rata", "vida_max": 10, "ataque": 2, "defensa": 0, "velocidad": 100, "comportamiento": "guardian", "suelta": []},
            {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos", "daño": 5, "rearme": 300}
        ]
        prov = ProveedorNiebla(esqueleto, contenidos, fichas)
        efectos = efectosJuego()
        modelo = Modelo(prov, semilla=1, inventario=Inventario(prov), diario=Diario(), efectos=efectos)
        efectos.registrarEn(modelo)
        modelo.iniciarPartida()

        # Encender antorcha en el jugador
        efectos.encenderAntorcha(modelo, modelo.jugador, 500)

        # Moverse a sala 2 con antorcha encendida
        modelo.ejecutar(Accion(ACC_MOVER, "E"))
        self.assertEqual(modelo.jugador.sala.id, 2)

        # Sala 3 debe estar Explorada gracias a la antorcha
        self.assertTrue(modelo.mapaConocido.estaExplorada(3))

        # Pero los enemigos de sala 3 NO deben estar activos
        sala3 = modelo.salas.buscar(3)
        for e in sala3.enemigos:
            self.assertFalse(e.activo)

    def test_escenario_pergamino_revierte_exploracion_antorcha(self):
        """[FR-015, Apéndice B] Un pergamino revierte una entrada con antorcha encendida:
        las salas exploradas por la antorcha vuelven a su estado anterior."""
        esqueleto = [
            {"id": 1, "nombre": "Inicio", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "Sala Central", "salidas": {"O": {"sala": 1}, "E": {"sala": 3}}},
            {"id": 3, "nombre": "Cueva", "salidas": {"O": {"sala": 2}}},
            {"id": 99, "nombre": "Salida", "salidas": {}}
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": ["itm_pergamino"], "trampas": []},
            {"sala": 2, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 99, "enemigos": [], "objetos": [], "trampas": []}
        ]
        fichas = [
            {"id": "itm_pergamino", "clase": "pergamino_retroceso", "nombre": "Pergamino", "peso": 1, "valor": 10}
        ]
        prov = ProveedorNiebla(esqueleto, contenidos, fichas)
        efectos = efectosJuego()
        modelo = Modelo(prov, semilla=1, inventario=Inventario(prov), diario=Diario(), efectos=efectos)
        efectos.registrarEn(modelo)
        modelo.iniciarPartida()

        # Recoger el pergamino
        modelo.inventario.configurar(10)
        modelo.inventario._recoger(modelo, 0)
        self.assertIsNotNone(modelo.inventario.buscarPergamino())

        # Encender antorcha
        efectos.encenderAntorcha(modelo, modelo.jugador, 500)

        # Sala 3 NO está explorada
        self.assertFalse(modelo.mapaConocido.estaExplorada(3))

        # Entrar a sala 2
        modelo.ejecutar(Accion(ACC_MOVER, "E"))
        self.assertEqual(modelo.jugador.sala.id, 2)
        self.assertTrue(modelo.mapaConocido.estaExplorada(3))

        # Usar pergamino de retroceso
        res = modelo.ejecutar(Accion(ACC_RETROCESO))
        self.assertTrue(res.ok)
        self.assertEqual(modelo.jugador.sala.id, 1)

        # Sala 3 vuelve a NO estar explorada
        self.assertFalse(modelo.mapaConocido.estaExplorada(3))

    def test_escenario_ir_a_se_detiene_ante_enemigos_dormidos(self):
        """[FR-018, Apéndice B] ir a entra a una sala con enemigos dormidos:
        los enemigos se activan según P1 §2.4 y el viaje se detiene."""
        esqueleto = [
            {"id": 1, "nombre": "Sala 1", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "Sala 2", "salidas": {"O": {"sala": 1}, "E": {"sala": 3}}},
            {"id": 3, "nombre": "Sala 3", "salidas": {"O": {"sala": 2}}},
            {"id": 99, "nombre": "Salida", "salidas": {}}
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 2, "enemigos": [{"instancia": "e-1", "tipo": "ent_rata", "vida": 10}],
             "objetos": [], "trampas": []},
            {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 99, "enemigos": [], "objetos": [], "trampas": []}
        ]
        fichas = [
            {"id": "ent_rata", "clase": "enemigo", "nombre": "Rata", "vida_max": 10, "ataque": 2, "defensa": 0, "velocidad": 100, "comportamiento": "guardian", "suelta": []}
        ]
        prov = ProveedorNiebla(esqueleto, contenidos, fichas)
        modelo = Modelo(prov, semilla=1, inventario=Inventario(prov), diario=Diario())
        controlador = Controlador(modelo)
        modelo.iniciarPartida()

        # Marcamos sala 3 como explorada artificialmente para que sea destino válido
        modelo.mapaConocido.explorarSala(modelo.salas.buscar(2))
        modelo.mapaConocido.explorarSala(modelo.salas.buscar(3))

        mensajes = []
        controlador._decir = lambda m: mensajes.append(m)

        # Ejecutamos ir a 3: debe avanzar de 1 a 2, y en 2 detenerse por los enemigos
        controlador.procesar("ir a 3")

        self.assertEqual(modelo.jugador.sala.id, 2)
        # El viaje se detuvo en la sala 2 y no continuó a la 3
        self.assertTrue(any("contiene enemigos" in m for m in mensajes))
        # El enemigo de sala 2 fue despertado al entrar
        enemigo = modelo.jugador.sala.enemigos[0]
        self.assertTrue(enemigo.activo)

    def test_escenario_memoria_puerta_cerrada_actualizacion_y_recalculo(self):
        """[FR-013, FR-017, Apéndice B] El mapa recuerda abierta una puerta que en realidad está cerrada:
        al observarla, el mapa se actualiza y la ruta se recalcula; si no queda ruta,
        el viaje se detiene sin consumir tiempo adicional."""
        esqueleto = [
            {"id": 1, "nombre": "Sala 1", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "Sala 2", "salidas": {"O": {"sala": 1}, "E": {"sala": 3}}},
            {"id": 3, "nombre": "Sala 3", "salidas": {"O": {"sala": 2}}},
            {"id": 99, "nombre": "Salida", "salidas": {}}
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 2, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 99, "enemigos": [], "objetos": [], "trampas": []}
        ]
        prov = ProveedorNiebla(esqueleto, contenidos, [])
        modelo = Modelo(prov, semilla=1, inventario=Inventario(prov), diario=Diario())
        controlador = Controlador(modelo)
        modelo.iniciarPartida()

        # Las tres salas exploradas
        modelo.mapaConocido.explorarSala(modelo.salas.buscar(2))
        modelo.mapaConocido.explorarSala(modelo.salas.buscar(3))

        # La puerta entre 2 y 3 se cierra en la realidad mientras el jugador está en 1
        puerta23 = modelo.salas.buscar(2).salida("E").puerta
        puerta23.cerrada = True

        # El mapa del jugador en sala 1 todavía recuerda que la puerta 2-3 estaba abierta
        self.assertTrue(modelo.mapaConocido.puertaRecordadaAbierta(2, 3, puerta23))

        mensajes = []
        controlador._decir = lambda m: mensajes.append(m)

        # El jugador inicia "ir a 3"
        # Paso 1: se mueve de 1 a 2.
        # En sala 2: observa que la puerta a sala 3 está cerrada.
        # Recalcula: no hay más rutas a 3.
        # Se detiene en sala 2 sin tiempo adicional.
        controlador.procesar("ir a 3")

        self.assertEqual(modelo.jugador.sala.id, 2)
        self.assertTrue(modelo.mapaConocido.puertaRecordadaCerrada(2, 3, puerta23))
        self.assertTrue(any("no existe ruta conocida abierta" in m for m in mensajes))


if __name__ == "__main__":
    unittest.main()
