# Pruebas de aceptación y unitarias para Línea de Tiempo y Puntos de Control (§3.6, §5.5, FR-029 a FR-038).

import pytest
import os
import struct

from tests.FuentePrueba import FuentePrueba
from model.Acciones import Accion
from model.Constantes import (ACC_MOVER, ACC_ESPERAR, ACC_RETROCESO, EN_CURSO)
from model.Inventario import Inventario
from model.Diario import Diario
from model.efectosTrampa import efectosTrampa
from model.Juego import Modelo
from model.LineaTiempo import LineaTiempo


def _crearPartidaPrueba(ancho=4, alto=3, semilla=2026, checkpointCada=5):
    proveedor = FuentePrueba(ancho=ancho, alto=alto, semillaCripta=semilla)
    efectos = efectosTrampa()
    modelo = Modelo(proveedor, semilla, Inventario(proveedor), Diario(), efectos, kCheckpoint=checkpointCada)
    efectos.registrarEn(modelo)
    modelo.iniciarPartida()
    return modelo


def test_punto_control_inicial_y_frecuencia_k():
    """FR-029, FR-036: Se registra checkpoint en acción 0 y luego exactamente cada K acciones."""
    modelo = _crearPartidaPrueba(checkpointCada=3)
    lt = modelo.lineaTiempo

    # Checkpoint inicial en acción 0
    assert lt.cantidadPuntosControl() == 1
    assert lt._puntosControl[0].numAccion == 0

    # Ejecutar 2 acciones
    modelo.ejecutar(Accion(ACC_ESPERAR))
    modelo.ejecutar(Accion(ACC_ESPERAR))
    assert lt.cantidadPuntosControl() == 1  # aún no llega a K=3

    # Ejecutar la 3ra acción -> debe crear checkpoint
    modelo.ejecutar(Accion(ACC_ESPERAR))
    assert lt.cantidadPuntosControl() == 2
    assert lt._puntosControl[1].numAccion == 3

    # Ejecutar 3 acciones más -> nuevo checkpoint en acción 6
    modelo.ejecutar(Accion(ACC_ESPERAR))
    modelo.ejecutar(Accion(ACC_ESPERAR))
    modelo.ejecutar(Accion(ACC_ESPERAR))
    assert lt.cantidadPuntosControl() == 3
    assert lt._puntosControl[2].numAccion == 6


def test_consulta_historia_accion_k():
    """FR-031, FR-037: historia #k muestra el estado justo antes de la acción k."""
    modelo = _crearPartidaPrueba(checkpointCada=2)
    # Sala inicial es 1.
    assert modelo.jugador.sala.id == 1

    # Realizar movimiento a Sala 5 (sur)
    modelo.ejecutar(Accion(ACC_MOVER, "S"))
    assert modelo.jugador.sala.id == 5

    # Realizar movimiento a Sala 6 (este)
    modelo.ejecutar(Accion(ACC_MOVER, "E"))
    assert modelo.jugador.sala.id == 6

    # Consultar estado antes de la acción #1: jugador debe estar en Sala 1
    res1 = modelo.consultarHistoriaAccion(1)
    assert "Sala actual: Sala 1" in res1
    assert "Acción #1" in res1

    # Consultar estado antes de la acción #2: jugador debe estar en Sala 5
    res2 = modelo.consultarHistoriaAccion(2)
    assert "Sala actual: Sala 5" in res2
    assert "Acción #2" in res2

    # Consultar estado antes de la acción #3 (actual): jugador debe estar en Sala 6
    res3 = modelo.consultarHistoriaAccion(3)
    assert "Sala actual: Sala 6" in res3
    assert "Acción #3" in res3


def test_consulta_historia_tiempo_t():
    """FR-030: historia <t> muestra el estado en el instante t."""
    modelo = _crearPartidaPrueba(checkpointCada=5)
    tInicio = modelo.reloj
    assert tInicio == 0

    # Esperar 2 turnos (cada esperar cuesta 100)
    modelo.ejecutar(Accion(ACC_ESPERAR))
    t1 = modelo.reloj
    assert t1 == 100

    modelo.ejecutar(Accion(ACC_ESPERAR))
    t2 = modelo.reloj
    assert t2 == 200

    # Consultar en t=0
    res0 = modelo.consultarHistoriaTiempo(0)
    assert "Reloj: 0" in res0

    # Consultar en t=100
    res1 = modelo.consultarHistoriaTiempo(100)
    assert "Reloj: 100" in res1

    # Consultar en t=200
    res2 = modelo.consultarHistoriaTiempo(200)
    assert "Reloj: 200" in res2


def test_rechazo_consultas_futuras_e_invalidas():
    """FR-033: historia con t > reloj o k inválido se rechaza con error."""
    modelo = _crearPartidaPrueba()
    modelo.ejecutar(Accion(ACC_ESPERAR))

    # Reloj actual es 100, consultar t=150 debe fallar
    with pytest.raises(ValueError) as exc:
        modelo.consultarHistoriaTiempo(150)
    assert "No se puede consultar el futuro" in str(exc.value)

    # Solo se ha hecho 1 acción (pendiente acción #2), consultar acción #5 debe fallar
    with pytest.raises(ValueError) as excAcc:
        modelo.consultarHistoriaAccion(5)
    assert "No se puede consultar la acción #5" in str(excAcc.value)

    # Consultar acción #0 o negativa debe fallar
    with pytest.raises(ValueError):
        modelo.consultarHistoriaAccion(0)


def test_no_interferencia_con_partida():
    """FR-032: Las consultas no alteran tiempo, estado ni registro."""
    modelo = _crearPartidaPrueba()
    modelo.ejecutar(Accion(ACC_ESPERAR))
    relojAntes = modelo.reloj
    accionesAntes = modelo.jugador.acciones
    vidaAntes = modelo.jugador.vida

    # Realizar múltiples consultas
    _ = modelo.consultarHistoriaTiempo(0)
    _ = modelo.consultarHistoriaAccion(1)

    # Estado del modelo vivo debe permanecer estrictamente intacto
    assert modelo.reloj == relojAntes
    assert modelo.jugador.acciones == accionesAntes
    assert modelo.jugador.vida == vidaAntes


def test_interaccion_con_pergamino_retroceso():
    """FR-034: El retroceso descarta las acciones y checkpoints anulados."""
    modelo = _crearPartidaPrueba(checkpointCada=2)
    # Ejecutar 4 acciones
    modelo.ejecutar(Accion(ACC_ESPERAR)) # acción 1
    modelo.ejecutar(Accion(ACC_ESPERAR)) # acción 2 (checkpoint 2)
    modelo.ejecutar(Accion(ACC_ESPERAR)) # acción 3
    modelo.ejecutar(Accion(ACC_ESPERAR)) # acción 4 (checkpoint 4)

    assert modelo.lineaTiempo.cantidadAcciones() == 4
    assert modelo.lineaTiempo.cantidadPuntosControl() == 3 # cp 0, 2, 4
    relojAntes = modelo.reloj

    # Dar pergamino de retroceso al jugador
    from model.Entidades import ObjetoInstancia
    from model.Inventario import Nodo
    modelo.inventario._enlazarDespues(Nodo(ObjetoInstancia("itm_pergamino", 999)), modelo.inventario.cola)

    # Retroceder 1 acción
    res = modelo.ejecutar(Accion(ACC_RETROCESO))
    assert res.ok is True
    assert modelo.jugador.acciones == 3
    assert modelo.reloj < relojAntes

    # La línea de tiempo debe haberse recortado a 3 acciones
    assert modelo.lineaTiempo.cantidadAcciones() == 3
    # El checkpoint 4 debió ser descartado
    assert modelo.lineaTiempo.cantidadPuntosControl() == 2 # cp 0, 2

    # Consultar el tiempo anterior al retroceso ahora es considerado futuro
    with pytest.raises(ValueError):
        modelo.consultarHistoriaTiempo(relojAntes)


def test_persistencia_guardado_y_carga_linea_tiempo(tmp_path):
    """FR-038: Guardar y cargar preserva la línea de tiempo completa."""
    from adapters.guardadoPartida import guardadoPartida

    rutaGuardado = str(tmp_path / "partida_v3.crps")
    modelo = _crearPartidaPrueba(checkpointCada=2)
    modelo.ejecutar(Accion(ACC_MOVER, "E"))
    modelo.ejecutar(Accion(ACC_MOVER, "E"))

    guardador = guardadoPartida("cripta-prueba", "v1", "cat-v1")
    guardador.guardar(modelo, rutaGuardado)

    # Nuevo modelo vacío
    modeloNuevo = _crearPartidaPrueba(checkpointCada=2)
    guardador.cargar(modeloNuevo, rutaGuardado)

    # Verificar que el modelo nuevo puede consultar historia de acciones previas al guardado
    resAcc1 = modeloNuevo.consultarHistoriaAccion(1)
    assert "Sala actual: Sala 1" in resAcc1
    resAcc2 = modeloNuevo.consultarHistoriaAccion(2)
    assert "Sala actual: Sala 2" in resAcc2


def test_incompatibilidad_formato_guardado_parte_1(tmp_path):
    """FR-038: Cargar un archivo con versión de formato 2 (Parte I) es rechazado explícitamente."""
    from adapters.guardadoPartida import guardadoPartida, MAGIC, ENCABEZADO

    rutaIncompatible = str(tmp_path / "partida_v2.crps")
    # Crear archivo binario simulando versión 2
    with open(rutaIncompatible, "wb") as f:
        # encabezado con version=2
        f.write(ENCABEZADO.pack(MAGIC, 2, 0, 0, 0))

    modelo = _crearPartidaPrueba()
    guardador = guardadoPartida()

    with pytest.raises(ValueError) as exc:
        guardador.cargar(modelo, rutaIncompatible)

    assert "Formato incompatible" in str(exc.value)
    assert "Parte I" in str(exc.value)


def test_controlador_comando_historia(capsys):
    """FR-030, FR-031: Comando interactivo 'historia' en ControladorJuego."""
    from controller.ControladorJuego import Controlador
    from view.Consola import VistaConsola

    modelo = _crearPartidaPrueba()
    modelo.ejecutar(Accion(ACC_ESPERAR))

    controlador = Controlador(modelo, VistaConsola())

    # Probar historia 0
    controlador.procesar("historia 0")
    out, _ = capsys.readouterr()
    assert "=== HISTORIA: Estado en Reloj: 0 ===" in out

    # Probar historia #1
    controlador.procesar("historia #1")
    out, _ = capsys.readouterr()
    assert "=== HISTORIA: Estado antes de Acción #1" in out

    # Probar historia futuro
    controlador.procesar("historia 9999")
    out, _ = capsys.readouterr()
    assert "Error en historia: No se puede consultar el futuro" in out


def test_replay_hasta_no_interactivo(capsys):
    """FR-035: Replay no interactivo con --hasta <t>."""
    from controller.ControladorJuego import Controlador

    modelo = _crearPartidaPrueba()
    controlador = Controlador(modelo)

    acciones = ["mover E", "esperar", "esperar"]
    # Reproducir hasta t=100
    ok, _ = controlador.reproducirHasta(acciones, 100)
    assert ok is True
    out, _ = capsys.readouterr()
    assert "=== HISTORIA: Estado en Reloj: 100 ===" in out


def test_replay_hasta_posterior_a_fin_de_partida(capsys):
    """FR-035: Replay con t posterior al final de la partida informa terminación anticipada."""
    from controller.ControladorJuego import Controlador

    modelo = _crearPartidaPrueba()
    controlador = Controlador(modelo)

    ok, _ = controlador.reproducirHasta(["esperar"], 1000)
    assert ok is True
    out, _ = capsys.readouterr()
    assert "La partida terminó antes del instante t=1000" in out


def test_consulta_historia_no_gasta_red_ni_muta_cache():
    """FR-032 / L-03: La consulta de historia no realiza solicitudes de red ni muta la caché.
    Utiliza un contador real envolviendo los métodos de acceso a datos del proveedor y la caché real,
    comprobando que la prueba falle si se fuerza una solicitud a propósito dentro de una consulta.
    """
    from model.cache_estructuras import CacheCatalogo
    from adapters.ProveedorRed import FichaConCrudo

    class ProveedorConRastreo:
        def __init__(self, fuente, capacidadCache=25):
            self._fuente = fuente
            self.cache = CacheCatalogo(capacidadCache)
            self.solicitudesRed = 0
            self.salasDescargadas = {}

        def __getattr__(self, name):
            return getattr(self._fuente, name)

        def pedirRed(self, endpoint):
            self.solicitudesRed += 1

        def contenidoSala(self, salaId):
            if salaId not in self.salasDescargadas:
                self.pedirRed("contenido_sala_%d" % salaId)
                self.salasDescargadas[salaId] = self._fuente.contenidoSala(salaId)
            return self.salasDescargadas[salaId]

        def ficha(self, tipoId):
            ficha = self.cache.obtener(tipoId)
            if ficha is None:
                self.pedirRed("ficha_%s" % tipoId)
                crudo = self._fuente.ficha(tipoId)
                self.cache.insertar(tipoId, FichaConCrudo(crudo))
                return crudo
            return ficha.crudo

    fuente = FuentePrueba(ancho=4, alto=3, semillaCripta=2026)
    proveedor = ProveedorConRastreo(fuente)

    efectos = efectosTrampa()
    modelo = Modelo(proveedor, 2026, Inventario(proveedor), Diario(), efectos, kCheckpoint=5)
    efectos.registrarEn(modelo)
    modelo.iniciarPartida()

    # Ejecutar varias acciones del juego
    modelo.ejecutar(Accion(ACC_MOVER, "S"))
    modelo.ejecutar(Accion(ACC_MOVER, "E"))
    modelo.ejecutar(Accion(ACC_ESPERAR))

    def verificar_consulta(consulta_fn):
        sol_inicio = proveedor.solicitudesRed
        cache_inicio = proveedor.cache.cantidad_actual
        resultado = consulta_fn()
        if proveedor.solicitudesRed != sol_inicio:
            raise AssertionError(
                "Se detectaron solicitudes de red indebidas durante la consulta histórica (delta=%d)"
                % (proveedor.solicitudesRed - sol_inicio)
            )
        if proveedor.cache.cantidad_actual != cache_inicio:
            raise AssertionError("Se detectó mutación indebida de la caché durante la consulta histórica")
        return resultado

    # 1. Las consultas legítimas pasan estrictamente sin emitir solicitudes ni alterar la caché
    verificar_consulta(lambda: modelo.consultarHistoriaTiempo(0))
    verificar_consulta(lambda: modelo.consultarHistoriaTiempo(100))
    verificar_consulta(lambda: modelo.consultarHistoriaAccion(1))
    verificar_consulta(lambda: modelo.consultarHistoriaAccion(2))
    verificar_consulta(lambda: modelo.consultarHistoriaAccion(3))

    # 2. Comprobar que la prueba FALLA si se fuerza una solicitud a propósito dentro de una consulta
    def consulta_con_solicitud_forzada():
        res = modelo.consultarHistoriaTiempo(0)
        proveedor.pedirRed("solicitud_forzada_ilegitima")
        return res

    with pytest.raises(AssertionError, match="solicitudes de red indebidas"):
        verificar_consulta(consulta_con_solicitud_forzada)


def test_invariantes_puntos_control():
    """FR-029, FR-036: Invariantes de puntos de control (punto 0 presente, orden creciente de acciones y reloj)."""
    modelo = _crearPartidaPrueba(checkpointCada=3)
    lt = modelo.lineaTiempo

    # Invariante 1: Siempre existe el punto de control 0 al iniciar
    assert lt.cantidadPuntosControl() >= 1
    cp0 = lt._puntosControl[0]
    assert cp0.numAccion == 0
    assert cp0.reloj == modelo.reloj

    # Ejecutar múltiples acciones para generar varios puntos de control
    for _ in range(12):
        modelo.ejecutar(Accion(ACC_ESPERAR))

    # Deben existir varios puntos (0, 3, 6, 9, 12)
    assert lt.cantidadPuntosControl() == 5

    # Invariante 2 y 3: Orden estrictamente creciente de numAccion y monótono creciente de reloj
    for i in range(1, len(lt._puntosControl)):
        anterior = lt._puntosControl[i - 1]
        actual = lt._puntosControl[i]
        assert actual.numAccion > anterior.numAccion
        assert actual.reloj >= anterior.reloj


def test_consulta_historia_accion_k_pendiente_muestra_estado_actual():
    """FR-031: historia #k con k = acciones realizadas + 1 muestra el estado actual antes de la decisión."""
    modelo = _crearPartidaPrueba()
    # 0 acciones realizadas: k = 1 es la acción pendiente (estado actual inicial)
    assert modelo.jugador.acciones == 0
    resInicial = modelo.consultarHistoriaAccion(1)
    assert "Acción #1" in resInicial
    assert "Sala actual: Sala 1" in resInicial
    assert "Reloj: %d" % modelo.reloj in resInicial

    # Ejecutar 2 acciones
    modelo.ejecutar(Accion(ACC_MOVER, "S"))
    modelo.ejecutar(Accion(ACC_MOVER, "E"))
    assert modelo.jugador.acciones == 2

    # Con 2 acciones realizadas, k = 3 es la acción pendiente actual
    resPendiente = modelo.consultarHistoriaAccion(3)
    assert "Acción #3" in resPendiente
    assert "Sala actual: Sala %d" % modelo.jugador.sala.id in resPendiente
    assert "Reloj: %d" % modelo.reloj in resPendiente


def test_consulta_historia_limites_t0_y_negativos():
    """FR-033: t < 0 y k < 0 se rechazan con error descriptivo, y t = 0 sí es válido."""
    modelo = _crearPartidaPrueba()
    modelo.ejecutar(Accion(ACC_ESPERAR))

    # t = 0 sí es válido
    resT0 = modelo.consultarHistoriaTiempo(0)
    assert "=== HISTORIA: Estado en Reloj: 0 ===" in resT0

    # t < 0 se rechaza con mensaje de error
    with pytest.raises(ValueError) as excTNeg:
        modelo.consultarHistoriaTiempo(-1)
    assert "El instante de tiempo no puede ser negativo" in str(excTNeg.value)

    with pytest.raises(ValueError) as excTNeg2:
        modelo.consultarHistoriaTiempo(-50)
    assert "El instante de tiempo no puede ser negativo" in str(excTNeg2.value)

    # k < 0 se rechaza con mensaje de error descriptivo
    with pytest.raises(ValueError) as excKNeg:
        modelo.consultarHistoriaAccion(-1)
    assert "No se puede consultar la acción #-1" in str(excKNeg.value)

    with pytest.raises(ValueError) as excKNeg2:
        modelo.consultarHistoriaAccion(-5)
    assert "No se puede consultar la acción #-5" in str(excKNeg2.value)


def test_comparacion_historia_esqueleto_compartido_vs_reconstruccion_completa():
    """FR-030, FR-031, FR-032, T019: Compara el resultado de historia con el esqueleto
    compartido contra el de la reconstrucción completa para varias acciones k y varios
    tiempos t, y comprueba que el modelo vivo permanece intacto sin mutaciones.
    """
    from model.LineaTiempo import _consultarAccionCompleta, _consultarTiempoCompleto

    # Crear una partida con varias acciones y cambios de estado (movimientos y esperas)
    proveedor = FuentePrueba(ancho=6, alto=6, semillaCripta=2026, vidaJugador=100000)
    efectos = efectosTrampa()
    modelo = Modelo(proveedor, 2026, Inventario(proveedor), Diario(), efectos, kCheckpoint=5)
    efectos.registrarEn(modelo)
    modelo.iniciarPartida()
    direcciones = ["S", "E", "S", "O", "N", "E"]
    for i in range(30):
        if i < len(direcciones):
            d = direcciones[i]
            res = modelo.ejecutar(Accion(ACC_MOVER, d))
            if not res.ok:
                modelo.ejecutar(Accion(ACC_ESPERAR))
        else:
            modelo.ejecutar(Accion(ACC_ESPERAR))

    # Guardar snapshot completo del modelo vivo antes de cualquier consulta
    snapshotVivoInicial = modelo.capturarEstado()

    # Comparar múltiples acciones k (cubriendo distintos puntos de control)
    accionesK = [1, 5, 6, 12, 18, 25, 30]
    for k in accionesK:
        resCompartido = modelo.consultarHistoriaAccion(k)
        resCompleto = _consultarAccionCompleta(modelo, k)
        assert resCompartido == resCompleto, (
            "Diferencia en historia #%d entre esqueleto compartido y reconstrucción completa" % k
        )

    # Comparar múltiples instantes de tiempo t
    relojActual = modelo.reloj
    tiemposT = [0, relojActual // 5, relojActual // 2, relojActual * 3 // 4, relojActual]
    for t in tiemposT:
        resCompartido = modelo.consultarHistoriaTiempo(t)
        resCompleto = _consultarTiempoCompleto(modelo, t)
        assert resCompartido == resCompleto, (
            "Diferencia en historia t=%d entre esqueleto compartido y reconstrucción completa" % t
        )

    # Comprobar que el modelo vivo no sufrió ninguna modificación (FR-032)
    snapshotVivoFinal = modelo.capturarEstado()
    assert snapshotVivoInicial == snapshotVivoFinal, "El modelo vivo fue mutado durante las consultas de historia"
