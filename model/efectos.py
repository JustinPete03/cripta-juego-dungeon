class Efecto:
    def __init__(self, actor):
        self.actor = actor
        self.evento = None     # evento programado en la agenda
        self.activo = False

    def activar(self, agenda):
        raise NotImplementedError

    def disparar(self, agenda):
        raise NotImplementedError

    def cancelar(self, agenda):
        """Impide activaciones futuras sin recorrer la agenda."""
        if self.evento is not None:
            agenda.cancelar(self.evento)
            self.evento = None
        self.activo = False


class Veneno(Efecto):
    INTERVALO = 80
    DURACION = 400

    def __init__(self, actor, dano):
        super().__init__(actor)
        self.dano = dano
        self.fin = None

    def activar(self, agenda):
        self.activo = True
        self.fin = agenda.reloj + self.DURACION
        self.evento = agenda.programar(agenda.reloj + self.INTERVALO, self.disparar)

    def disparar(self, agenda):
        self.actor.vida = max(0, self.actor.vida - self.dano)
        siguiente = agenda.reloj + self.INTERVALO
        if self.actor.vida > 0 and siguiente <= self.fin:
            self.evento = agenda.programar(siguiente, self.disparar)
        else:
            self.evento = None
            self.activo = False


class Regeneracion(Efecto):
    INTERVALO = 200

    def __init__(self, actor, cantidad):
        super().__init__(actor)
        self.cantidad = cantidad

    def activar(self, agenda):
        self.activo = True
        self.evento = agenda.programar(agenda.reloj + self.INTERVALO, self.disparar)

    def disparar(self, agenda):
        self.actor.vida = min(self.actor.vida_max, self.actor.vida + self.cantidad)
        self.evento = agenda.programar(agenda.reloj + self.INTERVALO, self.disparar)


class Antorcha(Efecto):
    def __init__(self, actor, duracion):
        super().__init__(actor)
        self.duracion = duracion

    def activar(self, agenda):
        self.activo = True
        self.evento = agenda.programar(agenda.reloj + self.duracion, self.disparar)

    def disparar(self, agenda):
        self.evento = None
        self.activo = False        # se apaga


class CambioVelocidad(Efecto):
    def __init__(self, actor, velocidad_nueva, duracion):
        super().__init__(actor)
        self.velocidad_nueva = velocidad_nueva
        self.duracion = duracion
        self.velocidad_anterior = None

    def _reescalar(self, agenda, vel_vieja, vel_nueva):
        ev = self.actor.evento_accion
        if ev is not None:
            restante = max(1, (ev.tiempo - agenda.reloj) * vel_vieja // vel_nueva)
            agenda.reprogramar(ev, agenda.reloj + restante)

    def activar(self, agenda):
        self.activo = True
        self.velocidad_anterior = self.actor.velocidad
        self.actor.velocidad = self.velocidad_nueva
        self._reescalar(agenda, self.velocidad_anterior, self.velocidad_nueva)
        self.evento = agenda.programar(agenda.reloj + self.duracion, self.disparar)

    def disparar(self, agenda):
        # Termina el efecto: restaura la velocidad y reajusta de nuevo.
        self.actor.velocidad = self.velocidad_anterior
        self._reescalar(agenda, self.velocidad_nueva, self.velocidad_anterior)
        self.evento = None
        self.activo = False

    def cancelar(self, agenda):
        if self.activo:
            self.actor.velocidad = self.velocidad_anterior
            self._reescalar(agenda, self.velocidad_nueva, self.velocidad_anterior)
        super().cancelar(agenda)