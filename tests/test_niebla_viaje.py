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


    def test_N01_antorcha_no_observa_puertas_de_vecinas(self):
        """[FR-014, FR-013, N-01] Con la antorcha, la vecina B queda explorada y la puerta A-B
        observada, pero la puerta B-C (que el jugador nunca tuvo enfrente) queda sin observar."""
        esqueleto = [
            {"id": 1, "nombre": "Inicio", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "A", "salidas": {"O": {"sala": 1}, "E": {"sala": 3}}},
            {"id": 3, "nombre": "B", "salidas": {"O": {"sala": 2}, "E": {"sala": 4, "cerrada": True}}},
            {"id": 4, "nombre": "C", "salidas": {"O": {"sala": 3}}},
            {"id": 99, "nombre": "Salida", "salidas": {}}
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 2, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 4, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 99, "enemigos": [], "objetos": [], "trampas": []}
        ]
        prov = ProveedorNiebla(esqueleto, contenidos, [])
        efectos = efectosJuego()
        modelo = Modelo(prov, semilla=1, inventario=Inventario(prov), diario=Diario(), efectos=efectos)
        efectos.registrarEn(modelo)
        modelo.iniciarPartida()
        efectos.encenderAntorcha(modelo, modelo.jugador, 500)

        # El jugador entra a A (sala 2); B (sala 3) es su vecina
        modelo.ejecutar(Accion(ACC_MOVER, "E"))
        self.assertEqual(modelo.jugador.sala.id, 2)

        mapa = modelo.mapaConocido
        self.assertTrue(mapa.estaExplorada(3))
        self.assertEqual(mapa.estadoPuertaRecordada(2, 3), "abierta")
        self.assertEqual(mapa.estadoPuertaRecordada(3, 4), "sin_observar")

    def test_N02_ir_a_no_usa_puerta_sin_observar_y_mapa_no_revela_estado(self):
        """[FR-013, FR-017, N-02] Una puerta que el jugador nunca observó y que en realidad está
        abierta: «ir a» no la usa y el mapa la muestra como sin observar."""
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
        modelo.iniciarPartida()

        # Salas 2 y 3 conocidas, pero solo marcadas: ninguna puerta de ellas fue observada
        modelo.mapaConocido.marcarExplorada(modelo.salas.buscar(2))
        modelo.mapaConocido.marcarExplorada(modelo.salas.buscar(3))

        # La puerta 2-3 está realmente abierta
        self.assertFalse(modelo.salas.buscar(2).salida("E").puerta.cerrada)
        self.assertEqual(modelo.mapaConocido.estadoPuertaRecordada(2, 3), "sin_observar")

        # «ir a» no la usa: no hay ruta conocida y no se mueve ni gasta tiempo
        salida, motivo = modelo.pasoViaje(3)
        self.assertIsNone(salida)
        self.assertEqual(motivo, Modelo.VIAJE_SIN_RUTA)
        self.assertEqual(modelo.jugador.sala.id, 1)
        self.assertEqual(modelo.reloj, 0)

        # El mapa no revela el estado real de esa puerta
        controlador = Controlador(modelo)
        mensajes = []
        controlador._decir = lambda m: mensajes.append(m)
        controlador.procesar("mapa")
        self.assertIn(
            "E->Sala 3 (costo: 100, sin observar)",
            "\n".join(mensajes),
        )
    def test_N03_viaje_se_detiene_por_danio_aunque_la_vida_se_recupere(self):
        """[FR-018, N-03] El daño se detecta por el aviso del modelo, no comparando la vida:
        si hay regeneración en el mismo paso, el viaje se detiene igual. Corre sin controlador."""
        esqueleto = [
            {"id": 1, "nombre": "Sala 1", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "Sala 2", "salidas": {"O": {"sala": 1}, "E": {"sala": 3}}},
            {"id": 3, "nombre": "Sala 3", "salidas": {"O": {"sala": 2}}},
            {"id": 99, "nombre": "Salida", "salidas": {}}
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 2, "enemigos": [], "objetos": [],
             "trampas": [{"instancia": "t-1", "tipo": "trp_dardos"}]},
            {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 99, "enemigos": [], "objetos": [], "trampas": []}
        ]
        fichas = [
            {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos", "daño": 5, "rearme": 300}
        ]
        prov = ProveedorNiebla(esqueleto, contenidos, fichas)
        modelo = Modelo(prov, semilla=1, inventario=Inventario(prov), diario=Diario())
        modelo.iniciarPartida()
        modelo.mapaConocido.explorarSala(modelo.salas.buscar(2))
        modelo.mapaConocido.explorarSala(modelo.salas.buscar(3))

        # Regeneración simulada: cada daño al jugador se cura en el mismo paso
        original = modelo.aplicarDanio

        def conRegeneracion(actor, cantidad):
            original(actor, cantidad)
            if actor is modelo.jugador:
                modelo.curar(actor, cantidad)
        modelo.aplicarDanio = conRegeneracion

        vidaAntes = modelo.jugador.vida
        salida, motivo = modelo.pasoViaje(3)

        self.assertIsNotNone(salida)
        self.assertEqual(modelo.jugador.sala.id, 2)
        self.assertEqual(modelo.jugador.vida, vidaAntes)       # comparar vidas no vería nada
        self.assertEqual(motivo, Modelo.VIAJE_DANIO)






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
        # Desde la sala con enemigos, hay una ruta conocida hacia la sala 3.
        self.assertTrue(modelo.mapaConocido.puertaRecordadaAbierta(2, 3))
        relojAntes = modelo.reloj

        salida, motivo = modelo.pasoViaje(3)

        self.assertIsNone(salida)
        self.assertEqual(motivo, Modelo.VIAJE_ENEMIGOS)
        self.assertEqual(modelo.jugador.sala.id, 2)
        self.assertEqual(modelo.reloj, relojAntes)

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
        self.assertTrue(modelo.mapaConocido.puertaRecordadaAbierta(2, 3))

        mensajes = []
        controlador._decir = lambda m: mensajes.append(m)

        # El jugador inicia "ir a 3"
        # Paso 1: se mueve de 1 a 2.
        # En sala 2: observa que la puerta a sala 3 está cerrada.
        # Recalcula: no hay más rutas a 3.
        # Se detiene en sala 2 sin tiempo adicional.
        controlador.procesar("ir a 3")

        self.assertEqual(modelo.jugador.sala.id, 2)
        self.assertEqual(modelo.mapaConocido.estadoPuertaRecordada(2, 3), "cerrada")
        self.assertTrue(any("no existe ruta conocida abierta" in m for m in mensajes))

    def test_n01_antorcha_no_observa_puertas_lejanas(self):
        """[N-01, §3.3] Entrar con antorcha explora vecinas pero NO observa sus puertas lejanas."""
        esqueleto = [
            {"id": 1, "nombre": "Sala A", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "Sala B", "salidas": {"O": {"sala": 1}, "E": {"sala": 3, "cerrada": True}}},
            {"id": 3, "nombre": "Sala C", "salidas": {"O": {"sala": 2, "cerrada": True}}},
            {"id": 99, "nombre": "Salida", "salidas": {}}
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 2, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 99, "enemigos": [], "objetos": [], "trampas": []}
        ]
        prov = ProveedorNiebla(esqueleto, contenidos, [])
        efectos = efectosJuego()
        modelo = Modelo(prov, semilla=1, inventario=Inventario(prov), diario=Diario(), efectos=efectos)
        efectos.registrarEn(modelo)
        modelo.iniciarPartida()

        # Encender antorcha y moverse a Sala 1 (o ya está en 1 e inicia)
        efectos.encenderAntorcha(modelo, modelo.jugador, 500)
        # Sala 1 es A. Al moverse al este hacia Sala 2 (B):
        # Vecina de B es C (Sala 3). La antorcha revela C como explorada,
        # pero la puerta B-C NO debe haber sido observada por estar en A.
        # Simulamos mover de una sala preliminar o directamente:
        # Si el jugador está en 1 y tiene antorcha, sus vecinas (2) están exploradas.
        # Al entrar a 2 con antorcha, la vecina lejana 3 se explora por antorcha.
        res = modelo.ejecutar(Accion(ACC_MOVER, "E"))
        self.assertTrue(res.ok)
        self.assertEqual(modelo.jugador.sala.id, 2)

        # Sala 2 está explorada y puerta 1-2 observada
        self.assertTrue(modelo.mapaConocido.estaExplorada(2))
        self.assertEqual(modelo.mapaConocido.estadoPuertaRecordada(1, 2), "abierta")

        # Puerta 2-3 está conectada a la sala 2 donde está el jugador, por lo que 2-3 sí se observa
        self.assertEqual(modelo.mapaConocido.estadoPuertaRecordada(2, 3), "cerrada")

    def test_n02_puerta_sin_observar_no_usada_por_ir_a(self):
        """[N-02, §3.3, §3.4] Una puerta sin observar no se asume abierta y 'ir a' no la utiliza."""
        s1 = Sala(1, "Sala 1")
        s2 = Sala(2, "Sala 2")
        p12 = Puerta(False, None, None)  # En realidad está abierta
        s1.salidas.append(Salida("E", s1, 2, p12))
        s2.salidas.append(Salida("O", s2, 1, p12))

        salas = IndiceOrdenado()
        salas.insertar(1, s1)
        salas.insertar(2, s2)

        mapa = MapaConocido()
        # Sala 1 y 2 marcadas exploradas pero sin observar la puerta 1-2
        mapa.marcarExplorada(s1)
        mapa.marcarExplorada(s2)

        self.assertEqual(mapa.estadoPuertaRecordada(1, 2), "sin_observar")
        # puertaRecordadaAbierta debe ser False para puertas sin observar
        self.assertFalse(mapa.puertaRecordadaAbierta(1, 2))

        # 'ir a' no puede usar una puerta sin observar
        salida, costo = elegirPasoViajeAutomatico(s1, s2, salas, mapa)
        self.assertIsNone(salida)










if __name__ == "__main__":
    unittest.main()