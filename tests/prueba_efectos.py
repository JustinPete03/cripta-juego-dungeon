from model.efectos import Veneno, Regeneracion, Antorcha, CambioVelocidad
from tests.agenda_falsa import AgendaFalsa


class Actor:
    def __init__(self, vida=30, vida_max=30, velocidad=100):
        self.vida = vida
        self.vida_max = vida_max
        self.velocidad = velocidad
        self.evento_accion = None


def test_veneno_completo():
    # Pulsos en 80, 160, 240, 320 y 400 (dura 400): 5 pulsos de 2 de daño
    a, ag = Actor(), AgendaFalsa()
    Veneno(a, 2).activar(ag)
    ag.avanzar_hasta(1000)
    assert a.vida == 30 - 2 * 5


def test_veneno_cancelado():
    # Antidoto después del pulso de 160: los pulsos futuros no hacen daño
    a, ag = Actor(), AgendaFalsa()
    v = Veneno(a, 2)
    v.activar(ag)
    ag.avanzar_hasta(170)
    v.cancelar(ag)
    ag.avanzar_hasta(1000)
    assert a.vida == 30 - 2 * 2
    assert not v.activo


def test_regeneracion_con_tope():
    # Pulsos en 200, 400, 600...: 10 + 4 + 4 = 18
    a, ag = Actor(vida=10), AgendaFalsa()
    Regeneracion(a, 4).activar(ag)
    ag.avanzar_hasta(400)
    assert a.vida == 18
    ag.avanzar_hasta(2000)
    assert a.vida == a.vida_max      # nunca lo supera


def test_antorcha():
    a, ag = Actor(), AgendaFalsa()
    t = Antorcha(a, 2000)
    t.activar(ag)
    ag.avanzar_hasta(1999)
    assert t.activo
    ag.avanzar_hasta(2000)
    assert not t.activo


def test_cambio_velocidad():
    a, ag = Actor(), AgendaFalsa()
    a.evento_accion = ag.programar(1000, lambda agenda: None)
    ef = CambioVelocidad(a, 200, 300)
    ef.activar(ag)
    # Restante 1000 a velocidad 100 -> 1000*100//200 = 500
    assert a.velocidad == 200
    assert a.evento_accion.tiempo == 500
    ag.avanzar_hasta(300)             # termina el efecto
    # En t=300 quedan 200; (200*200)//100 = 400 -> tiempo 700
    assert a.velocidad == 100
    assert a.evento_accion.tiempo == 700


if __name__ == "__main__":
    test_veneno_completo()
    test_veneno_cancelado()
    test_regeneracion_con_tope()
    test_antorcha()
    test_cambio_velocidad()
    print("Todos los efectos OK")