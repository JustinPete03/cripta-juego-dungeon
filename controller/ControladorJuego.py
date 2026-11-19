"""Controlador: traduce texto del usuario a acciones del modelo y coordina el flujo.

Sirve igual para el modo interactivo y para --replay (sin vista): reproducir() no usa la vista.
Servicios opcionales (los aportan los demás): registro (bitácora de partida de Diego),
puntajes (tabla de puntajes de Diego), guardado (guardado binario de Jurnier).
"""
from model.Constantes import (EN_CURSO, VICTORIA, ACC_MOVER, ACC_ABRIR, ACC_ATACAR, ACC_ESPERAR,
                               ACC_RECOGER, ACC_USAR, ACC_EQUIPAR, ACC_SOLTAR, ACC_RETROCESO,
                               ACC_SIGUIENTE, ACC_ANTERIOR)
from model.Acciones import Accion, accionesDesdeTexto
from model.Interfaces import Resultado

AYUDA = (
    "Comandos: n/s/e/o (mover) | ir a <sala> | mapa | abrir <n|s|e|o> | atacar [k] | esperar | recoger [k] | soltar |\n"
    "          equipar | usar | retroceso | sig | ant | inv | ordenar <peso|valor|nombre> |\n"
    "          historia <t> | historia #k | puntajes | guardar <archivo> | cargar <archivo> | ayuda | salir"
)


def _direccion(texto):
    letra = texto.strip().upper()
    if letra in ("N", "S", "E", "O"):
        return letra
    return None


class Controlador:
    def __init__(self, modelo, vista=None, registro=None, puntajes=None, guardado=None, reporte=None):
        self.modelo = modelo
        self.vista = vista
        self.registro = registro
        self.puntajes = puntajes
        self.guardado = guardado
        self.reporte = reporte        # función del adaptador de red: solicitudes vs presupuesto (5.1)
        self.termino = False
        self.nombre = "Jugador"
        self.idCripta = ""
        self.versionCripta = ""

    def interpretar(self, texto):

        partes = texto.strip().lower().split()
        if len(partes) == 0:
            return None
        nombre = partes[0]
        arg = partes[1] if len(partes) > 1 else None
        if nombre in ("n", "s", "e", "o") and arg is None:
            return Accion(ACC_MOVER, nombre.upper())
        if nombre in ("mover", "ir") and arg is not None and _direccion(arg) is not None:
            return Accion(ACC_MOVER, _direccion(arg))
        if nombre == "abrir" and arg is not None and _direccion(arg) is not None:
            return Accion(ACC_ABRIR, _direccion(arg))
        if nombre in ("atacar", "recoger"):
            tipo = ACC_ATACAR if nombre == "atacar" else ACC_RECOGER
            if arg is None:
                return Accion(tipo, 0)
            if arg.isdigit() and int(arg) >= 1:
                return Accion(tipo, int(arg) - 1)
            return None
        if nombre in ("esperar", "z"):
            return Accion(ACC_ESPERAR)
        if nombre == "soltar":
            return Accion(ACC_SOLTAR)
        if nombre == "equipar":
            return Accion(ACC_EQUIPAR)
        if nombre == "usar":
            return Accion(ACC_USAR)
        if nombre in ("retroceso", "pergamino"):
            return Accion(ACC_RETROCESO)
        if nombre == "sig":
            return Accion(ACC_SIGUIENTE)
        if nombre == "ant":
            return Accion(ACC_ANTERIOR)
        return None

    def ejecutarAccion(self, accion):
        ##Ejecuta en el modelo y anota en la bitácora de partida lo que cambia el estado.
        resultado = self.modelo.ejecutar(accion)
        if resultado.ok and resultado.registrable and self.registro is not None:
            self.registro.registrarAccion(accion.aTexto())
        if self.modelo.estado != EN_CURSO:
            self._cerrarPartida()
        return resultado

    def procesar(self, texto):
        ## Procesa una línea del usuario. Devuelve True si la sesión debe terminar.
        palabra = texto.strip().lower().split()
        if len(palabra) == 0:
            return False
        comando = palabra[0]
        if comando in ("salir", "q"):
            return True
        if comando == "ayuda":
            self._decir(AYUDA)
            return False
        if comando == "inv":
            self._mostrarInventario()
            return False
        if comando == "ordenar":
            self._ordenar(palabra[1] if len(palabra) > 1 else "")
            return False
        if comando in ("puntajes", "tabla"):
            self._mostrarPuntajes()
            return False
        if comando in ("guardar", "cargar"):
            self._guardarCargar(comando, palabra[1] if len(palabra) > 1 else "")
            return False
        if comando == "mapa":
            self._mostrarMapa()
            return False
        if comando == "historia":
            self._mostrarHistoria(palabra[1] if len(palabra) > 1 else "")
            return False
        if comando == "ir":
            if len(palabra) == 2 and _direccion(palabra[1]) is not None:
                pass
            elif len(palabra) >= 2 and palabra[1] == "a":
                if len(palabra) >= 3:
                    self._ejecutarIrA(palabra[2])
                    return False
                else:
                    self._decir("Uso: ir a <id_sala>")
                    return False
            elif len(palabra) == 2 and palabra[1].isdigit():
                self._ejecutarIrA(palabra[1])
                return False
            elif len(palabra) >= 2:
                destinoStr = palabra[2] if (len(palabra) >= 3 and palabra[1] == "a") else palabra[1]
                self._ejecutarIrA(destinoStr)
                return False
        accion = self.interpretar(texto)
        if accion is None:
            self._decir("No entiendo ese comando. Escribe 'ayuda'.")
            return False
        self.ejecutarAccion(accion)
        return False

    def bucleInteractivo(self):
        self.vista.mostrar(self.modelo)
        while self.modelo.estado == EN_CURSO:
            texto = self.vista.leerComando()
            if texto is None:
                break
            if self.procesar(texto):
                break
            self.vista.mostrar(self.modelo)
        if self.modelo.estado != EN_CURSO:
            self.vista.mostrar(self.modelo)
            self.vista.mostrarFinal(self.modelo)

    def reproducir(self, lineas):

       ## Devuelve (True, "") o (False, motivo) si una acción canónica no se puede ejecutar.
        numero = 0
        for linea in lineas:
            numero += 1
            if len(linea.strip()) == 0:
                continue
            accion = accionesDesdeTexto(linea)
            if accion is None:
                return (False, "Línea %d no es una acción válida: %r" % (numero, linea))
            resultado = self.modelo.ejecutar(accion)
            if not resultado.ok:
                return (False, "Línea %d fue rechazada (%s): %s" % (numero, linea, resultado.mensaje))
            if self.modelo.estado != EN_CURSO:
                break
        return (True, "")

    def reproducirHasta(self, lineas, hastaReloj):
        """Reproduce la partida hasta el instante t (§3.6) y muestra el estado en ese instante."""
        if hastaReloj < 0:
            return (False, "El instante de reproducción no puede ser negativo (--hasta %d)." % hastaReloj)
        numero = 0
        for linea in lineas:
            numero += 1
            if len(linea.strip()) == 0:
                continue
            accion = accionesDesdeTexto(linea)
            if accion is None:
                return (False, "Línea %d no es una acción válida: %r" % (numero, linea))
            if self.modelo.reloj >= hastaReloj or self.modelo.estado != EN_CURSO:
                break
            resultado = self.modelo.ejecutar(accion)
            if not resultado.ok:
                return (False, "Línea %d fue rechazada (%s): %s" % (numero, linea, resultado.mensaje))
            if self.modelo.estado != EN_CURSO:
                break

        if self.modelo.reloj < hastaReloj:
            print("La partida terminó antes del instante t=%d (terminó en reloj=%d)."
                  % (hastaReloj, self.modelo.reloj))

        tiempoConsulta = min(hastaReloj, self.modelo.reloj)
        try:
            resumen = self.modelo.consultarHistoriaTiempo(tiempoConsulta)
            print(resumen)
        except (ValueError, RuntimeError) as err:
            print("Error en consulta histórica: %s" % err)
        return (True, "")

    def _mostrarHistoria(self, arg):
        if not arg:
            self._decir("Uso: historia <t> | historia #k")
            return
        try:
            if arg.startswith("#"):
                numStr = arg[1:]
                if not numStr.isdigit():
                    self._decir("Número de acción inválido: %s" % arg)
                    return
                k = int(numStr)
                res = self.modelo.consultarHistoriaAccion(k)
                self._decir(res)
            else:
                if not arg.isdigit():
                    self._decir("Instante de tiempo inválido: %s" % arg)
                    return
                t = int(arg)
                res = self.modelo.consultarHistoriaTiempo(t)
                self._decir(res)
        except (ValueError, RuntimeError) as err:
            self._decir("Error en historia: %s" % err)


    def _cerrarPartida(self):
        if self.termino:
            return
        self.termino = True
        if self.puntajes is not None:
            r = self.modelo.resultadoPartida()
            self.puntajes.registrarPartida(self.nombre, self.idCripta, self.versionCripta,
                                           r.acciones, r.derrotados, r.tiempoFinal,
                                           r.estado == VICTORIA)
        if self.reporte is not None:
            self._decir(self.reporte())      # la GUI también tiene que mostrar el reporte (5.1)

    def _mostrarPuntajes(self):
        if self.puntajes is None:
            self._decir("Tabla de puntajes no disponible.")
            return
        if hasattr(self.puntajes, "formatearTabla"):
            self._decir(self.puntajes.formatearTabla())
        else:
            tabla = self.puntajes.obtenerTablaOrdenada()
            self._decir("Partidas registradas: %d" % len(tabla))

    def _decir(self, texto):
        if self.vista is not None:
            self.vista.mostrarTexto(texto)

    def _mostrarInventario(self):
        lineas = []
        for objeto in self.modelo.inventario.objetos():
            lineas.append("  - " + self.modelo.nombreDe(objeto.tipoId))
        self._decir("Inventario:\n" + ("\n".join(lineas) if len(lineas) > 0 else "  (vacío)"))

    def _ordenar(self, criterio):
        inventario = self.modelo.inventario
        if not hasattr(inventario, "vistaOrdenada"):
            self._decir("La vista ordenada la aporta el inventario de Jorge.")
            return
        lista = inventario.vistaOrdenada(criterio)
        lineas = []
        for objeto in lista:
            lineas.append("  - " + self.modelo.nombreDe(objeto.tipoId))
        self._decir("Inventario por %s:\n%s" % (criterio, "\n".join(lineas)))

    def _guardarCargar(self, comando, ruta):
        if self.guardado is None:
            self._decir("El guardado de partida no está disponible en este modo.")
            return
        if len(ruta) == 0:
            self._decir("Indica un archivo: %s <archivo>" % comando)
            return
        try:
            if comando == "guardar":
                self.guardado.guardar(self.modelo, ruta)
                self._decir("Partida guardada en %s." % ruta)
            else:
                self.guardado.cargar(self.modelo, ruta)
                self._decir("Partida cargada desde %s." % ruta)
        except Exception as error:
            self._decir("No se pudo %s: %s" % (comando, error))

    def _mostrarMapa(self):
        from model.ordenamiento.Selector import ordenar
        mapa = self.modelo.mapaConocido
        exploradas = ordenar(mapa.listaExploradas())
        avistadas = ordenar(mapa.listaAvistadas(self.modelo.salas))
        lineas = ["=== MAPA CONOCIDO ==="]
        lineas.append("Salas exploradas (%d):" % len(exploradas))
        for sId in exploradas:
            sala = self.modelo.salas.buscar(sId)
            if sala is None:
                continue
            salidas = []
            for s in sala.salidas:
                # N-02: tres estados; una puerta que el jugador nunca observó no revela su estado real
                estadoP = mapa.estadoPuertaRecordada(sala.id, s.destinoId)
                if estadoP == "sin_observar":
                    estadoP = "sin observar"
                salidas.append("%s->Sala %s (costo: %d, %s)" % (s.direccion, s.destinoId, s.costo, estadoP))
            lineas.append("  Sala %s (%s): %s" % (sala.id, sala.nombre, "; ".join(salidas) if salidas else "sin salidas"))
        lineas.append("Salas avistadas (%d): %s" % (len(avistadas), ", ".join(str(x) for x in avistadas) if avistadas else "ninguna"))
        self._decir("\n".join(lineas))

    def _ejecutarIrA(self, destinoStr):
        """«ir a» (§3.4). Las reglas viven en el modelo (validarViaje y pasoViaje, N-03):
        el controlador solo repite el paso, registra en la bitácora de partida y muestra el motivo."""
        try:
            destId = int(destinoStr)
        except ValueError:
            self._decir("Identificador de sala inválido: '%s'. Debe ser un número." % destinoStr)
            return

        ok, motivo = self.modelo.validarViaje(destId)
        if not ok:
            self._decir(self._textoMotivoViaje(motivo, destId))
            return

        if self.registro is not None and hasattr(self.registro, "registrarComentario"):
            self.registro.registrarComentario("ir a %s" % destId)

        while True:
            salida, motivo = self.modelo.pasoViaje(destId)
            if salida is not None:
                self._registrarPasoViaje(salida)
            partidaTermino = self.modelo.estado != EN_CURSO
            if partidaTermino:
                self._cerrarPartida()
            if motivo is not None and motivo != self.modelo.VIAJE_FIN_PARTIDA:
                self._decir(self._textoMotivoViaje(motivo, destId))
            if partidaTermino or motivo is not None:
                return

    def _registrarPasoViaje(self, salida):
        if self.registro is not None:
            self.registro.registrarAccion(Accion(ACC_MOVER, salida.direccion).aTexto())

    def _textoMotivoViaje(self, motivo, destId):
        modelo = self.modelo
        sala = modelo.salas.buscar(destId)
        nombre = sala.nombre if sala is not None else str(destId)
        if motivo == modelo.VIAJE_LLEGO:
            return "Has llegado a tu destino: %s." % nombre
        if motivo == modelo.VIAJE_ENEMIGOS:
            return "El viaje se detiene: la sala contiene enemigos."
        if motivo == modelo.VIAJE_DANIO:
            return "El viaje se detiene: has recibido daño."
        if motivo == modelo.VIAJE_SIN_RUTA:
            return "El viaje se detiene: no existe ruta conocida abierta hacia %s." % nombre
        if motivo == modelo.VIAJE_RECHAZADO:
            return "El viaje se detiene: %s" % modelo.mensajeRechazoViaje
        if motivo == modelo.VIAJE_NO_EXISTE:
            return "La sala %s no existe en la cripta." % destId
        if motivo == modelo.VIAJE_NO_EXPLORADA:
            return "ir a hacia una sala no explorada: se rechaza y no consume tiempo."
        if motivo == modelo.VIAJE_YA_EN_DESTINO:
            return "Ya estás en la sala %s." % destId
        if motivo == modelo.VIAJE_FIN_PARTIDA:
            return "La partida ya terminó."
        return "El viaje se detiene."