#Modelo del juego: reloj virtual, agenda, combate, movimiento, puertas, trampas, comportamientos.

#Reglas de oro:
 # * Toda mutación pasa por asignar / agregar / quitar/ insertar (o por la agenda),
 #   que informan su inversa al diario. Así el retroceso no necesita copias del estado.
 # * Nada de dict como índice. Nada de hora del sistema.
 # * El modelo solo conoce las interfaces de modelo/interfaces.py.
import random

from model.Constantes import (
    DIRECCIONES, direccionOpuesta, EN_CURSO, VICTORIA, DERROTA,
    EV_JUGADOR, EV_ENEMIGO, EV_CIERRE_PUERTA, EV_REARME_TRAMPA, CANTIDAD_TIPOS_EVENTO,
    ACC_MOVER, ACC_ABRIR, ACC_ATACAR, ACC_ESPERAR, ACC_RECOGER, ACC_USAR, ACC_EQUIPAR,
    ACC_SOLTAR, ACC_RETROCESO, ACC_SIGUIENTE, ACC_ANTERIOR,
    COSTOS, COSTO_ACCION_ENEMIGO, CAPACIDAD_BITACORA, REARME_POR_DEFECTO,
)
from model.Tiempo import intervaloAccion, tiempoTrasCambioVelocidad
from model.Agenda import Agenda
from model.Bitacora import BitacoraCircular
from model.Salas import IndiceOrdenado
from model.Entidades import (Sala, Salida, Puerta, Jugador, Enemigo, ObjetoInstancia, Trampa,
                              ordenarEnemigosPorInstancia)
from model.Interfaces import Resultado, DiarioNulo, EfectosBase, SinDatos
from model.Rastro import elegirDestinoRastreador
from model import estado


class ResultadoPartida:
    def __init__(self, estado, acciones, derrotados, tiempoFinal):
        self.estado = estado
        self.acciones = acciones
        self.derrotados = derrotados
        self.tiempoFinal = tiempoFinal


class Modelo:
    def __init__(self, proveedor, semilla, inventario, diario=None, efectos=None):
        self.proveedor = proveedor
        self.semilla = semilla
        self.inventario = inventario
        self.diario = diario if diario is not None else DiarioNulo()
        self.efectos = efectos if efectos is not None else EfectosBase()

        # Tabla de manejadores indexada por tipo de evento (
        self._manejadores = [None] * CANTIDAD_TIPOS_EVENTO
        self._manejadores[EV_ENEMIGO] = self._manejarEnemigo
        self._manejadores[EV_CIERRE_PUERTA] = self._manejarCierrePuerta
        self._manejadores[EV_REARME_TRAMPA] = self._manejarRearmeTrampa
        self._prepararEstado()

    def _prepararEstado(self):
        """Deja el modelo como recién creado. Lo usan iniciarPartida y el cargado de partidas."""
        self.azar = random.Random(self.semilla)        # única fuente de azar
        self.bitacora = BitacoraCircular(CAPACIDAD_BITACORA)
        self.reloj = 0
        self.agenda = Agenda(self._registrar)
        self.salas = IndiceOrdenado()
        self.jugador = None
        self.enemigosVivos = []
        self.estado = EN_CURSO
        self.eventoDecision = None                # evento del jugador ya sacado: espera su decisión
        self.puertaSalidaAbierta = False
        self.salaInicialId = None
        self.salaSalidaId = None
        self.llaveSalida = None
        self.siguienteSerieObjeto = 0
        self._grabando = False

    def reiniciar(self):
        # El cargado descarta la partida en curso antes de reconstruir el mundo desde el archivo.
        self._prepararEstado()


    # Interfaz reversible (la usan Jorge y Jurnier)
    def _registrar(self, deshacer):
        if self._grabando:
            self.diario.registrar(deshacer)

    def asignar(self, objeto, campo, valor):
        """objeto.campo = valor, registrando la inversa."""
        anterior = getattr(objeto, campo)
        setattr(objeto, campo, valor)
        if self._grabando:
            def deshacer():
                setattr(objeto, campo, anterior)
            self.diario.registrar(deshacer)

    def agregarA(self, lista, elemento):
        lista.append(elemento)
        if self._grabando:
            def deshacer():
                i = len(lista) - 1
                while i >= 0:
                    if lista[i] is elemento:
                        del lista[i]
                        return
                    i -= 1
            self.diario.registrar(deshacer)

    def insertarEn(self, lista, indice, elemento):
        lista.insert(indice, elemento)
        if self._grabando:
            def deshacer():
                i = 0
                while i < len(lista):
                    if lista[i] is elemento:
                        del lista[i]
                        return
                    i += 1
            self.diario.registrar(deshacer)

    def quitarDe(self, lista, elemento):
        #Quita por identidad; la inversa lo devuelve a su posición.
        i = 0
        while i < len(lista):
            if lista[i] is elemento:
                break
            i += 1
        if i == len(lista):
            return
        del lista[i]
        if self._grabando:
            def deshacer():
                lista.insert(min(i, len(lista)), elemento)
            self.diario.registrar(deshacer)

    def registrarManejador(self, tipoEvento, funcion):
        """funcion(modelo, evento). Para los eventos de efectos de Jurnier/Jorge."""
        def manejador(evento):
            funcion(self, evento)
        self._manejadores[tipoEvento] = manejador

    def programarEvento(self, tiempo, tipo, propietario, datos=None):
        return self.agenda.programar(tiempo, tipo, propietario, datos)

    def cancelarEvento(self, evento):
        if evento is not None:
            self.agenda.cancelar(evento)

    def mensaje(self, texto):
        self.bitacora.agregar("[t=%d] %s" % (self.reloj, texto))

    def nombreDe(self, tipoId):
        return self.proveedor.ficha(tipoId)["nombre"]

    # Inicio de partida
    def iniciarPartida(self):
        datos = self.proveedor.datosGenerales()
        self.salaInicialId = datos["sala_inicial"]
        self.salaSalidaId = datos["sala_salida"]
        self.llaveSalida = datos["llave_salida"]
        self.inventario.configurar(datos["inventario_max"])
        stats = datos["jugador"]
        self.jugador = Jugador(stats["vida_max"], stats["ataque"], stats["defensa"], stats["velocidad"])

        self._construirSalas(self.proveedor.esqueleto())
        inicial = self.salas.buscar(self.salaInicialId)
        if inicial is None:
            raise ValueError("La sala inicial %s no existe en el esqueleto." % (self.salaInicialId,))
        if self.salas.buscar(self.salaSalidaId) is None:
            raise ValueError("La sala de salida %s no existe en el esqueleto." % (self.salaSalidaId,))
        # §2.12 pide entrar con la puerta de acceso abierta, no haberla abierto en persona: una
        # cripta que la entrega ya abierta (sección 9) sigue siendo ganable.
        for acceso in self.salas.buscar(self.salaSalidaId).salidas:
            if not acceso.puerta.cerrada:
                self.puertaSalidaAbierta = True
        self.proveedor.fijarFichasEnUso(self.fichasEnUso)

        # El contenido de la sala inicial se carga antes de aceptar la primera acción (sección 2.4)
        self._asegurarContenido(inicial)
        self.jugador.sala = inicial
        inicial.rastro = 0

        evento = self.agenda.programar(0, EV_JUGADOR, self.jugador)
        self.jugador.evento = evento
        self.jugador.tiempoSiguiente = 0
        self._activarDormidos(inicial)           # los de la sala inicial, en t = 0
        self.proveedor.anticipar(inicial.id)
        self.mensaje("Comienza la partida en: %s." % inicial.nombre)
        self._correrHastaDecision()

    def _construirSalas(self, esqueleto):
        for datos in esqueleto:
            sala = Sala(datos["id"], datos["nombre"])
            self.salas.insertar(sala.id, sala)
            salidas = datos["salidas"]
            for direccion in DIRECCIONES:
                if direccion in salidas:
                    info = salidas[direccion]
                    puerta = Puerta(bool(info.get("cerrada", False)),
                                    info.get("llave"),
                                    info.get("cierre_automatico"))
                    sala.salidas.append(Salida(direccion, sala, info["sala"], puerta))

        cantidad = self.salas.cantidad()
        for i in range(cantidad):
            sala = self.salas.enPosicion(i)
            for salida in sala.salidas:
                destino = self.salas.buscar(salida.destinoId)
                if destino is None:
                    raise ValueError("La sala %s tiene una salida hacia la sala inexistente %s."
                                     % (sala.id, salida.destinoId))
                salida.destino = destino

        # Las dos salidas que conectan el mismo par de salas comparten una sola puerta
        for i in range(cantidad):
            sala = self.salas.enPosicion(i)
            for salida in sala.salidas:
                inversa = salida.destino.salida(direccionOpuesta(salida.direccion))
                if inversa is not None and inversa.destino is sala and inversa.puerta is not salida.puerta:
                    a = salida.puerta
                    b = inversa.puerta
                    unida = Puerta(a.cerrada or b.cerrada,
                                   a.llave if a.llave is not None else b.llave,
                                   a.cierreAutomatico if a.cierreAutomatico else b.cierreAutomatico)
                    salida.puerta = unida
                    inversa.puerta = unida

    def _asegurarContenido(self, sala):
        #Incorpora el contenido al modelo (sin activar enemigos). Puede bloquear en red;
        #eso nunca mueve el reloj virtual. No es parte del estado reversible.
        if sala.contenidoIncorporado:
            return
        contenido = self.proveedor.contenidoSala(sala.id)
        # Las fichas que la sala va a necesitar se piden juntas: así el catálogo se resuelve en
        # lotes de 10 y no con una solicitud por ficha, que es lo que estira el presupuesto (2.3).
        ids = list(contenido["objetos"])
        for datos in contenido["enemigos"]:
            ids.append(datos["tipo"])
        for datos in contenido["trampas"]:
            ids.append(datos["tipo"])
        self.proveedor.asegurarFichas(ids)
        nuevosEnemigos = []
        for datos in contenido["enemigos"]:
            ficha = self.proveedor.ficha(datos["tipo"])
            vida = datos.get("vida", ficha["vida_max"])
            enemigo = Enemigo(datos["instancia"], datos["tipo"], ficha["nombre"],
                              ficha["comportamiento"], vida, ficha["vida_max"],
                              ficha["ataque"], ficha["defensa"], ficha["velocidad"])
            enemigo.sala = sala
            nuevosEnemigos.append(enemigo)
        serieInicial = self.siguienteSerieObjeto
        nuevosObjetos = []
        for i, tipoObjeto in enumerate(contenido["objetos"]):
            nuevosObjetos.append(ObjetoInstancia(tipoObjeto, serieInicial + i))
        nuevasTrampas = []
        for datos in contenido["trampas"]:
            nuevasTrampas.append(Trampa(datos["instancia"], datos["tipo"]))

        # Todo lo que puede fallar ya ocurrió: desde aquí la sala se completa de una sola vez,
        # para que un SinDatos a medias no deje enemigos duplicados en el modelo.
        for enemigo in nuevosEnemigos:
            sala.enemigos.append(enemigo)
            self.enemigosVivos.append(enemigo)
        sala.objetos.extend(nuevosObjetos)
        self.siguienteSerieObjeto = serieInicial + len(nuevosObjetos)
        sala.trampas.extend(nuevasTrampas)
        sala.contenidoIncorporado = True

    # Bucle del reloj virtual
    def esperandoDecision(self):
        return self.estado == EN_CURSO and self.eventoDecision is not None

    def _correrHastaDecision(self):
        """Ejecuta eventos en orden (tiempo, seq) hasta que le toque decidir al jugador."""
        while self.estado == EN_CURSO:
            evento = self.agenda.proximo()
            if evento is None:
                raise RuntimeError("La agenda quedó vacía: el jugador siempre debe tener un evento.")
            self.reloj = evento.tiempo
            if evento.tipo == EV_JUGADOR:
                self.asignar(self, "eventoDecision", evento)
                self.asignar(self.jugador, "evento", None)
                return
            manejador = self._manejadores[evento.tipo]
            if manejador is None:
                raise RuntimeError("No hay manejador para el evento de tipo %d." % evento.tipo)
            manejador(evento)

    # Acciones del jugador
    def ejecutar(self, accion):
        if self.estado != EN_CURSO:
            return Resultado(False, "La partida ya terminó.")
        tipo = accion.tipo
        if tipo == ACC_RETROCESO:
            return self._retroceder()
        if tipo == ACC_SIGUIENTE:
            self.inventario.avanzar()
            return Resultado(True, "", True)
        if tipo == ACC_ANTERIOR:
            self.inventario.retroceder()
            return Resultado(True, "", True)

        validacion = self._validar(accion)
        if not validacion.ok:
            self.mensaje(validacion.mensaje)       # rechazada: no consume tiempo ni cambia estado
            return validacion

        self._grabando = self.diario.activo
        self.diario.abrirIntervalo()
        relojAnterior = self.reloj
        if self._grabando:
            estadoAzar = self.azar.getstate()
            serieAnterior = self.siguienteSerieObjeto
            secuenciaAnterior = self.agenda.secuencia()
            def restaurarReloj():
                self.reloj = relojAnterior
            def restaurarContadores():
                self.azar.setstate(estadoAzar)
                self.siguienteSerieObjeto = serieAnterior
                self.agenda.restaurarSecuencia(secuenciaAnterior)
            self.diario.registrar(restaurarReloj)
            self.diario.registrar(restaurarContadores)
        self.asignar(self, "eventoDecision", None)   # la inversa restaura el evento del jugador

        self._programarSiguienteJugador(COSTOS[tipo])
        self.asignar(self.jugador, "acciones", self.jugador.acciones + 1)
        self._aplicar(accion)
        if self.estado == EN_CURSO:
            # El rastro de la sala actual se refresca en cada acción del jugador (Apéndice B)
            self.asignar(self.jugador.sala, "rastro", self.reloj)
            self._correrHastaDecision()

        self.diario.cerrarIntervalo()
        self._grabando = False
        return Resultado(True, "", True)

    def _retroceder(self):
        self._grabando = False
        resultado = self.diario.retroceder(self)
        if resultado.ok:
            self.mensaje("El tiempo retrocede.")
            resultado.registrable = True
        else:
            self.mensaje(resultado.mensaje)
        return resultado

    def _programarSiguienteJugador(self, costo):
        jugador = self.jugador
        tiempo = self.reloj + intervaloAccion(costo, jugador.velocidad)
        evento = self.agenda.programar(tiempo, EV_JUGADOR, jugador)
        self.asignar(jugador, "evento", evento)
        self.asignar(jugador, "tiempoSiguiente", tiempo)

    def _validar(self, accion):
        tipo = accion.tipo
        sala = self.jugador.sala
        if tipo == ACC_ESPERAR:
            return Resultado(True)
        if tipo == ACC_MOVER:
            salida = sala.salida(accion.argumento)
            if salida is None:
                return Resultado(False, "No hay salida hacia %s." % accion.argumento)
            if salida.puerta.cerrada:
                return Resultado(False, "La puerta hacia %s está cerrada." % accion.argumento)
            try:
                self._asegurarContenido(salida.destino)   # nunca se entra sin contenido
            except SinDatos as falta:
                # Rechazar aquí no gasta tiempo: el presupuesto de la cripta manda (sección 2.3).
                return Resultado(False, "No se puede entrar a %s: %s." % (salida.destino.nombre, falta))
            return Resultado(True)
        if tipo == ACC_ABRIR:
            salida = sala.salida(accion.argumento)
            if salida is None:
                return Resultado(False, "No hay salida hacia %s." % accion.argumento)
            puerta = salida.puerta
            if not puerta.cerrada:
                return Resultado(False, "La puerta hacia %s ya está abierta." % accion.argumento)
            if puerta.llave is not None and not self.inventario.tieneLlave(puerta.llave):
                return Resultado(False, "No tienes la llave correcta para esa puerta.")
            return Resultado(True)
        if tipo == ACC_ATACAR:
            if accion.argumento < 0 or accion.argumento >= len(sala.enemigos):
                return Resultado(False, "No hay ese enemigo en la sala.")
            return Resultado(True)
        # RECOGER, USAR, EQUIPAR, SOLTAR:
        return self.inventario.validar(self, accion)

    def _aplicar(self, accion):
        tipo = accion.tipo
        if tipo == ACC_ESPERAR:
            self.mensaje("Esperas.")
        elif tipo == ACC_MOVER:
            self._aplicarMover(accion.argumento)
        elif tipo == ACC_ABRIR:
            self._aplicarAbrir(accion.argumento)
        elif tipo == ACC_ATACAR:
            self._aplicarAtacar(accion.argumento)
        else:
            self.inventario.aplicar(self, accion)

    def _aplicarMover(self, direccion):
        origen = self.jugador.sala
        destino = origen.salida(direccion).destino
        self.asignar(self.jugador, "sala", destino)
        self.asignar(destino, "rastro", self.reloj)
        self.mensaje("Entras a: %s." % destino.nombre)
        self._activarDormidos(destino)
        self._activarTrampas(destino)
        if (self.estado == EN_CURSO and destino.id == self.salaSalidaId
                and self.puertaSalidaAbierta):
            self.estado = VICTORIA
            self.mensaje("¡Llegas a la salida! Victoria.")
        self.proveedor.anticipar(destino.id)

    def _aplicarAbrir(self, direccion):
        origen = self.jugador.sala
        salida = origen.salida(direccion)
        puerta = salida.puerta
        self.asignar(puerta, "cerrada", False)
        self.mensaje("Abres la puerta hacia %s." % direccion)
        if puerta.cierreAutomatico:
            evento = self.agenda.programar(self.reloj + puerta.cierreAutomatico,
                                           EV_CIERRE_PUERTA, puerta)
            self.asignar(puerta, "eventoCierre", evento)
        if (puerta.llave is not None and puerta.llave == self.llaveSalida
                and (salida.destino.id == self.salaSalidaId or origen.id == self.salaSalidaId)):
            self.asignar(self, "puertaSalidaAbierta", True)

    def _aplicarAtacar(self, indice):
        jugador = self.jugador
        objetivo = jugador.sala.enemigos[indice]
        dano = self._calcularDanio(jugador.ataque + jugador.bonoAtaque, objetivo.defensa)
        self.mensaje("Atacas a %s: %d de daño." % (objetivo.etiqueta(), dano))
        self.aplicarDanio(objetivo, dano)

    # Combate, vida y muerte
    def _calcularDanio(self, ataque, defensa):
        return max(1, ataque + self.azar.randint(0, 4) - defensa)

    def aplicarDanio(self, actor, cantidad):
        """Resta vida (nunca bajo 0). Si llega a 0 el actor muere en el acto."""
        if not actor.vivo or cantidad <= 0:
            return
        nueva = max(0, actor.vida - cantidad)
        self.asignar(actor, "vida", nueva)
        if nueva == 0:
            self._morir(actor)

    def curar(self, actor, cantidad):
        """Suma vida sin superar vidaMax."""
        if not actor.vivo:
            return
        self.asignar(actor, "vida", min(actor.vidaMax, actor.vida + cantidad))

    def _morir(self, actor):
        self.asignar(actor, "vivo", False)
        if actor is self.jugador:
            self.estado = DERROTA
            self.mensaje("Has muerto. Derrota.")
            self.efectos.alMorir(self, actor)
            return
        # Enemigo: sus eventos futuros dejan de ejecutarse sin recorrer la agenda
        if actor.evento is not None:
            self.agenda.cancelar(actor.evento)
            self.asignar(actor, "evento", None)
        self.efectos.alMorir(self, actor)
        sala = actor.sala
        self.quitarDe(sala.enemigos, actor)
        self.quitarDe(self.enemigosVivos, actor)
        self.asignar(self.jugador, "derrotados", self.jugador.derrotados + 1)
        self.mensaje("%s muere." % actor.etiqueta())
        for tipoObjeto in self.proveedor.ficha(actor.tipoId).get("suelta", []):
            objeto = ObjetoInstancia(tipoObjeto, self.siguienteSerieObjeto)
            self.siguienteSerieObjeto += 1
            self.agregarA(sala.objetos, objeto)

    def cambiarVelocidad(self, actor, nueva):
        """Cambio de velocidad con reescalado de la acción ya programada (sección 2.3)."""
        if nueva <= 0:
            raise ValueError("La velocidad debe ser positiva.")
        anterior = actor.velocidad
        if nueva == anterior:
            return
        self.asignar(actor, "velocidad", nueva)
        evento = actor.evento
        if evento is not None and not evento.cancelado:
            nuevoTiempo = tiempoTrasCambioVelocidad(evento.tiempo, self.reloj, anterior, nueva)
            nuevo = self.agenda.reprogramar(evento, nuevoTiempo)   # seq nuevo
            self.asignar(actor, "evento", nuevo)
            self.asignar(actor, "tiempoSiguiente", nuevoTiempo)

    # Enemigos: activación y turnos
    def _activarDormidos(self, sala):
        dormidos = []
        for enemigo in sala.enemigos:
            if not enemigo.activo:
                dormidos.append(enemigo)
        for enemigo in ordenarEnemigosPorInstancia(dormidos):
            self.asignar(enemigo, "activo", True)
            self._programarEnemigo(enemigo)
            self.efectos.alActivarEnemigo(self, enemigo)

    def _programarEnemigo(self, enemigo):
        tiempo = self.reloj + intervaloAccion(COSTO_ACCION_ENEMIGO, enemigo.velocidad)
        evento = self.agenda.programar(tiempo, EV_ENEMIGO, enemigo)
        self.asignar(enemigo, "evento", evento)
        self.asignar(enemigo, "tiempoSiguiente", tiempo)

    def _manejarEnemigo(self, evento):
        enemigo = evento.propietario
        if not enemigo.vivo:
            return
        if enemigo.sala is self.jugador.sala:
            self._enemigoAtaca(enemigo)
        else:
            self._enemigoSeComporta(enemigo)
        if self.estado == EN_CURSO and enemigo.vivo:
            self._programarEnemigo(enemigo)

    def _enemigoAtaca(self, enemigo):
        jugador = self.jugador
        dano = self._calcularDanio(enemigo.ataque, jugador.defensa + jugador.bonoDefensa)
        self.mensaje("%s te ataca: %d de daño." % (enemigo.etiqueta(), dano))
        self.aplicarDanio(jugador, dano)

    def _enemigoSeComporta(self, enemigo):
        comportamiento = enemigo.comportamiento
        if comportamiento == "errante":
            abiertas = []
            for salida in enemigo.sala.salidas:
                if not salida.puerta.cerrada:
                    abiertas.append(salida)
            if len(abiertas) > 0:
                elegida = abiertas[self.azar.randrange(len(abiertas))]
                self._moverEnemigo(enemigo, elegida.destino)
        elif comportamiento == "rastreador":
            destino = elegirDestinoRastreador(enemigo.sala, self.reloj)
            if destino is not None:
                self._moverEnemigo(enemigo, destino)

    def _moverEnemigo(self, enemigo, destino):
        origen = enemigo.sala
        self.quitarDe(origen.enemigos, enemigo)
        self.agregarA(destino.enemigos, enemigo)
        self.asignar(enemigo, "sala", destino)
        if destino is self.jugador.sala:
            self.mensaje("%s entra a la sala." % enemigo.etiqueta())

    # Trampas y puertas
    def _activarTrampas(self, sala):
        for trampa in sala.trampas:
            if not trampa.armada:
                continue
            ficha = self.proveedor.ficha(trampa.tipoId)
            self.asignar(trampa, "armada", False)
            rearme = ficha.get("rearme", REARME_POR_DEFECTO)
            evento = self.agenda.programar(self.reloj + rearme, EV_REARME_TRAMPA, trampa)
            self.asignar(trampa, "eventoRearme", evento)
            dano = ficha.get("daño", 0)
            self.mensaje("¡%s! Recibes %d de daño." % (ficha["nombre"], dano))
            self.aplicarDanio(self.jugador, dano)
            self.efectos.alActivarTrampa(self, trampa, ficha)
            if self.estado != EN_CURSO:
                return

    def _manejarRearmeTrampa(self, evento):
        trampa = evento.propietario
        self.asignar(trampa, "armada", True)
        self.asignar(trampa, "eventoRearme", None)

    def _manejarCierrePuerta(self, evento):
        puerta = evento.propietario
        self.asignar(puerta, "cerrada", True)    # quien está al otro lado permanece allí
        self.asignar(puerta, "eventoCierre", None)

    # Consultas
    def fichasEnUso(self):
        """Lista de ids de fichas referenciadas por una instancia activa (sección 4.4).

        Es una lista y no un predicado para que la caché la vuelva conjunto y recorra sus
        entradas una sola vez, en vez de evaluar esto sobre cada ficha guardada."""
        ids = []
        for enemigo in self.enemigosVivos:
            ids.append(enemigo.tipoId)
        for objeto in self.inventario.objetos():
            ids.append(objeto.tipoId)
        if self.jugador is not None and self.jugador.sala is not None:
            sala = self.jugador.sala
            for objeto in sala.objetos:
                ids.append(objeto.tipoId)
            for trampa in sala.trampas:
                ids.append(trampa.tipoId)
        return ids

    def resultadoPartida(self):
        return ResultadoPartida(self.estado, self.jugador.acciones, self.jugador.derrotados, self.reloj)

    # Guardado (sección 4.12): el modelo expone el estado como datos planos y sabe volver de ellos.
    def capturarEstado(self):
        return estado.capturar(self)

    def restaurarEstado(self, datos):
        estado.restaurar(self, datos)