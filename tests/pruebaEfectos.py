from model.Constantes import EV_JUGADOR
from model.Entidades import Enemigo
from model.efectos import efectosJuego
from tests.modeloFalso import modeloFalso


def nuevo(fichas=None):
    ef = efectosJuego()
    return modeloFalso(ef, fichas), ef


def testVenenoCompleto():
    m, ef = nuevo()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correrHasta(1000)
    assert m.jugador.vida == 30 - 2 * 5          # pulsos en 80,160,240,320,400
    assert ef.activos == []


def testAntidotoCancelaPulsosFuturos():
    m, ef = nuevo()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correrHasta(170)                           # pulsos en 80 y 160
    assert ef.curarVeneno(m, m.jugador) is True
    m.correrHasta(1000)
    assert m.jugador.vida == 30 - 2 * 2
    assert ef.curarVeneno(m, m.jugador) is False  # ya no hay veneno


def testVenenoMataAlActor():
    m, ef = nuevo()
    m.jugador.vida = 3
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correrHasta(1000)
    assert m.jugador.vida == 0 and not m.jugador.vivo
    assert ef.activos == []
    assert m.agenda.pendientesValidos() == []     # no quedan pulsos pendientes


def testRegeneracionConTope():
    m, ef = nuevo()
    rata = Enemigo("e-1", "ent_rata", "Rata", "guardián", 10, 30, 5, 1, 100)
    ef.aplicarRegeneracion(m, rata, 4)
    m.correrHasta(401)                           # pulsos en 200 y 400
    assert rata.vida == 18                        # 10 + 4 + 4
    m.correrHasta(2000)
    assert rata.vida == rata.vidaMax              # nunca lo supera


def testRegeneracionSeActivaConElEnemigo():
    m, ef = nuevo({"ent_rata": {"regeneracion": 4}})
    rata = Enemigo("e-1", "ent_rata", "Rata", "guardián", 10, 30, 5, 1, 100)
    ef.alActivarEnemigo(m, rata)
    m.correrHasta(200)
    assert rata.vida == 14


def testMuerteCancelaRegeneracion():
    m, ef = nuevo()
    rata = Enemigo("e-1", "ent_rata", "Rata", "guardián", 10, 30, 5, 1, 100)
    ef.aplicarRegeneracion(m, rata, 4)
    m.aplicarDanio(rata, 10)                      # muere
    m.correrHasta(1000)
    assert rata.vida == 0 and ef.activos == []


def testAntorcha():
    m, ef = nuevo()
    ef.encenderAntorcha(m, m.jugador, 2000)
    m.correrHasta(1999)
    assert ef.antorchaEncendida(m.jugador)
    m.correrHasta(2000)
    assert not ef.antorchaEncendida(m.jugador)


def testVelocidadYSuFin():
    m, ef = nuevo()
    m.jugador.evento = m.programarEvento(1000, EV_JUGADOR, m.jugador)
    ef.aplicarVelocidad(m, m.jugador, 200, 300)
    assert m.jugador.velocidad == 200
    assert m.jugador.evento.tiempo == 500         # 1000*100//200
    m.correrHasta(300)
    assert m.jugador.velocidad == 100
    assert m.jugador.evento.tiempo == 700         # (500-300)*200//100 = 400


def testVelocidadCanceladaAMitad():
    m, ef = nuevo()
    m.jugador.evento = m.programarEvento(1000, EV_JUGADOR, m.jugador)
    ef.aplicarVelocidad(m, m.jugador, 200, 300)
    m.correrHasta(100)
    ef.cancelar(m, ef.activosDe(m.jugador)[0])
    assert m.jugador.velocidad == 100
    assert m.jugador.evento.tiempo == 900         # (500-100)*200//100 = 800


def testRetrocesoVeneno():
    m, ef = nuevo()
    marca = m.marca()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correrHasta(170)
    assert m.jugador.vida == 26
    m.retrocederHasta(marca)
    assert m.jugador.vida == 30
    assert ef.activos == []
    assert m.agenda.pendientesValidos() == []


def testRetrocesoVelocidad():
    m, ef = nuevo()
    original = m.programarEvento(1000, EV_JUGADOR, m.jugador)
    m.jugador.evento = original
    marca = m.marca()
    ef.aplicarVelocidad(m, m.jugador, 200, 300)
    m.correrHasta(100)
    m.retrocederHasta(marca)
    assert m.jugador.velocidad == 100
    assert m.jugador.evento is original
    assert original.tiempo == 1000 and not original.cancelado
    assert ef.activos == []


def testReaplicarVenenoReinicia():
    m, ef = nuevo()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correrHasta(100)                           # 1 pulso
    ef.aplicarVeneno(m, m.jugador, 3)             # reinicia: 5 pulsos de 3 desde t=100
    m.correrHasta(1000)
    assert m.jugador.vida == 30 - 2 - 3 * 5
    assert len(ef.activos) == 0


def testDescripcionParaLaVista():
    m, ef = nuevo()
    assert ef.descripcionjugador(m) == []
    ef.aplicarVeneno(m, m.jugador, 2)
    ef.encenderAntorcha(m, m.jugador, 2000)
    m.correrHasta(100)
    textos = ef.descripcionjugador(m)
    assert len(textos) == 2
    assert "Veneno" in textos[0] and "quedan 300" in textos[0]
    assert "Antorcha" in textos[1] and "quedan 1900" in textos[1]


def testUsarAntidoto():
    m, ef = nuevo()
    ef.aplicarVeneno(m, m.jugador, 2)
    m.correrHasta(100)                           # 1 pulso
    ef.alUsarObjeto(m, {"clase": "antidoto", "nombre": "Antídoto"})
    m.correrHasta(1000)
    assert m.jugador.vida == 28 and ef.activos == []


def testUsarAntidotoSinVenenoNoFalla():
    m, ef = nuevo()
    ef.alUsarObjeto(m, {"clase": "antidoto", "nombre": "Antídoto"})
    assert ef.activos == []


def testUsarAntorcha():
    m, ef = nuevo()
    ef.alUsarObjeto(m, {"clase": "antorcha", "duracion": 2000})
    assert ef.antorchaEncendida(m.jugador)
    m.correrHasta(2000)
    assert not ef.antorchaEncendida(m.jugador)


def testUsarPocionDeVelocidad():
    m, ef = nuevo()
    m.jugador.evento = m.programarEvento(1000, EV_JUGADOR, m.jugador)
    ef.alUsarObjeto(m, {"clase": "pocion", "modificador_velocidad": 2, "duracion": 300})
    assert m.jugador.velocidad == 200
    m.correrHasta(300)
    assert m.jugador.velocidad == 100


def testPocionDeCuracionNoCreaEfectos():
    m, ef = nuevo()
    ef.alUsarObjeto(m, {"clase": "pocion", "cura": 10})   # la cura la hace el inventario
    assert ef.activos == []


if __name__ == "__main__":
    for nombre, f in list(globals().items()):
        if nombre.startswith("test"):
            f()
            print("OK", nombre)
    print("Efectos OK")