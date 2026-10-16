from model.Constantes import EV_JUGADOR
from model.Entidades import Enemigo
from model.efectos import EfectosJuego
from tests.modelo_falso import ModeloFalso


def nuevo(fichas=None):
    ef = EfectosJuego()
    return ModeloFalso(ef, fichas), ef


def test_veneno_completo():
    m, ef = nuevo()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correr_hasta(1000)
    assert m.jugador.vida == 30 - 2 * 5          # pulsos en 80,160,240,320,400
    assert ef.activos == []


def test_antidoto_cancela_pulsos_futuros():
    m, ef = nuevo()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correr_hasta(170)                           # pulsos en 80 y 160
    assert ef.curarVeneno(m, m.jugador) is True
    m.correr_hasta(1000)
    assert m.jugador.vida == 30 - 2 * 2
    assert ef.curarVeneno(m, m.jugador) is False  # ya no hay veneno


def test_veneno_mata_al_actor():
    m, ef = nuevo()
    m.jugador.vida = 3
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correr_hasta(1000)
    assert m.jugador.vida == 0 and not m.jugador.vivo
    assert ef.activos == []
    assert m.agenda.pendientesValidos() == []     # no quedan pulsos pendientes


def test_regeneracion_con_tope():
    m, ef = nuevo()
    rata = Enemigo("e-1", "ent_rata", "Rata", "guardián", 10, 30, 5, 1, 100)
    ef.aplicarRegeneracion(m, rata, 4)
    m.correr_hasta(401)                           # pulsos en 200 y 400
    assert rata.vida == 18                        # 10 + 4 + 4
    m.correr_hasta(2000)
    assert rata.vida == rata.vidaMax              # nunca lo supera


def test_regeneracion_se_activa_con_el_enemigo():
    m, ef = nuevo({"ent_rata": {"regeneracion": 4}})
    rata = Enemigo("e-1", "ent_rata", "Rata", "guardián", 10, 30, 5, 1, 100)
    ef.alActivarEnemigo(m, rata)
    m.correr_hasta(200)
    assert rata.vida == 14


def test_muerte_cancela_regeneracion():
    m, ef = nuevo()
    rata = Enemigo("e-1", "ent_rata", "Rata", "guardián", 10, 30, 5, 1, 100)
    ef.aplicarRegeneracion(m, rata, 4)
    m.aplicarDanio(rata, 10)                      # muere
    m.correr_hasta(1000)
    assert rata.vida == 0 and ef.activos == []


def test_antorcha():
    m, ef = nuevo()
    ef.encenderAntorcha(m, m.jugador, 2000)
    m.correr_hasta(1999)
    assert ef.antorchaEncendida(m.jugador)
    m.correr_hasta(2000)
    assert not ef.antorchaEncendida(m.jugador)


def test_velocidad_y_su_fin():
    m, ef = nuevo()
    m.jugador.evento = m.programarEvento(1000, EV_JUGADOR, m.jugador)
    ef.aplicarVelocidad(m, m.jugador, 200, 300)
    assert m.jugador.velocidad == 200
    assert m.jugador.evento.tiempo == 500         # 1000*100//200
    m.correr_hasta(300)
    assert m.jugador.velocidad == 100
    assert m.jugador.evento.tiempo == 700         # (500-300)*200//100 = 400


def test_velocidad_cancelada_a_mitad():
    m, ef = nuevo()
    m.jugador.evento = m.programarEvento(1000, EV_JUGADOR, m.jugador)
    ef.aplicarVelocidad(m, m.jugador, 200, 300)
    m.correr_hasta(100)
    ef.cancelar(m, ef.activosDe(m.jugador)[0])
    assert m.jugador.velocidad == 100
    assert m.jugador.evento.tiempo == 900         # (500-100)*200//100 = 800


def test_retroceso_veneno():
    m, ef = nuevo()
    marca = m.marca()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correr_hasta(170)
    assert m.jugador.vida == 26
    m.retroceder_hasta(marca)
    assert m.jugador.vida == 30
    assert ef.activos == []
    assert m.agenda.pendientesValidos() == []


def test_retroceso_velocidad():
    m, ef = nuevo()
    original = m.programarEvento(1000, EV_JUGADOR, m.jugador)
    m.jugador.evento = original
    marca = m.marca()
    ef.aplicarVelocidad(m, m.jugador, 200, 300)
    m.correr_hasta(100)
    m.retroceder_hasta(marca)
    assert m.jugador.velocidad == 100
    assert m.jugador.evento is original
    assert original.tiempo == 1000 and not original.cancelado
    assert ef.activos == []


def test_reaplicar_veneno_reinicia():
    m, ef = nuevo()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correr_hasta(100)                           # 1 pulso
    ef.aplicarVeneno(m, m.jugador, 3)             # reinicia: 5 pulsos de 3 desde t=100
    m.correr_hasta(1000)
    assert m.jugador.vida == 30 - 2 - 3 * 5
    assert len(ef.activos) == 0


def test_descripcion_para_la_vista():
    m, ef = nuevo()
    assert ef.descripcionjugador(m) == []
    ef.aplicarVeneno(m, m.jugador, 2)
    ef.encenderAntorcha(m, m.jugador, 2000)
    m.correr_hasta(100)
    textos = ef.descripcionjugador(m)
    assert len(textos) == 2
    assert "Veneno" in textos[0] and "quedan 300" in textos[0]
    assert "Antorcha" in textos[1] and "quedan 1900" in textos[1]


def test_usar_antidoto():
    m, ef = nuevo()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correr_hasta(100)                           # 1 pulso
    ef.alUsarObjeto(m, {"clase": "antidoto", "nombre": "Antídoto"})
    m.correr_hasta(1000)
    assert m.jugador.vida == 28 and ef.activos == []


def test_usar_antidoto_sin_veneno_no_falla():
    m, ef = nuevo()
    ef.alUsarObjeto(m, {"clase": "antidoto", "nombre": "Antídoto"})
    assert ef.activos == []


def test_usar_antorcha():
    m, ef = nuevo()
    ef.alUsarObjeto(m, {"clase": "antorcha", "duracion": 2000})
    assert ef.antorchaEncendida(m.jugador)
    m.correr_hasta(2000)
    assert not ef.antorchaEncendida(m.jugador)


def test_usar_pocion_de_velocidad():
    m, ef = nuevo()
    m.jugador.evento = m.programarEvento(1000, EV_JUGADOR, m.jugador)
    ef.alUsarObjeto(m, {"clase": "pocion", "modificador_velocidad": 2, "duracion": 300})
    assert m.jugador.velocidad == 200
    m.correr_hasta(300)
    assert m.jugador.velocidad == 100


def test_pocion_de_curacion_no_crea_efectos():
    m, ef = nuevo()
    ef.alUsarObjeto(m, {"clase": "pocion", "cura": 10})   # la cura la hace el inventario
    assert ef.activos == []


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test_"):
            f()
            print("OK", nombre)
    print("Efectos OK")