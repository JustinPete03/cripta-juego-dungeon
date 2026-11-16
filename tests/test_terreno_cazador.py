# Pruebas automatizadas de la Capacidad 1: Terreno y Cazador (§3.1, §3.2, Apéndice B).
# Trazabilidad con requisitos FR-001 a FR-010.

import unittest
from model.Constantes import ACC_MOVER, ACC_ESPERAR
from model.Acciones import Accion
from model.Entidades import Sala, Salida, Puerta, Jugador, Enemigo
from model.Salas import IndiceOrdenado
from model.Tabla import Tabla
from model.Dijkstra import MinHeapDijkstra, dijkstraDesde
from model.Cazador import elegirPasoCazador
from model.Juego import Modelo
from model.Tiempo import intervaloAccion, tiempoTrasCambioVelocidad
from model.Inventario import Inventario
from model.Diario import Diario


class ProveedorSintetico:
    """Proveedor mínimo en memoria para construir escenarios exactos de prueba."""

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

    def fijarFichasEnUso(self, funcion):
        pass

    def anticipar(self, salaId):
        pass

    def asegurarFichas(self, ids):
        pass


class TestTerrenoYCazador(unittest.TestCase):

    def test_T010_monticulo_dijkstra_orden_y_extraccion(self):
        """[FR-005] Prueba unitaria del montículo binario propio MinHeapDijkstra."""
        heap = MinHeapDijkstra()
        self.assertTrue(heap.estaVacio())

        heap.empujar(50, 1)
        heap.empujar(20, 2)
        heap.empujar(100, 3)
        heap.empujar(10, 4)
        heap.empujar(30, 5)

        self.assertEqual(len(heap), 5)
        self.assertEqual(heap.extraerMin(), (10, 4))
        self.assertEqual(heap.extraerMin(), (20, 2))
        self.assertEqual(heap.extraerMin(), (30, 5))
        self.assertEqual(heap.extraerMin(), (50, 1))
        self.assertEqual(heap.extraerMin(), (100, 3))
        self.assertTrue(heap.estaVacio())

    def test_T010_dijkstra_grafo_lineal_con_pesos(self):
        """[FR-005] Dijkstra calcula distancias mínimas considerando pesos no uniformes."""
        # 1 --(costo 10)--> 2 --(costo 20)--> 3
        s1 = Sala(1, "Sala 1")
        s2 = Sala(2, "Sala 2")
        s3 = Sala(3, "Sala 3")

        p12 = Puerta(False, None, None)
        p23 = Puerta(False, None, None)

        s1.salidas.append(Salida("E", s1, 2, p12, costo=10))
        s2.salidas.append(Salida("O", s2, 1, p12, costo=10))
        s2.salidas.append(Salida("E", s2, 3, p23, costo=20))
        s3.salidas.append(Salida("O", s3, 2, p23, costo=20))

        salas = IndiceOrdenado()
        salas.insertar(1, s1)
        salas.insertar(2, s2)
        salas.insertar(3, s3)

        dist = dijkstraDesde(s1, salas)
        self.assertEqual(dist.obtener(1), 0)
        self.assertEqual(dist.obtener(2), 10)
        self.assertEqual(dist.obtener(3), 30)

    def test_escenario_cazador_sin_ruta_espera_costo_100(self):
        """[FR-005, Apéndice B] Un cazador no tiene ruta abierta hacia el jugador: espera con costo 100."""
        cazador = Enemigo("c-1", "ent_cazador", "Cazador", "cazador", 20, 20, 5, 2, 100, rango=500)
        salaCazador = Sala(1, "Sala 1")
        salaJugador = Sala(2, "Sala 2")
        cazador.sala = salaCazador

        # Puerta cerrada entre sala 1 y sala 2
        puerta = Puerta(True, "llave_x", None)
        salaCazador.salidas.append(Salida("E", salaCazador, 2, puerta, costo=50))

        # Distancias calculadas desde el jugador: no llega a sala 1
        distancias = Tabla()
        distancias.guardar(2, 0)

        salida, costo = elegirPasoCazador(cazador, salaJugador, distancias)
        self.assertIsNone(salida)
        self.assertEqual(costo, 100)

    def test_escenario_cazador_ruta_mayor_que_rango_espera_costo_100(self):
        """[FR-005, Apéndice B] La ruta más barata del cazador cuesta más que su rango: espera con costo 100."""
        cazador = Enemigo("c-1", "ent_cazador", "Cazador", "cazador", 20, 20, 5, 2, 100, rango=150)
        salaCazador = Sala(1, "Sala 1")
        salaJugador = Sala(2, "Sala 2")
        cazador.sala = salaCazador

        puerta = Puerta(False, None, None)
        salaCazador.salidas.append(Salida("E", salaCazador, 2, puerta, costo=200))

        distancias = Tabla()
        distancias.guardar(2, 0)
        distancias.guardar(1, 200)  # d = 200 > rango (150)

        salida, costo = elegirPasoCazador(cazador, salaJugador, distancias)
        self.assertIsNone(salida)
        self.assertEqual(costo, 100)

    def test_escenario_ruta_menos_salas_mayor_costo_vs_mas_salas_menor_costo(self):
        """[FR-005, Apéndice B] Existe una ruta de menos salas pero mayor costo y otra de más salas y menor costo:
        el cazador sigue la de menor costo."""
        # Cazador en Sala 1, Jugador en Sala 4.
        # Ruta A: 1 <-> 4 (1 tramo, costo 500)
        # Ruta B: 1 <-> 2 <-> 3 <-> 4 (3 tramos, costos 50 + 50 + 50 = 150)
        s1 = Sala(1, "Sala 1")
        s2 = Sala(2, "Sala 2")
        s3 = Sala(3, "Sala 3")
        s4 = Sala(4, "Sala 4")

        p14 = Puerta(False, None, None)
        p12 = Puerta(False, None, None)
        p23 = Puerta(False, None, None)
        p34 = Puerta(False, None, None)

        s1.salidas.extend([
            Salida("N", s1, 4, p14, costo=500),
            Salida("E", s1, 2, p12, costo=50)
        ])
        s4.salidas.extend([
            Salida("S", s4, 1, p14, costo=500),
            Salida("O", s4, 3, p34, costo=50)
        ])
        s2.salidas.extend([
            Salida("O", s2, 1, p12, costo=50),
            Salida("E", s2, 3, p23, costo=50)
        ])
        s3.salidas.extend([
            Salida("O", s3, 2, p23, costo=50),
            Salida("E", s3, 4, p34, costo=50)
        ])

        salas = IndiceOrdenado()
        for s in [s1, s2, s3, s4]:
            salas.insertar(s.id, s)

        # Distancia desde sala 4 (jugador) hacia todas:
        dist = dijkstraDesde(s4, salas)
        self.assertEqual(dist.obtener(4), 0)
        self.assertEqual(dist.obtener(3), 50)
        self.assertEqual(dist.obtener(2), 100)
        self.assertEqual(dist.obtener(1), 150)  # Debe ser 150 (ruta B), no 500 (ruta A)

        cazador = Enemigo("c-1", "ent_cazador", "Cazador", "cazador", 20, 20, 5, 2, 100, rango=600)
        cazador.sala = s1

        salida, costo = elegirPasoCazador(cazador, s4, dist)
        self.assertIsNotNone(salida)
        self.assertEqual(salida.destinoId, 2)
        self.assertEqual(costo, 50)

    def test_escenario_desempate_dos_vecinas_costo_minimo_menor_id(self):
        """[FR-005, FR-008, Apéndice B] Dos vecinas inician rutas de costo mínimo: el cazador va a la de menor id."""
        # Cazador en Sala 10.
        # Vecina 5 con costo 100 y dist a jugador 50 => total 150
        # Vecina 2 con costo 100 y dist a jugador 50 => total 150
        # Debe elegir la vecina 2 por tener menor ID (2 < 5).
        s10 = Sala(10, "Sala 10")
        s5 = Sala(5, "Sala 5")
        s2 = Sala(2, "Sala 2")
        sJugador = Sala(1, "Sala Jugador")

        p10_5 = Puerta(False, None, None)
        p10_2 = Puerta(False, None, None)

        s10.salidas.append(Salida("N", s10, 5, p10_5, costo=100))
        s10.salidas.append(Salida("S", s10, 2, p10_2, costo=100))

        dist = Tabla()
        dist.guardar(1, 0)
        dist.guardar(5, 50)
        dist.guardar(2, 50)
        dist.guardar(10, 150)

        cazador = Enemigo("c-1", "ent_cazador", "Cazador", "cazador", 20, 20, 5, 2, 100, rango=300)
        cazador.sala = s10

        salida, costo = elegirPasoCazador(cazador, sJugador, dist)
        self.assertIsNotNone(salida)
        self.assertEqual(salida.destinoId, 2)
        self.assertEqual(costo, 100)

    def test_escenario_velocidad_alta_costo_uno_intervalo_minimo_uno(self):
        """[FR-002, Apéndice B] Un actor de velocidad alta atraviesa una salida de costo 1: el intervalo es al menos 1."""
        velocidad = 250
        costoSalida = 1
        intervalo = intervaloAccion(costoSalida, velocidad)
        self.assertEqual(intervalo, 1)

    def test_escenario_cambio_velocidad_salida_costosa_reescalado(self):
        """[FR-002, Apéndice B] Cambia la velocidad de un actor que atraviesa una salida costosa:
        el tiempo restante se escala según P1 §2.3."""
        # Acción en t=0 con costo 300 y velocidad 100 => intervalo = 300, tiempoSiguiente = 300
        # En t=100 (ha pasado 100 unidades, faltan 200), la velocidad aumenta a 200:
        # restante_nuevo = max(1, (300 - 100) * 100 // 200) = 200 * 100 // 200 = 100
        # tiempo_siguiente = 100 + 100 = 200
        nuevoTiempo = tiempoTrasCambioVelocidad(300, 100, 100, 200)
        self.assertEqual(nuevoTiempo, 200)

    def test_escenario_cazador_ataca_si_comparte_sala(self):
        """[FR-005] Si comparte sala con el jugador, ataca."""
        s1 = Sala(1, "Sala 1")
        cazador = Enemigo("c-1", "ent_cazador", "Cazador", "cazador", 20, 20, 5, 2, 100, rango=500)
        cazador.sala = s1

        dist = Tabla()
        dist.guardar(1, 0)

        salida, costo = elegirPasoCazador(cazador, s1, dist)
        self.assertIsNone(salida)
        self.assertEqual(costo, 0)

    def test_integracion_partida_cazador_persigue_y_terreno(self):
        """[FR-001, FR-002, FR-005, FR-007] Integración en el Modelo:
        El jugador se mueve por terreno costoso y el cazador avanza hacia él."""
        esqueleto = [
            {"id": 1, "nombre": "Entrada", "salidas": {"E": {"sala": 2, "costo": 200}}},
            {"id": 2, "nombre": "Pasillo", "salidas": {"O": {"sala": 1, "costo": 200}, "E": {"sala": 3, "costo": 50}}},
            {"id": 3, "nombre": "Cueva", "salidas": {"O": {"sala": 2, "costo": 50}, "N": {"sala": 4, "cerrada": True, "llave": "llave_fin"}}},
            {"id": 4, "nombre": "Salida", "salidas": {"S": {"sala": 3, "cerrada": True, "llave": "llave_fin"}}},
        ]
        contenidos = [
            {"sala": 1, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 2, "enemigos": [], "objetos": [], "trampas": []},
            {"sala": 3, "enemigos": [{"instancia": "c-101", "tipo": "ent_cazador", "vida": 15}],
             "objetos": [], "trampas": []},
            {"sala": 4, "enemigos": [], "objetos": [], "trampas": []},
        ]
        fichas = [
            {"id": "ent_cazador", "clase": "enemigo", "nombre": "Cazador",
             "vida_max": 15, "ataque": 4, "defensa": 1, "velocidad": 100,
             "comportamiento": "cazador", "rango": 600, "suelta": []}
        ]

        datosGen = {
            "sala_inicial": 1,
            "sala_salida": 4,
            "llave_salida": "llave_fin",
            "inventario_max": 10,
            "jugador": {"vida_max": 50, "ataque": 10, "defensa": 5, "velocidad": 100}
        }

        prov = ProveedorSintetico(esqueleto, contenidos, fichas, datosGen)
        modelo = Modelo(prov, semilla=42, inventario=Inventario(prov), diario=Diario())
        modelo.iniciarPartida()

        # Jugador en sala 1, tiempo=0
        self.assertEqual(modelo.jugador.sala.id, 1)
        self.assertEqual(modelo.reloj, 0)

        # Moverse al este (costo 200): debe tomar 200 unidades de reloj
        res = modelo.ejecutar(Accion(ACC_MOVER, "E"))
        self.assertTrue(res.ok)
        self.assertEqual(modelo.jugador.sala.id, 2)
        # El reloj virtual del jugador ahora es 200
        self.assertEqual(modelo.reloj, 200)

        # Al entrar a sala 2, el cazador en sala 3 aún no está activo porque está en sala 3 y el jugador no ha entrado allí
        # Entramos a sala 3 (costo 50)
        res = modelo.ejecutar(Accion(ACC_MOVER, "E"))
        self.assertTrue(res.ok)
        self.assertEqual(modelo.jugador.sala.id, 3)
        self.assertEqual(modelo.reloj, 250)

        # El cazador se activa en sala 3 al entrar el jugador
        self.assertEqual(len(modelo.jugador.sala.enemigos), 1)
        cazadorActivo = modelo.jugador.sala.enemigos[0]
        self.assertTrue(cazadorActivo.activo)
        self.assertEqual(cazadorActivo.rango, 600)


if __name__ == "__main__":
    unittest.main()
