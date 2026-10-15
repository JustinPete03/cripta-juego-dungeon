import struct
import os

from adapters.guardado_binario import GuardadoBinario
from model.efectos import Veneno, CambioVelocidad
from tests.agenda_falsa import AgendaFalsa


class Actor:
    def __init__(self, vida=30, vida_max=30, velocidad=100):
        self.vida = vida
        self.vida_max = vida_max
        self.velocidad = velocidad
        self.evento_accion = None


def test_veneno_mata_al_actor():
    # vida 3, daño 2: pulso 80 -> 1, pulso 160 -> 0. Nunca baja de 0
    # y no hay más pulsos después.
    a, ag = Actor(vida=3), AgendaFalsa()
    v = Veneno(a, 2)
    v.activar(ag)
    ag.avanzar_hasta(1000)
    assert a.vida == 0
    assert not v.activo


def test_velocidad_termina_antes_de_la_accion():
    # Acción en 1000 a velocidad 100. El efecto (velocidad 200, dura 300)
    # termina en t=300, antes de que llegue la acción.
    a, ag = Actor(), AgendaFalsa()
    a.evento_accion = ag.programar(1000, lambda agenda: None)
    CambioVelocidad(a, 200, 300).activar(ag)
    assert a.evento_accion.tiempo == 500        # 1000*100//200
    ag.avanzar_hasta(300)
    assert a.velocidad == 100                   # restaurada
    assert a.evento_accion.tiempo == 700        # t=300, restante 200*200//100=400


def test_velocidad_cancelada_a_mitad():
    a, ag = Actor(), AgendaFalsa()
    a.evento_accion = ag.programar(1000, lambda agenda: None)
    ef = CambioVelocidad(a, 200, 300)
    ef.activar(ag)                              # acción pasa a 500
    ag.avanzar_hasta(100)
    ef.cancelar(ag)                             # restante (500-100)*200//100 = 800
    assert a.velocidad == 100
    assert a.evento_accion.tiempo == 900
    ag.avanzar_hasta(1000)
    assert a.velocidad == 100                   # el fin del efecto ya no actúa


def test_velocidad_sin_accion_programada():
    a, ag = Actor(), AgendaFalsa()
    CambioVelocidad(a, 200, 300).activar(ag)    # no debe fallar
    ag.avanzar_hasta(300)
    assert a.velocidad == 100


def test_guardado_sala_con_enemigos_y_objetos():
    salas = [
        (1, [], []),
        (2, [("e-201", "ent_rata_gigante", 12), ("e-202", "ent_rata_gigante", 7)],
            ["itm_daga_oxidada", "itm_antorcha"]),
        (5, [], ["itm_antorcha"]),
    ]
    g = GuardadoBinario()
    g.guardar("t.sav", salas)
    assert g.cargar_sala("t.sav", 2) == salas[1]
    assert g.cargar_sala("t.sav", 99) is None
    assert g.cargar_todo("t.sav") == salas


def test_guardado_version_incompatible():
    g = GuardadoBinario()
    g.guardar("t.sav", [(1, [], [])])
    with open("t.sav", "r+b") as f:
        f.seek(4)                               # justo después de "CRPT"
        f.write(struct.pack("<H", 99))
    try:
        g.cargar_sala("t.sav", 1)
        raise AssertionError("debió rechazar la versión")
    except ValueError as e:
        assert "incompatible" in str(e)


def test_guardado_archivo_invalido():
    with open("t.sav", "wb") as f:
        f.write(b"basura" * 10)
    try:
        GuardadoBinario().cargar_sala("t.sav", 1)
        raise AssertionError("debió rechazar el archivo")
    except ValueError:
        pass


if __name__ == "__main__":
    try:
        test_veneno_mata_al_actor()
        test_velocidad_termina_antes_de_la_accion()
        test_velocidad_cancelada_a_mitad()
        test_velocidad_sin_accion_programada()
        test_guardado_sala_con_enemigos_y_objetos()
        test_guardado_version_incompatible()
        test_guardado_archivo_invalido()
        print("Apéndice B OK")
    finally:
        if os.path.exists("t.sav"):
            os.remove("t.sav")