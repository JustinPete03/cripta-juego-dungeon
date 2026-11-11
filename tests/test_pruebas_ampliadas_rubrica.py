# Suite de pruebas unitarias y de integración ampliada para responder a la retroalimentación
# de la rúbrica del profesor: "La suite de pruebas debería ampliarse más".
#
# Cubre casos de borde en:
# 1. Caché LRU de catálogo (capacidad unitaria, protección estricta de fichas en uso, rebasamiento controlado).
# 2. Cliente HTTP y robustez de red (reintentos 429, timeouts, errores 404/500, JSON inválido).
# 3. Formato de guardado binario e incompatibilidades de versión (v2 vs v3, magic corrupto).
# 4. Interacción compleja entre pergamino de retroceso y la línea de tiempo.

import io
import json
import os
import unittest
from unittest.mock import patch, MagicMock
import requests

from adapters.clienteHttp import (
    ClienteHTTP, ErrorLimiteFrecuenciaExcedido, ErrorHttp,
    ErrorTiempoEspera, ErrorConexionServidor, ErrorRespuestaInvalida
)
from model.cache_estructuras import CacheCatalogo
from model.Tabla import Tabla, Conjunto
from model.Acciones import Accion
from model.Constantes import ACC_MOVER, ACC_ESPERAR, ACC_RETROCESO, ACC_USAR, ACC_EQUIPAR
from model.Juego import Modelo
from model.Inventario import Inventario, Nodo
from model.Diario import Diario
from model.Entidades import ObjetoInstancia
from adapters.guardadoBinario import guardadoBinario
from adapters.guardadoPartida import guardadoPartida
from tests.FuentePrueba import FuentePrueba


class TestCacheCasosBorde(unittest.TestCase):
    """Pruebas de borde para la caché LRU de fichas de catálogo (§4.4)."""

    def test_cache_capacidad_minima_uno(self):
        """Con capacidad_maxima=1, cada nueva inserción debe desalojar la anterior si no está en uso."""
        cache = CacheCatalogo(capacidad_maxima=1)
        cache.insertar("f1", {"id": "f1", "nombre": "Ficha 1"})
        self.assertEqual(cache.cantidad_actual, 1)
        self.assertIsNotNone(cache.obtener("f1"))

        # Insertar f2: desaloja f1
        cache.insertar("f2", {"id": "f2", "nombre": "Ficha 2"})
        self.assertEqual(cache.cantidad_actual, 1)
        self.assertIsNone(cache.obtener("f1"))
        self.assertIsNotNone(cache.obtener("f2"))
        self.assertEqual(cache.desalojos, 1)

    def test_cache_todas_en_uso_inhibe_desalojo_y_registra_sobre_tope(self):
        """Si todas las fichas están en uso, ninguna puede ser expulsada y la caché supera el tope."""
        cache = CacheCatalogo(capacidad_maxima=2)
        cache.insertar("f1", {"id": "f1", "nombre": "Ficha 1"})
        cache.insertar("f2", {"id": "f2", "nombre": "Ficha 2"})

        # Marcar ambas fichas como activamente en uso por el juego (+1 referencia)
        cache.marcar_en_uso("f1", 1)
        cache.marcar_en_uso("f2", 1)

        # Intentar insertar una tercera ficha: no puede desalojar ni f1 ni f2
        cache.insertar("f3", {"id": "f3", "nombre": "Ficha 3"})

        # La capacidad se supera temporalmente para no violar la integridad referencial
        self.assertEqual(cache.cantidad_actual, 3)
        self.assertIsNotNone(cache.obtener("f1"))
        self.assertIsNotNone(cache.obtener("f2"))
        self.assertIsNotNone(cache.obtener("f3"))

    def test_cache_lru_actualiza_orden_en_acierto(self):
        """Un acierto (obtener) debe renovar la frescura, convirtiendo a la otra en la menos usada."""
        cache = CacheCatalogo(capacidad_maxima=2)
        cache.insertar("f1", {"id": "f1", "nombre": "Ficha 1"})
        cache.insertar("f2", {"id": "f2", "nombre": "Ficha 2"})

        # Acceder a f1 para renovar su frescura (LRU)
        _ = cache.obtener("f1")

        # Ahora f2 es la menos recientemente usada; insertar f3 debe desalojar f2
        cache.insertar("f3", {"id": "f3", "nombre": "Ficha 3"})
        self.assertIsNotNone(cache.obtener("f1"))
        self.assertIsNotNone(cache.obtener("f3"))
        self.assertIsNone(cache.obtener("f2"))
        self.assertEqual(cache.desalojos, 1)


class TestClienteHttpRobustez(unittest.TestCase):
    """Pruebas de robustez y clasificación de errores para ClienteHTTP."""

    def setUp(self):
        self.cliente = ClienteHTTP("http://servidor-falso.local/api", timeout=2)

    @patch("requests.get")
    def test_peticion_exitosa_200(self, mockGet):
        mockResp = MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {"estado": "ok"}
        mockResp.content = b'{"estado": "ok"}'
        mockGet.return_value = mockResp

        res = self.cliente._hacerPeticionSegura("/prueba")
        self.assertEqual(res, {"estado": "ok"})
        self.assertEqual(self.cliente.solicitudesRealizadas, 1)

    @patch("requests.get")
    def test_peticion_json_invalido_lanza_error_respuesta_invalida(self, mockGet):
        mockResp = MagicMock()
        mockResp.status_code = 200
        mockResp.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)
        mockResp.content = b"<html>Error 502 Bad Gateway</html>"
        mockResp.text = "<html>Error 502 Bad Gateway</html>"
        mockGet.return_value = mockResp

        with self.assertRaises(ErrorRespuestaInvalida):
            self.cliente._hacerPeticionSegura("/ruta-corrupta")

    @patch("requests.get")
    def test_error_http_404_lanza_error_especifico(self, mockGet):
        mockResp = MagicMock()
        mockResp.status_code = 404
        mockResp.text = "Cripta inexistente"
        mockGet.return_value = mockResp

        with self.assertRaises(ErrorHttp) as ctx:
            self.cliente.obtenerDatosGenerales("cripta-fantasma")
        self.assertEqual(ctx.exception.codigo, 404)

    @patch("requests.get")
    def test_error_http_500_servidor_lanza_error_http(self, mockGet):
        mockResp = MagicMock()
        mockResp.status_code = 500
        mockResp.text = "Internal Server Error"
        mockGet.return_value = mockResp

        with self.assertRaises(ErrorHttp) as ctx:
            self.cliente.obtenerVersionCatalogo()
        self.assertEqual(ctx.exception.codigo, 500)

    @patch("requests.get")
    def test_timeout_lanza_error_tiempo_espera(self, mockGet):
        mockGet.side_effect = requests.exceptions.Timeout("Read timed out")

        with self.assertRaises(ErrorTiempoEspera):
            self.cliente._hacerPeticionSegura("/lenta")

    @patch("requests.get")
    def test_fallo_conexion_lanza_error_conexion_servidor(self, mockGet):
        mockGet.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with self.assertRaises(ErrorConexionServidor):
            self.cliente._hacerPeticionSegura("/desconectado")

    @patch("time.sleep")
    @patch("requests.get")
    def test_reintentos_429_maximo_superado(self, mockGet, mockSleep):
        mockResp429 = MagicMock()
        mockResp429.status_code = 429
        mockResp429.json.return_value = {"reintentar_en": 1}
        mockGet.return_value = mockResp429

        with self.assertRaises(ErrorLimiteFrecuenciaExcedido):
            self.cliente._hacerPeticionSegura("/saturada")
        self.assertGreater(mockSleep.call_count, 4)


class TestPersistenciaIncompatibilidad(unittest.TestCase):
    """Pruebas de validación de formato binario e incompatibilidades de versión."""

    def test_guardado_binario_rechaza_magic_invalido(self):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            # Escribir magic falso "MALO"
            tf.write(b"MALO\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            nombreTemp = tf.name

        try:
            gb = guardadoBinario()
            with self.assertRaises(ValueError) as ctx:
                gb.cargarSala(nombreTemp, 1)
            self.assertIn("inválido", str(ctx.exception))
        finally:
            if os.path.exists(nombreTemp):
                os.remove(nombreTemp)

    def test_guardado_partida_rechaza_version_2_parte_1(self):
        """Un archivo guardado de la primera parte (v2) debe ser explícitamente rechazado (§3.6)."""
        import tempfile
        from adapters.guardadoPartida import ENCABEZADO
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            # MAGIC "CRPS", Version 2 (Parte I)
            tf.write(ENCABEZADO.pack(b"CRPS", 2, 0, 0, 0))
            nombreTemp = tf.name

        try:
            gp = guardadoPartida("cripta-01", "v1", "v1")
            with self.assertRaises(ValueError) as ctx:
                with open(nombreTemp, "rb") as f:
                    gp._leerEncabezado(f)
            self.assertIn("versión 2", str(ctx.exception))
        finally:
            if os.path.exists(nombreTemp):
                os.remove(nombreTemp)


class TestRetrocesoYLineaTiempoComplejo(unittest.TestCase):
    """Pruebas de la interacción entre pergamino de retroceso y línea de tiempo."""

    def _crearModeloConPergamino(self):
        fuente = FuentePrueba(ancho=4, alto=3, semillaCripta=777)
        datosGen = fuente.datosGenerales()
        datosGen["inventario_max"] = 5
        inventario = Inventario(fuente)
        inventario.configurar(5)
        diario = Diario()
        from model.efectosTrampa import efectosTrampa
        efectos = efectosTrampa()
        modelo = Modelo(fuente, 777, inventario, diario, efectos, kCheckpoint=5)
        efectos.registrarEn(modelo)
        modelo.iniciarPartida()

        # Otorgar un pergamino al jugador (en FuentePrueba se llama 'itm_pergamino')
        pergamino = ObjetoInstancia("itm_pergamino", 9999)
        nodo = Nodo(pergamino)
        modelo.inventario._enlazarDespues(nodo, modelo.inventario.cola)
        return modelo

    def test_retroceso_trunca_linea_tiempo_exactamente(self):
        """Las acciones revertidas con retroceso deben desaparecer de la línea de tiempo (§3.6)."""
        modelo = self._crearModeloConPergamino()
        self.assertEqual(modelo.jugador.acciones, 0)

        # Realizar 2 esperas
        modelo.ejecutar(Accion(ACC_ESPERAR))
        relojAccion1 = modelo.reloj
        modelo.ejecutar(Accion(ACC_ESPERAR))
        self.assertEqual(modelo.jugador.acciones, 2)
        self.assertEqual(len(modelo.lineaTiempo._acciones), 2)

        # Consultar historia de acción #2 antes de retroceder
        resAct2 = modelo.consultarHistoriaAccion(2)
        self.assertIn("Acción #2", resAct2)

        # Usar pergamino de retroceso (revierte acción #2)
        resRetroceso = modelo.ejecutar(Accion(ACC_RETROCESO))
        self.assertTrue(resRetroceso.ok)
        self.assertEqual(modelo.jugador.acciones, 1)

        # La línea de tiempo debe tener solo 1 acción registrada
        self.assertEqual(len(modelo.lineaTiempo._acciones), 1)

        # Consultar la acción 3 ahora debe ser rechazada porque solo hay 1 acción registrada
        with self.assertRaises(ValueError):
            modelo.consultarHistoriaAccion(3)

        # Consultar instante posterior al reloj actual debe ser rechazado (§3.6)
        with self.assertRaises(ValueError):
            modelo.consultarHistoriaTiempo(modelo.reloj + 1000)


if __name__ == "__main__":
    unittest.main()
