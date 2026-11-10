# Pruebas de la especificación 005: rutas ponderadas e invalidación de rutas.
# Trazabilidad: FR-039 a FR-044, PR-010 (specs/005-rutas-e-invalidacion/spec.md).
#
# Fase 3 (T008): núcleo de búsqueda común (calcularDistancias, elegirPrimerPaso).

import random
import unittest

from model.Constantes import DIRECCIONES
from model.Entidades import Sala, Salida, Puerta
from model.Dijkstra import (calcularDistancias, elegirPrimerPaso, puertaAbierta, dijkstraDesde)


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


if __name__ == "__main__":
    unittest.main()
