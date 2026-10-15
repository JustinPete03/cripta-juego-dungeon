class Evento:
    def __init__(self, tiempo, accion):
        self.tiempo = tiempo
        self.accion = accion
        self.cancelado = False


class AgendaFalsa:
    def __init__(self):
        self.reloj = 0
        self.eventos = []

    def programar(self, tiempo, accion):
        ev = Evento(tiempo, accion)
        self.eventos.append(ev)
        return ev

    def cancelar(self, ev):
        ev.cancelado = True

    def reprogramar(self, ev, nuevo_tiempo):
        ev.tiempo = nuevo_tiempo

    def avanzar_hasta(self, limite):
        """Ejecuta eventos en orden de tiempo hasta 'limite'."""
        while True:
            pendientes = [e for e in self.eventos if not e.cancelado and e.tiempo <= limite]
            if not pendientes:
                break
            ev = min(pendientes, key=lambda e: e.tiempo)
            self.eventos.remove(ev)
            self.reloj = ev.tiempo
            ev.accion(self)
        self.reloj = limite