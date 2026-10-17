# Imita los métodos de Modelo (Justin) que usan los efectos. NO es el modelo real.
from model.Agenda import Agenda
from model.Constantes import CANTIDAD_TIPOS_EVENTO, EV_JUGADOR
from model.Entidades import Jugador


class proveedorFalso:
    def __init__(self, fichas):
        self.fichas = fichas

    def ficha(self, tipoId):
        return self.fichas[tipoId]


class modeloFalso:
    def __init__(self, efectos, fichas=None):
        self.reloj = 0
        self.diario = []                         # inversas, como el diario de Jorge
        self.agenda = Agenda(self._registrar)
        self.efectos = efectos
        self.jugador = Jugador(30, 6, 2, 100)
        self.proveedor = proveedorFalso(fichas or {})
        self.mensajes = []
        self._manejadores = [None] * CANTIDAD_TIPOS_EVENTO
        efectos.registrarEn(self)

    def _registrar(self, deshacer):
        self.diario.append(deshacer)

    def asignar(self, objeto, campo, valor):
        anterior = getattr(objeto, campo)
        setattr(objeto, campo, valor)

        def deshacer():
            setattr(objeto, campo, anterior)
        self.diario.append(deshacer)

    def agregarA(self, lista, elemento):
        lista.append(elemento)

        def deshacer():
            for i in range(len(lista) - 1, -1, -1):
                if lista[i] is elemento:
                    del lista[i]
                    return
        self.diario.append(deshacer)

    def quitarDe(self, lista, elemento):
        for i in range(len(lista)):
            if lista[i] is elemento:
                break
        else:
            return
        del lista[i]

        def deshacer():
            lista.insert(min(i, len(lista)), elemento)
        self.diario.append(deshacer)

    def registrarManejador(self, tipo, funcion):
        self._manejadores[tipo] = lambda evento: funcion(self, evento)

    def programarEvento(self, tiempo, tipo, propietario, datos=None):
        return self.agenda.programar(tiempo, tipo, propietario, datos)

    def cancelarEvento(self, evento):
        if evento is not None:
            self.agenda.cancelar(evento)

    def mensaje(self, texto):
        self.mensajes.append("[t=%d] %s" % (self.reloj, texto))

    def aplicarDanio(self, actor, cantidad):
        if not actor.vivo or cantidad <= 0:
            return
        nueva = max(0, actor.vida - cantidad)
        self.asignar(actor, "vida", nueva)
        if nueva == 0:
            self.asignar(actor, "vivo", False)
            if actor.evento is not None:
                self.agenda.cancelar(actor.evento)
            self.efectos.alMorir(self, actor)

    def curar(self, actor, cantidad):
        if not actor.vivo:
            return
        self.asignar(actor, "vida", min(actor.vidaMax, actor.vida + cantidad))

    def cambiarVelocidad(self, actor, nueva):
        anterior = actor.velocidad
        if nueva == anterior:
            return
        self.asignar(actor, "velocidad", nueva)
        evento = actor.evento
        if evento is not None and not evento.cancelado:
            restante = max(1, (evento.tiempo - self.reloj) * anterior // nueva)   # §2.3
            nuevo = self.agenda.reprogramar(evento, self.reloj + restante)
            self.asignar(actor, "evento", nuevo)

    # --- para las pruebas
    def correrHasta(self, limite):
        parada = self.programarEvento(limite, EV_JUGADOR, None, "parada")
        while True:
            evento = self.agenda.proximo()
            self.reloj = evento.tiempo
            if evento is parada:
                break
            self._manejadores[evento.tipo](evento)

    def marca(self):
        return len(self.diario)

    def retrocederHasta(self, marca):
        while len(self.diario) > marca:
            self.diario.pop()()