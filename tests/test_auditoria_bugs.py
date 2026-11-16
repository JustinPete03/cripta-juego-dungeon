# Pruebas de regresión y auditoría de casos límite y correcciones de bugs.

import pytest
from tests.FuentePrueba import FuentePrueba
from model.Acciones import Accion
from model.Constantes import ACC_MOVER, EN_CURSO
from model.Salas import IndiceOrdenado
from controller.ControladorJuego import Controlador
from main import armarModelo


class VistaCaptura:
    def __init__(self):
        self.mensajes = []

    def mostrarTexto(self, texto):
        self.mensajes.append(texto)

    def mostrar(self, modelo):
        pass

    def mostrarFinal(self, modelo):
        pass


def _crearControladorPrueba():
    fuente = FuentePrueba(ancho=4, alto=3, semillaCripta=2026)
    modelo = armarModelo(fuente, 2026)
    modelo.iniciarPartida()
    vista = VistaCaptura()
    ctrl = Controlador(modelo, vista)
    return ctrl, modelo, vista


def test_ir_direccion_cardinal_no_choca_con_ir_a():
    """Bug fix: 'ir n', 'ir s', 'ir e', 'ir o' ejecutan movimiento y no 'ir a'."""
    ctrl, modelo, vista = _crearControladorPrueba()
    # Sala inicial es 1. Al este está la Sala 2 (salida abierta).
    assert modelo.jugador.sala.id == 1

    fin = ctrl.procesar("ir e")
    assert fin is False
    assert modelo.jugador.sala.id == 2


def test_ir_a_sin_argumentos():
    """Bug fix: 'ir a' sin destino informa uso y no lanza TypeError."""
    ctrl, modelo, vista = _crearControladorPrueba()
    fin = ctrl.procesar("ir a")
    assert fin is False
    assert any("Uso: ir a <id_sala>" in m for m in vista.mensajes)


def test_ir_a_destino_invalido_texto():
    """Bug fix: 'ir a abc' no lanza TypeError por comparar int con str en IndiceOrdenado."""
    ctrl, modelo, vista = _crearControladorPrueba()
    fin = ctrl.procesar("ir a abc")
    assert fin is False
    assert any("Identificador de sala inválido" in m for m in vista.mensajes)


def test_ir_shorthand_numerico():
    """'ir 2' funciona como abreviatura de 'ir a 2'."""
    ctrl, modelo, vista = _crearControladorPrueba()
    assert modelo.jugador.sala.id == 1
    # La sala 2 no está explorada inicialmente
    ctrl.procesar("ir 2")
    assert any("no explorada" in m for m in vista.mensajes)


def test_indice_ordenado_buscar_tipo_incompatible():
    """IndiceOrdenado.buscar con str sobre índice de enteros devuelve None sin TypeError."""
    indice = IndiceOrdenado()
    indice.insertar(1, "Sala 1")
    indice.insertar(2, "Sala 2")

    assert indice.buscar("abc") is None
    assert indice.buscar(None) is None
    assert indice.buscar(2) == "Sala 2"


def test_historia_tiempo_negativo_rechazado():
    """historia <t> con t < 0 es rechazado con ValueError."""
    _, modelo, _ = _crearControladorPrueba()
    with pytest.raises(ValueError) as exc:
        modelo.consultarHistoriaTiempo(-1)
    assert "no puede ser negativo" in str(exc.value)


def test_reproducir_hasta_negativo_rechazado():
    """Controlador.reproducirHasta con hastaReloj < 0 devuelve error."""
    ctrl, _, _ = _crearControladorPrueba()
    ok, motivo = ctrl.reproducirHasta(["mover E"], -5)
    assert ok is False
    assert "no puede ser negativo" in motivo


def test_minimap_niebla_guerra():
    """La instantánea visual del minimapa utiliza mapaConocido para salas exploradas y puertas."""
    from view.presentacion import celdasDelMapa
    _, modelo, _ = _crearControladorPrueba()

    celdas = celdasDelMapa(modelo)
    assert len(celdas) > 0
    # Sala 1 explorada
    c1 = next(c for c in celdas if c.idSala == 1)
    assert c1.visitada is True
