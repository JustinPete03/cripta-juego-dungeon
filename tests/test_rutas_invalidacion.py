# Pruebas de la especificación 005: rutas ponderadas e invalidación de rutas.
# Trazabilidad: FR-039 a FR-044, PR-010 (specs/005-rutas-e-invalidacion/spec.md).
#
# Fase 3 (T008): núcleo de búsqueda común (calcularDistancias, elegirPrimerPaso).
# Fases 4 y 5 (T011, T016, T017): cazador con cota, RutasCazador e invalidación fina.
# Fase 6 (T019): «ir a» sobre el núcleo. Fase 8 (T024): simetría de las criptas de demostración.

import glob
import json
import os
import random
import unittest

from model.Constantes import DIRECCIONES, ACC_ESPERAR, ACC_MOVER, ACC_ABRIR, ACC_RETROCESO
from model.Entidades import Sala, Salida, Puerta, Enemigo, ObjetoInstancia
from model.Dijkstra import (calcularDistancias, elegirPrimerPaso, puertaAbierta, dijkstraDesde,
                            EspacioBusqueda)
from model.Cazador import elegirPasoCazador
from model.RutasCazador import RutasCazador
from model.Acciones import Accion
import model.Juego as moduloJuego


# ------------------------------------------------------------------ construcción de criptas
def _conectar(a, direccion, b, direccionInversa, costo, cerrada=False):
    """Une a y b con una sola puerta compartida y el mismo costo en ambos sentidos (§3.1)."""
    puerta = Puerta(cerrada, None, None)
    ida = Salida(direccion, a, b.id, puerta, costo)
    ida.destino = b
    vuelta = Salida(direccionInversa, b, a.id, puerta, costo)
    vuelta.destino = a
    a.salidas.append(ida)
    b.salidas.append(vuelta)
    return puerta


def _ordenarSalidas(salas):
    """Deja las salidas de cada sala en el orden canónico N, S, E, O, como _construirSalas."""
    for sala in salas:
        sala.salidas.sort(key=lambda s: DIRECCIONES.index(s.direccion))


def _salas(n):
    return [None] + [Sala(i, "Sala %d" % i) for i in range(1, n + 1)]


def _cuadricula(lado, costoFijo=None, semilla=1):
    """Cuadrícula lado x lado; ids 1..lado², fila por fila. Costos fijos o al azar con semilla."""
    azar = random.Random(semilla)
    s = _salas(lado * lado)
    for y in range(lado):
        for x in range(lado):
            sala = s[y * lado + x + 1]
            if x < lado - 1:
                _conectar(sala, "E", s[y * lado + x + 2], "O", costoFijo or azar.randint(10, 200))
            if y < lado - 1:
                _conectar(sala, "S", s[(y + 1) * lado + x + 1], "N", costoFijo or azar.randint(10, 200))
    _ordenarSalidas(s[1:])
    return s


def _destino(salida):
    return None if salida is None else salida.destino.id


# ------------------------------------------------------------------ pruebas
class TestNucleoBusqueda(unittest.TestCase):

    def test_pesos_menos_salas_no_es_mas_barato(self):
        """FR-043: la distancia es la de menor costo, no la de menos salas.

        1 -(300)- 3 directo, frente a 1 -(100)- 2 -(100)- 3.
        """
        s = _salas(3)
        _conectar(s[1], "E", s[3], "O", 300)
        _conectar(s[1], "S", s[2], "N", 100)
        _conectar(s[2], "E", s[3], "O", 100)
        _ordenarSalidas(s[1:])
        dist = calcularDistancias(s[3], puertaAbierta)
        self.assertEqual(dist.de(s[1]), 200)
        self.assertEqual(_destino(elegirPrimerPaso(s[1], dist, puertaAbierta)), 2)

    def test_puerta_cerrada_no_se_usa(self):
        """FR-043: con la regla del cazador, una salida cerrada no forma parte de ninguna ruta."""
        s = _salas(3)
        _conectar(s[1], "E", s[3], "O", 300)
        _conectar(s[1], "S", s[2], "N", 100)
        barata = _conectar(s[2], "E", s[3], "O", 100)
        _ordenarSalidas(s[1:])
        barata.cerrada = True
        dist = calcularDistancias(s[3], puertaAbierta)
        self.assertEqual(dist.de(s[1]), 300)
        self.assertEqual(_destino(elegirPrimerPaso(s[1], dist, puertaAbierta)), 3)

    def test_sin_ruta_devuelve_none(self):
        """FR-043: si todas las salidas hacia el origen están cerradas, no hay distancia ni paso."""
        s = _salas(2)
        puerta = _conectar(s[1], "E", s[2], "O", 50)
        puerta.cerrada = True
        dist = calcularDistancias(s[2], puertaAbierta)
        self.assertIsNone(dist.de(s[1]))
        self.assertIsNone(elegirPrimerPaso(s[1], dist, puertaAbierta))

    def test_en_el_origen_no_hay_paso(self):
        """D4: desde el propio origen no hay candidatas (la regla de ataque de 001 decide antes)."""
        s = _salas(2)
        _conectar(s[1], "E", s[2], "O", 50)
        dist = calcularDistancias(s[1], puertaAbierta)
        self.assertEqual(dist.de(s[1]), 0)
        self.assertIsNone(elegirPrimerPaso(s[1], dist, puertaAbierta))

    def test_muchas_rutas_de_igual_costo(self):
        """FR-042, US-1 escenario 10: en una cuadrícula de costos iguales hay muchas rutas mínimas;
        en cada paso se va a la vecina de menor id entre las que inician una ruta mínima.

        Cuadrícula 3x3 (ids 1..9), origen en 9. Desde 1 las vecinas 2 y 4 inician rutas mínimas:
        gana 2. El recorrido completo, paso a paso, es 1 -> 2 -> 3 -> 6 -> 9.
        """
        s = _cuadricula(3, costoFijo=100)
        dist = calcularDistancias(s[9], puertaAbierta)
        recorrido = [1]
        actual = s[1]
        while actual is not s[9]:
            actual = elegirPrimerPaso(actual, dist, puertaAbierta).destino
            recorrido.append(actual.id)
        self.assertEqual(recorrido, [1, 2, 3, 6, 9])

    def test_desempate_no_depende_del_orden_de_las_salidas(self):
        """FR-042: el resultado es el mismo aunque las salidas estén en otro orden."""
        s = _cuadricula(3, costoFijo=100)
        dist = calcularDistancias(s[9], puertaAbierta)
        antes = _destino(elegirPrimerPaso(s[5], dist, puertaAbierta))
        s[5].salidas.reverse()
        despues = _destino(elegirPrimerPaso(s[5], dist, puertaAbierta))
        self.assertEqual(antes, despues)
        self.assertEqual(antes, 6)     # desde 5, las vecinas 6 y 8 empatan: gana 6

    def test_dos_salidas_hacia_la_misma_vecina(self):
        """Spec Q4: hacia la vecina elegida se usa la salida más barata; si empatan, la primera
        en orden N, S, E, O."""
        s = _salas(2)
        _conectar(s[1], "N", s[2], "S", 80)
        _conectar(s[1], "E", s[2], "O", 50)
        _ordenarSalidas(s[1:])
        dist = calcularDistancias(s[2], puertaAbierta)
        paso = elegirPrimerPaso(s[1], dist, puertaAbierta)
        self.assertEqual((paso.direccion, paso.costo), ("E", 50))

        s = _salas(2)
        _conectar(s[1], "E", s[2], "O", 50)
        _conectar(s[1], "S", s[2], "N", 50)
        _ordenarSalidas(s[1:])
        dist = calcularDistancias(s[2], puertaAbierta)
        self.assertEqual(elegirPrimerPaso(s[1], dist, puertaAbierta).direccion, "S")

    def test_coincide_con_la_busqueda_anterior(self):
        """FR-039: el núcleo da las mismas distancias que dijkstraDesde en una cripta con pesos."""
        from model.Salas import IndiceOrdenado
        s = _cuadricula(8, semilla=7)
        indice = IndiceOrdenado()
        for sala in s[1:]:
            indice.insertar(sala.id, sala)
        nuevo = calcularDistancias(s[28], puertaAbierta)
        viejo = dijkstraDesde(s[28], indice)
        for sala in s[1:]:
            self.assertEqual(nuevo.de(sala), viejo.obtener(sala.id))

    def test_cota_no_cambia_decisiones_dentro_del_rango(self):
        """FR-043, PR-010: con cota = rango, toda sala a distancia <= rango decide lo mismo que
        sin cota; las salas más allá quedan como desconocidas (el cazador espera)."""
        s = _cuadricula(12, semilla=3)
        origen = s[66]
        rango = 400
        completa = calcularDistancias(origen, puertaAbierta)
        acotada = calcularDistancias(origen, puertaAbierta, cota=rango)
        dentro = 0
        for sala in s[1:]:
            d = completa.de(sala)
            if d <= rango:
                dentro += 1
                self.assertEqual(acotada.de(sala), d)
                self.assertEqual(_destino(elegirPrimerPaso(sala, acotada, puertaAbierta)),
                                 _destino(elegirPrimerPaso(sala, completa, puertaAbierta)))
            else:
                self.assertIsNone(acotada.de(sala))
        self.assertGreater(dentro, 1)

    def test_cota_examina_pocas_salas(self):
        """PR-010: con una cota pequeña, la búsqueda examina pocas salas aunque la cripta sea
        grande, y la cantidad no cambia con el tamaño de la cripta."""
        examinadas = []
        for lado in (10, 40):
            s = _cuadricula(lado, costoFijo=100)
            centro = s[(lado // 2) * lado + lado // 2 + 1]
            dist = calcularDistancias(centro, puertaAbierta, cota=200)
            examinadas.append(dist.salasExaminadas)
        self.assertEqual(examinadas[0], examinadas[1])
        self.assertEqual(examinadas[0], 13)     # rombo de radio 2: 1 + 4 + 8

    def test_regla_puede_usar_personalizada(self):
        """FR-044: la misma búsqueda sirve para «ir a» cambiando la regla de salidas usables
        (aquí: solo salas marcadas como conocidas)."""
        s = _cuadricula(3, costoFijo=100)
        conocidas = (1, 2, 3, 6, 9)

        def soloConocidas(sala, salida):
            return salida.destino.id in conocidas and not salida.puerta.cerrada

        dist = calcularDistancias(s[9], soloConocidas)
        self.assertIsNone(dist.de(s[4]))
        self.assertEqual(dist.de(s[1]), 400)
        self.assertEqual(_destino(elegirPrimerPaso(s[1], dist, soloConocidas)), 2)

    def test_espacio_con_sellos_da_lo_mismo_que_tabla(self):
        """PR-010, plan D3: el arreglo con sellos da las mismas distancias que la Tabla, también
        en búsquedas sucesivas con el mismo espacio y con cota."""
        s = _cuadricula(9, semilla=11)
        _preparar(s)
        espacio = EspacioBusqueda(len(s) - 1)
        for origen, cota in ((s[1], None), (s[41], 300), (s[81], None), (s[41], 300)):
            conTabla = calcularDistancias(origen, puertaAbierta, cota)
            conEspacio = calcularDistancias(origen, puertaAbierta, cota, espacio)
            for sala in s[1:]:
                self.assertEqual(conEspacio.de(sala), conTabla.de(sala))
            self.assertEqual(conEspacio.salasExaminadas, conTabla.salasExaminadas)

    def test_distancias_obsoletas_no_se_pueden_leer(self):
        """Plan D3: tras otra búsqueda en el mismo espacio, las distancias anteriores no se leen
        en silencio con datos ajenos."""
        s = _cuadricula(3, costoFijo=100)
        _preparar(s)
        espacio = EspacioBusqueda(9)
        vieja = calcularDistancias(s[1], puertaAbierta, None, espacio)
        calcularDistancias(s[9], puertaAbierta, None, espacio)
        with self.assertRaises(RuntimeError):
            vieja.de(s[5])


# ------------------------------------------------------------------ apoyo para rutas del cazador
def _preparar(s):
    """Hace con una cripta armada a mano lo que hace Juego._construirSalas (T003, T004)."""
    for i, sala in enumerate(s[1:]):
        sala.indice = i
        for salida in sala.salidas:
            if salida.puerta.salaA is None:
                salida.puerta.salaA = sala
                salida.puerta.salaB = salida.destino
                salida.puerta.costo = salida.costo
    return s


def _cazadorEn(sala, rango):
    c = Enemigo("c", "ent_cazador", "Cazador", "cazador", 20, 20, 1, 1, 100, rango=rango)
    c.sala = sala
    c.activo = True
    return c


def _decisionDesdeCero(sala, jugador, rango):
    return _paso(elegirPasoCazador(_cazadorEn(sala, rango), jugador,
                                   calcularDistancias(jugador, puertaAbierta)))


def _paso(decision):
    salida, costo = decision
    return (None if salida is None else salida.destino.id, costo)


def _puertaEntre(a, b):
    for salida in a.salidas:
        if salida.destino is b:
            return salida.puerta
    raise AssertionError("no hay puerta entre %s y %s" % (a.id, b.id))


class TestRutasCazador(unittest.TestCase):
    """RutasCazador sobre criptas armadas a mano (T011, T012 a T014; spec 005 US-1)."""

    def _rutas(self, s):
        return RutasCazador(len(s) - 1)

    def _assertTodasIguales(self, s, jugador, rutas, rango):
        """FR-039: toda sala decide igual con la caché que calculando desde cero."""
        dist = rutas.distanciasPara(jugador, rango, lambda: rango)
        for sala in s[1:]:
            self.assertEqual(_paso(elegirPasoCazador(_cazadorEn(sala, rango), jugador, dist)),
                             _decisionDesdeCero(sala, jugador, rango), "sala %d" % sala.id)

    def test_reutiliza_mientras_nada_cambia(self):
        """FR-041: dos consultas seguidas con el jugador en la misma sala hacen una sola búsqueda."""
        s = _preparar(_cuadricula(4, semilla=2))
        rutas = self._rutas(s)
        rutas.distanciasPara(s[1], 500, lambda: 500)
        rutas.distanciasPara(s[1], 500, lambda: 500)
        self.assertEqual(rutas.recalculos, 1)

    def test_recalcula_si_el_jugador_cambia_de_sala(self):
        """FR-040, US-1 escenario 5: con el jugador en otra sala, las rutas apuntan a la nueva."""
        s = _preparar(_cuadricula(4, semilla=2))
        rutas = self._rutas(s)
        rutas.distanciasPara(s[1], 10 ** 6, lambda: 10 ** 6)
        dist = rutas.distanciasPara(s[16], 10 ** 6, lambda: 10 ** 6)
        self.assertEqual(rutas.recalculos, 2)
        self.assertEqual(dist.de(s[16]), 0)
        self._assertTodasIguales(s, s[16], rutas, 10 ** 6)

    def test_cazador_de_mas_rango_obliga_a_recalcular(self):
        """FR-040, FR-043, US-1 escenario 9: si se activa un cazador con más rango que la cota,
        se recalcula con la cota nueva y su decisión coincide con un cálculo desde cero."""
        s = _preparar(_cuadricula(6, semilla=5))
        rutas = self._rutas(s)
        rutas.distanciasPara(s[1], 150, lambda: 150)
        lejana = s[36]
        dist = rutas.distanciasPara(s[1], 5000, lambda: 150)
        self.assertEqual(rutas.recalculos, 2)
        self.assertEqual(_paso(elegirPasoCazador(_cazadorEn(lejana, 5000), s[1], dist)),
                         _decisionDesdeCero(lejana, s[1], 5000))
        self.assertIsNotNone(_paso(elegirPasoCazador(_cazadorEn(lejana, 5000), s[1], dist))[0])

    def test_rango_exactamente_igual_al_costo(self):
        """FR-039, US-1 escenario 11: si el costo mínimo al jugador es igual al rango, se mueve."""
        s = _salas(3)
        _conectar(s[1], "E", s[2], "O", 70)
        _conectar(s[2], "E", s[3], "O", 80)
        _ordenarSalidas(s[1:])
        _preparar(s)
        rutas = self._rutas(s)
        dist = rutas.distanciasPara(s[1], 150, lambda: 150)
        self.assertEqual(_paso(elegirPasoCazador(_cazadorEn(s[3], 150), s[1], dist)), (2, 80))
        self.assertEqual(_paso(elegirPasoCazador(_cazadorEn(s[3], 149), s[1], dist)), (None, 100))

    def test_cierre_lejos_de_rutas_minimas_no_invalida(self):
        """FR-041, US-1 escenario 2: cerrar una puerta que no está en ningún camino mínimo no
        obliga a recalcular, y ninguna decisión cambia."""
        s = _salas(4)
        _conectar(s[1], "E", s[2], "O", 10)
        _conectar(s[2], "S", s[4], "N", 10)
        _conectar(s[1], "S", s[3], "N", 10)
        lejana = _conectar(s[3], "E", s[4], "O", 500)      # 3-4 no es camino mínimo de nadie
        _ordenarSalidas(s[1:])
        _preparar(s)
        rutas = self._rutas(s)
        rutas.distanciasPara(s[1], 1000, lambda: 1000)
        lejana.cerrada = True
        rutas.puertaCambio(lejana, False)
        self.assertEqual(rutas.puertasIgnoradas, 1)
        self.assertEqual(rutas.invalidaciones, 0)
        self._assertTodasIguales(s, s[1], rutas, 1000)
        self.assertEqual(rutas.recalculos, 1)

    def test_cierre_en_camino_minimo_invalida(self):
        """FR-039, FR-041, US-1 escenario 1: cerrar una puerta de un camino mínimo invalida, y la
        decisión siguiente toma la otra ruta, igual que un cálculo desde cero."""
        s = _salas(4)
        atajo = _conectar(s[1], "E", s[2], "O", 10)
        _conectar(s[2], "S", s[4], "N", 10)
        _conectar(s[1], "S", s[3], "N", 50)
        _conectar(s[3], "E", s[4], "O", 50)
        _ordenarSalidas(s[1:])
        _preparar(s)
        rutas = self._rutas(s)
        dist = rutas.distanciasPara(s[1], 1000, lambda: 1000)
        self.assertEqual(_paso(elegirPasoCazador(_cazadorEn(s[4], 1000), s[1], dist)), (2, 10))
        atajo.cerrada = True
        rutas.puertaCambio(atajo, False)
        self.assertEqual(rutas.invalidaciones, 1)
        dist = rutas.distanciasPara(s[1], 1000, lambda: 1000)
        self.assertEqual(_paso(elegirPasoCazador(_cazadorEn(s[4], 1000), s[1], dist)), (3, 50))
        self._assertTodasIguales(s, s[1], rutas, 1000)

    def test_apertura_que_crea_un_atajo_invalida(self):
        """FR-039, US-1 escenario 3: abrir una puerta que acorta una ruta invalida, y el cazador
        usa el atajo en el turno siguiente."""
        s = _salas(4)
        atajo = _conectar(s[1], "E", s[2], "O", 10, cerrada=True)
        _conectar(s[2], "S", s[4], "N", 10)
        _conectar(s[1], "S", s[3], "N", 50)
        _conectar(s[3], "E", s[4], "O", 50)
        _ordenarSalidas(s[1:])
        _preparar(s)
        rutas = self._rutas(s)
        dist = rutas.distanciasPara(s[1], 1000, lambda: 1000)
        self.assertEqual(_paso(elegirPasoCazador(_cazadorEn(s[4], 1000), s[1], dist)), (3, 50))
        atajo.cerrada = False
        rutas.puertaCambio(atajo, True)
        self.assertEqual(rutas.invalidaciones, 1)
        dist = rutas.distanciasPara(s[1], 1000, lambda: 1000)
        self.assertEqual(_paso(elegirPasoCazador(_cazadorEn(s[4], 1000), s[1], dist)), (2, 10))

    def test_apertura_sin_atajo_no_invalida(self):
        """FR-041, US-1 escenario 4: abrir una puerta que no acorta ninguna ruta no invalida."""
        s = _salas(4)
        _conectar(s[1], "E", s[2], "O", 10)
        _conectar(s[2], "S", s[4], "N", 10)
        _conectar(s[1], "S", s[3], "N", 10)
        cara = _conectar(s[3], "E", s[4], "O", 500, cerrada=True)
        _ordenarSalidas(s[1:])
        _preparar(s)
        rutas = self._rutas(s)
        rutas.distanciasPara(s[1], 1000, lambda: 1000)
        cara.cerrada = False
        rutas.puertaCambio(cara, True)
        self.assertEqual(rutas.invalidaciones, 0)
        self._assertTodasIguales(s, s[1], rutas, 1000)

    def test_apertura_fuera_de_la_cota_no_invalida(self):
        """FR-041, PR-010: abrir una puerta entre salas que siguen fuera de la cota no invalida."""
        s = _preparar(_cuadricula(10, costoFijo=100))
        rutas = self._rutas(s)
        rutas.distanciasPara(s[1], 200, lambda: 200)
        lejana = _puertaEntre(s[99], s[100])
        lejana.cerrada = True
        rutas.puertaCambio(lejana, False)
        lejana.cerrada = False
        rutas.puertaCambio(lejana, True)
        self.assertEqual(rutas.invalidaciones, 0)
        self.assertEqual(rutas.puertasIgnoradas, 2)

    def test_puerta_sin_salas_conocidas_invalida(self):
        """Plan D5: si una puerta no conoce sus salas, no se puede demostrar nada y se invalida."""
        s = _preparar(_cuadricula(3, costoFijo=100))
        rutas = self._rutas(s)
        rutas.distanciasPara(s[1], 1000, lambda: 1000)
        rutas.puertaCambio(Puerta(False, None, None), False)
        self.assertEqual(rutas.invalidaciones, 1)


# ------------------------------------------------------------------ partida real
FICHA_CAZADOR = {"id": "ent_cazador", "clase": "enemigo", "nombre": "Cazador", "vida_max": 20,
                 "ataque": 1, "defensa": 50, "velocidad": 100, "comportamiento": "cazador",
                 "rango": 10 ** 6, "suelta": []}
FICHA_PERGAMINO = {"id": "itm_pergamino", "clase": "pergamino_retroceso",
                   "nombre": "Pergamino de retroceso", "peso": 1, "valor": 50}


class _FuenteRutas:
    """Cuadrícula lado x lado con costos al azar, cazadores en salas dadas y, si se pide, una
    puerta con cierre automático entre las salas 1 y 2."""

    def __init__(self, lado, salasCazadores, semilla=3, cierreAutomatico=None):
        azar = random.Random(semilla)
        self.total = lado * lado
        self.salas = [{"id": i + 1, "nombre": "Sala %d" % (i + 1), "salidas": {}} for i in range(self.total)]
        for y in range(lado):
            for x in range(lado):
                i = y * lado + x + 1
                if x < lado - 1:
                    c = azar.randint(10, 200)
                    self.salas[i - 1]["salidas"]["E"] = {"sala": i + 1, "costo": c}
                    self.salas[i]["salidas"]["O"] = {"sala": i, "costo": c}
                if y < lado - 1:
                    c = azar.randint(10, 200)
                    self.salas[i - 1]["salidas"]["S"] = {"sala": i + lado, "costo": c}
                    self.salas[i + lado - 1]["salidas"]["N"] = {"sala": i, "costo": c}
        if cierreAutomatico is not None:
            for a, b, d in ((1, 2, "E"), (2, 1, "O")):
                info = self.salas[a - 1]["salidas"][d]
                info["costo"] = 10
                info["cerrada"] = True
                info["cierre_automatico"] = cierreAutomatico
        self.enemigos = [[] for _ in range(self.total)]
        for n, sala in enumerate(salasCazadores):
            self.enemigos[sala - 1].append({"instancia": "c-%02d" % n, "tipo": "ent_cazador"})

    def datosGenerales(self):
        return {"id": "cripta-rutas", "version": "v1", "sala_inicial": 1, "sala_salida": self.total,
                "llave_salida": "itm_inexistente", "presupuesto_solicitudes": 10 ** 6, "inventario_max": 10,
                "jugador": {"vida_max": 10 ** 9, "ataque": 1, "defensa": 1000, "velocidad": 100}}

    def esqueleto(self):
        return self.salas

    def contenidoSala(self, salaId):
        return {"sala": salaId, "enemigos": list(self.enemigos[salaId - 1]), "objetos": [], "trampas": []}

    def ficha(self, tipoId):
        for f in (FICHA_CAZADOR, FICHA_PERGAMINO):
            if f["id"] == tipoId:
                return f
        raise KeyError(tipoId)

    def anticipar(self, salaId):
        pass

    def asegurarFichas(self, tipoIds):
        pass

    def fijarFichasEnUso(self, productor):
        pass


def _partida(fuente, semilla=1):
    from model.Inventario import Inventario
    from model.Diario import Diario
    modelo = moduloJuego.Modelo(fuente, semilla, Inventario(fuente), Diario())
    modelo.iniciarPartida()
    for i in range(modelo.salas.cantidad()):
        sala = modelo.salas.enPosicion(i)
        modelo._asegurarContenido(sala)
        modelo._activarDormidos(sala)
    return modelo


class _Oraculo:
    """Envuelve la decisión del cazador del motor: en cada turno compara la decisión tomada con
    la caché contra la de un cálculo desde cero sin cota (FR-039)."""

    def __init__(self, prueba):
        self.prueba = prueba
        self.decisiones = 0
        self.movimientos = 0

    def __enter__(self):
        self._original = moduloJuego.elegirPasoCazador
        original = self._original

        def verificada(cazador, salaJugador, distancias):
            real = original(cazador, salaJugador, distancias)
            cero = original(cazador, salaJugador, calcularDistancias(salaJugador, puertaAbierta))
            self.prueba.assertEqual(_paso(real), _paso(cero))
            self.decisiones += 1
            if real[0] is not None:
                self.movimientos += 1
            return real

        moduloJuego.elegirPasoCazador = verificada
        return self

    def __exit__(self, *exc):
        moduloJuego.elegirPasoCazador = self._original
        return False


class TestRutasEnPartida(unittest.TestCase):
    """Spec 005 US-1 en una partida real (T016, T017)."""

    def test_puerta_de_la_ruta_se_cierra_por_la_agenda(self):
        """FR-039, FR-040, US-1 escenario 1 (Apéndice B): el jugador abre una puerta con cierre
        automático; los cazadores la usan como atajo; la agenda la cierra entre dos turnos y
        cada decisión posterior coincide con un cálculo desde cero."""
        modelo = _partida(_FuenteRutas(5, (5, 10, 15, 20, 25, 24), cierreAutomatico=300))
        with _Oraculo(self) as oraculo:
            self.assertTrue(modelo.ejecutar(Accion(ACC_ABRIR, "E")).ok)
            puerta = modelo.jugador.sala.salida("E").puerta
            antesDelCierre = None
            for _ in range(12):
                modelo.ejecutar(Accion(ACC_ESPERAR))
                if antesDelCierre is None and puerta.cerrada:
                    antesDelCierre = oraculo.decisiones
            self.assertTrue(puerta.cerrada)
            self.assertGreater(oraculo.decisiones, antesDelCierre)
        self.assertGreaterEqual(modelo.rutasCazador.invalidaciones, 1)

    def test_pergamino_revierte_una_puerta_abierta(self):
        """FR-040, US-1 escenario 6: el jugador abre una puerta que es atajo de los cazadores y
        el pergamino la vuelve a cerrar sin que el jugador cambie de sala. Como el diario revierte
        la puerta sin pasar por los eventos, las rutas deben invalidarse: cada decisión posterior
        coincide con un cálculo desde cero."""
        modelo = _partida(_FuenteRutas(5, (2, 3, 7, 8, 12), cierreAutomatico=10 ** 6))
        sala = modelo.jugador.sala
        with _Oraculo(self) as oraculo:
            self.assertTrue(modelo.ejecutar(Accion(ACC_ABRIR, "E")).ok)
            puerta = sala.salida("E").puerta
            self.assertFalse(puerta.cerrada)
            # Lo que haría el turno de un cazador: dejar calculadas las rutas con la puerta abierta
            modelo._obtenerDistanciasCazador(modelo.enemigosVivos[0])
            modelo.inventario._enlazarDespues(_nodo(ObjetoInstancia("itm_pergamino", 999)), modelo.inventario.cola)
            self.assertTrue(modelo.ejecutar(Accion(ACC_RETROCESO)).ok)
            self.assertTrue(puerta.cerrada)
            self.assertIs(modelo.jugador.sala, sala)
            decisiones = oraculo.decisiones
            for _ in range(6):
                modelo.ejecutar(Accion(ACC_ESPERAR))
            self.assertGreater(oraculo.decisiones, decisiones)

    def test_restaurar_estado_invalida_las_rutas(self):
        """FR-040, US-1 escenario 8: restaurar un estado guardado (cargar partida) cambia puertas
        sin pasar por los eventos; la primera decisión de cada cazador coincide con un cálculo
        desde cero."""
        modelo = _partida(_FuenteRutas(5, (2, 3, 7, 8, 12), cierreAutomatico=10 ** 6))
        guardado = modelo.capturarEstado()
        with _Oraculo(self) as oraculo:
            self.assertTrue(modelo.ejecutar(Accion(ACC_ABRIR, "E")).ok)
            modelo._obtenerDistanciasCazador(modelo.enemigosVivos[0])   # rutas con la puerta abierta
            modelo.restaurarEstado(guardado)
            self.assertTrue(modelo.jugador.sala.salida("E").puerta.cerrada)
            decisiones = oraculo.decisiones
            for _ in range(6):
                modelo.ejecutar(Accion(ACC_ESPERAR))
            self.assertGreater(oraculo.decisiones, decisiones)

    def _simular(self, lado, salasCazadores, probMover, turnos, semilla):
        modelo = _partida(_FuenteRutas(lado, salasCazadores, semilla=semilla), semilla=semilla)
        azar = random.Random(semilla)
        puertas = []
        for i in range(modelo.salas.cantidad()):
            for salida in modelo.salas.enPosicion(i).salidas:
                if salida.direccion in ("E", "S"):
                    puertas.append(salida.puerta)
        with _Oraculo(self) as oraculo:
            for _ in range(turnos):
                if azar.random() < probMover:
                    abiertas = [s for s in modelo.jugador.sala.salidas if not s.puerta.cerrada]
                    if abiertas:
                        modelo.ejecutar(Accion(ACC_MOVER, abiertas[azar.randrange(len(abiertas))].direccion))
                        continue
                puerta = puertas[azar.randrange(len(puertas))]
                modelo.asignar(puerta, "cerrada", not puerta.cerrada)
                modelo.rutasCazador.puertaCambio(puerta, not puerta.cerrada)
                modelo.ejecutar(Accion(ACC_ESPERAR))
        rutas = modelo.rutasCazador
        self.assertGreater(oraculo.decisiones, turnos)
        self.assertGreater(rutas.invalidaciones, 0)       # hubo cambios que sí afectaban
        self.assertGreater(rutas.puertasIgnoradas, 0)     # y otros que se demostró que no
        self.assertLess(rutas.recalculos, oraculo.decisiones)

    def test_oraculo_jugador_quieto_y_puertas_cambiando(self):
        """FR-039, FR-041, US-1 escenario 12: el jugador casi no se mueve y en cada turno se abre
        o cierra una puerta al azar; cada decisión coincide con un cálculo desde cero."""
        self._simular(10, tuple(range(5, 100, 4)), 0.05, 300, 9)

    def test_oraculo_jugador_en_movimiento(self):
        """FR-039, FR-040, US-1 escenarios 5, 7 y 12: el jugador se mueve con frecuencia, los
        cazadores cambian de sala y las puertas cambian; cada decisión coincide con un cálculo
        desde cero."""
        self._simular(8, tuple(range(10, 65, 3)), 0.25, 300, 9)


def _nodo(objeto):
    from model.Inventario import Nodo
    return Nodo(objeto)


# ------------------------------------------------------------------ «ir a» y simetría
class TestViajeYSimetria(unittest.TestCase):

    def test_ir_a_desempata_igual_que_el_cazador(self):
        """FR-044, US-3 escenario 1: con dos vecinas exploradas que inician rutas conocidas de
        costo mínimo, el viaje da el primer paso hacia la de menor id."""
        from model.Dijkstra import elegirPasoViajeAutomatico
        from model.MapaConocido import MapaConocido
        s = _cuadricula(3, costoFijo=100)
        mapa = MapaConocido(lambda *a: None)
        for sala in s[1:]:
            mapa.explorarSala(sala)
        salida, costo = elegirPasoViajeAutomatico(s[1], s[9], None, mapa)
        self.assertEqual((salida.destino.id, costo), (2, 100))

    def test_ir_a_prefiere_menor_costo_a_menos_salas(self):
        """FR-044, US-3 escenario 2: en el mapa conocido, el viaje sigue la ruta de menor costo."""
        from model.Dijkstra import elegirPasoViajeAutomatico
        from model.MapaConocido import MapaConocido
        s = _salas(3)
        _conectar(s[1], "E", s[3], "O", 300)
        _conectar(s[1], "S", s[2], "N", 100)
        _conectar(s[2], "E", s[3], "O", 100)
        _ordenarSalidas(s[1:])
        mapa = MapaConocido(lambda *a: None)
        for sala in s[1:]:
            mapa.explorarSala(sala)
        salida, costo = elegirPasoViajeAutomatico(s[1], s[3], None, mapa)
        self.assertEqual((salida.destino.id, costo), (2, 100))

    def test_simetria_de_las_criptas_de_demostracion(self):
        """Supuesto de la spec 005 (§3.1), T024: en cada cripta de demostración, toda salida
        tiene una salida de vuelta con la misma puerta y el mismo costo. Es lo que permite que
        una sola búsqueda desde el jugador dé la distancia de cada sala hacia el jugador."""
        raiz = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos_demo")
        archivos = sorted(glob.glob(os.path.join(raiz, "cripta-*_salas_p1.json")))
        self.assertGreater(len(archivos), 0)
        for archivo in archivos:
            with open(archivo, encoding="utf-8") as f:
                esqueleto = json.load(f)["salas"]
            modelo = moduloJuego.Modelo(None, 1, None)
            modelo._construirSalas(esqueleto)
            for i in range(modelo.salas.cantidad()):
                sala = modelo.salas.enPosicion(i)
                for salida in sala.salidas:
                    vuelta = [v for v in salida.destino.salidas if v.destino is sala]
                    self.assertTrue(vuelta, "%s: %d -> %d sin vuelta" % (archivo, sala.id, salida.destino.id))
                    self.assertTrue(any(v.puerta is salida.puerta and v.costo == salida.costo for v in vuelta),
                                    "%s: %d <-> %d no comparten puerta y costo" % (archivo, sala.id, salida.destino.id))


if __name__ == "__main__":
    unittest.main()
