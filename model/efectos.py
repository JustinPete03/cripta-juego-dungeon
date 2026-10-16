from model.Constantes import EV_VENENO, EV_REGENERACION, EV_FIN_ANTORCHA, EV_FIN_VELOCIDAD
from model.Interfaces import EfectosBase

INTERVALO_VENENO = 80
DURACION_VENENO = 400
INTERVALO_REGENERACION = 200

VENENO = 0
REGENERACION = 1
ANTORCHA = 2
VELOCIDAD = 3


class EfectoActivo:
    """Un efecto en curso sobre un actor. Su evento pendiente se guarda aquí mismo,
    de modo que cancelarlo no exige buscarlo en la agenda."""

    def __init__(self, clase, actor, cantidad=0, fin=0, velocidadAnterior=None):
        self.clase = clase
        self.actor = actor
        self.cantidad = cantidad            # daño por pulso, o curación por pulso
        self.fin = fin                      # instante en que expira (veneno)
        self.velocidadAnterior = velocidadAnterior
        self.evento = None                  # evento pendiente (para cancelarlo)
        self.activo = True


class EfectosJuego(EfectosBase):
    def __init__(self):
        self.activos = []                   # efectos en curso (pocos a la vez)

    def registrarEn(self, modelo):
        modelo.registrarManejador(EV_VENENO, self._pulsoVeneno)
        modelo.registrarManejador(EV_REGENERACION, self._pulsoRegeneracion)
        modelo.registrarManejador(EV_FIN_ANTORCHA, self._finEfecto)
        modelo.registrarManejador(EV_FIN_VELOCIDAD, self._finEfecto)

    # ------------------------------------------------------------ API pública
    def aplicarVeneno(self, modelo, actor, dano):
        if not actor.vivo:
            return
        self._reemplazar(modelo, VENENO, actor)
        efecto = EfectoActivo(VENENO, actor, dano, modelo.reloj + DURACION_VENENO)
        efecto.evento = modelo.programarEvento(modelo.reloj + INTERVALO_VENENO, EV_VENENO, efecto)
        modelo.agregarA(self.activos, efecto)
        modelo.mensaje("%s queda envenenado." % self._nombre(actor))

    def curarVeneno(self, modelo, actor):
        """Antídoto. Devuelve True si había veneno activo."""
        efecto = self._buscar(VENENO, actor)
        if efecto is None:
            return False
        self.cancelar(modelo, efecto)
        return True

    def aplicarRegeneracion(self, modelo, actor, cantidad):
        if not actor.vivo:
            return
        self._reemplazar(modelo, REGENERACION, actor)
        efecto = EfectoActivo(REGENERACION, actor, cantidad)
        efecto.evento = modelo.programarEvento(modelo.reloj + INTERVALO_REGENERACION,
                                               EV_REGENERACION, efecto)
        modelo.agregarA(self.activos, efecto)

    def encenderAntorcha(self, modelo, actor, duracion):
        if not actor.vivo:
            return
        self._reemplazar(modelo, ANTORCHA, actor)
        efecto = EfectoActivo(ANTORCHA, actor)
        efecto.evento = modelo.programarEvento(modelo.reloj + duracion, EV_FIN_ANTORCHA, efecto)
        modelo.agregarA(self.activos, efecto)
        modelo.mensaje("La antorcha se enciende.")

    def aplicarVelocidad(self, modelo, actor, velocidadNueva, duracion):
        if not actor.vivo:
            return
        self._reemplazar(modelo, VELOCIDAD, actor)     # restaura la velocidad previa
        efecto = EfectoActivo(VELOCIDAD, actor, velocidadAnterior=actor.velocidad)
        modelo.cambiarVelocidad(actor, velocidadNueva)  # reescala la acción ya programada
        efecto.evento = modelo.programarEvento(modelo.reloj + duracion, EV_FIN_VELOCIDAD, efecto)
        modelo.agregarA(self.activos, efecto)

    def cancelar(self, modelo, efecto):
        if not efecto.activo:
            return
        modelo.cancelarEvento(efecto.evento)           # O(1): la agenda solo marca
        modelo.asignar(efecto, "evento", None)
        self._quitar(modelo, efecto)

    def activosDe(self, actor):
        resultado = []
        for efecto in self.activos:
            if efecto.actor is actor:
                resultado.append(efecto)
        return resultado

    def antorchaEncendida(self, actor):
        return self._buscar(ANTORCHA, actor) is not None

    # ------------------------------------------------- ganchos que llama el modelo
    def alMorir(self, modelo, actor):
        for efecto in list(self.activos):              # copia: cancelar modifica la lista
            if efecto.actor is actor:
                self.cancelar(modelo, efecto)

    def alActivarEnemigo(self, modelo, enemigo):
        ficha = modelo.proveedor.ficha(enemigo.tipoId)
        cantidad = ficha.get("regeneracion")           # VERIFICAR el nombre del campo en el catálogo
        if cantidad:
            self.aplicarRegeneracion(modelo, enemigo, cantidad)

    def alUsarObjeto(self, modelo, ficha):
        """Gancho que llama Inventario._usar (Jorge) al consumir un objeto.
        La cura de las pociones la hace el inventario; aquí van los efectos temporales."""
        clase = ficha.get("clase")
        jugador = modelo.jugador
        if clase == "antidoto":
            if self.curarVeneno(modelo, jugador):
                modelo.mensaje("El antídoto cancela el veneno.")
        elif clase == "antorcha":
            self.encenderAntorcha(modelo, jugador, ficha["duracion"])
        elif clase == "pocion" and "modificador_velocidad" in ficha:
            nueva = self._velocidadNueva(jugador, ficha["modificador_velocidad"])
            self.aplicarVelocidad(modelo, jugador, nueva, ficha["duracion"])

    def _velocidadNueva(self, actor, modificador):
        # SUPUESTO SIN VERIFICAR: modificador_velocidad es un multiplicador (1.5 = +50 %).
        # Comprobar en el catálogo real; si es un valor absoluto o una suma, cambiar solo esta línea.
        return max(1, int(actor.velocidad * modificador))

    def descripcionjugador(self, modelo):
        """Textos de los efectos activos del jugador, para la vista. Solo lee, no muta."""
        textos = []
        for efecto in self.activos:
            if efecto.actor is not modelo.jugador:
                continue
            if efecto.clase == VENENO:
                textos.append("Veneno: %d de daño cada %d (quedan %d)"
                              % (efecto.cantidad, INTERVALO_VENENO, efecto.fin - modelo.reloj))
            elif efecto.clase == REGENERACION:
                textos.append("Regeneración: +%d cada %d" % (efecto.cantidad, INTERVALO_REGENERACION))
            elif efecto.clase == ANTORCHA:
                textos.append("Antorcha encendida (quedan %d)" % (efecto.evento.tiempo - modelo.reloj))
            elif efecto.clase == VELOCIDAD:
                textos.append("Velocidad %d (quedan %d)"
                              % (efecto.actor.velocidad, efecto.evento.tiempo - modelo.reloj))
        return textos

    # ----------------------------------------------------- manejadores de eventos
    def _pulsoVeneno(self, modelo, evento):
        efecto = evento.propietario
        if not efecto.activo:
            return
        actor = efecto.actor
        modelo.mensaje("El veneno hace %d de daño a %s." % (efecto.cantidad, self._nombre(actor)))
        modelo.aplicarDanio(actor, efecto.cantidad)
        if not efecto.activo:                          # el actor murió: alMorir lo canceló
            return
        siguiente = modelo.reloj + INTERVALO_VENENO
        if siguiente <= efecto.fin:
            modelo.asignar(efecto, "evento",
                           modelo.programarEvento(siguiente, EV_VENENO, efecto))
        else:
            modelo.asignar(efecto, "evento", None)
            self._quitar(modelo, efecto)

    def _pulsoRegeneracion(self, modelo, evento):
        efecto = evento.propietario
        if not efecto.activo:
            return
        modelo.curar(efecto.actor, efecto.cantidad)
        modelo.asignar(efecto, "evento",
                       modelo.programarEvento(modelo.reloj + INTERVALO_REGENERACION,
                                              EV_REGENERACION, efecto))

    def _finEfecto(self, modelo, evento):              # fin de antorcha y de velocidad
        efecto = evento.propietario
        if not efecto.activo:
            return
        modelo.asignar(efecto, "evento", None)
        self._quitar(modelo, efecto)

    # ---------------------------------------------------------------- auxiliares
    def _quitar(self, modelo, efecto):
        modelo.asignar(efecto, "activo", False)
        modelo.quitarDe(self.activos, efecto)
        if efecto.clase == VELOCIDAD and efecto.actor.vivo:
            modelo.cambiarVelocidad(efecto.actor, efecto.velocidadAnterior)
        elif efecto.clase == ANTORCHA:
            modelo.mensaje("La antorcha se apaga.")

    def _buscar(self, clase, actor):
        for efecto in self.activos:
            if efecto.clase == clase and efecto.actor is actor:
                return efecto
        return None

    def _reemplazar(self, modelo, clase, actor):
        previo = self._buscar(clase, actor)
        if previo is not None:
            self.cancelar(modelo, previo)

    def _nombre(self, actor):
        etiqueta = getattr(actor, "etiqueta", None)
        return etiqueta() if etiqueta is not None else "Jugador"