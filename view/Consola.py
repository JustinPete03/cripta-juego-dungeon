# Vista de consola. Solo lee el estado del modelo y recoge texto; no cambia nada.
from model.Constantes import EN_CURSO, VICTORIA


class VistaConsola:
    def leerComando(self):
        try:
            return input("> ")
        except EOFError:
            return None

    def mostrarTexto(self, texto):
        print(texto)

    def mostrar(self, modelo):
        jugador = modelo.jugador
        sala = jugador.sala
        lineas = []
        lineas.append("")
        lineas.append("=" * 60)
        lineas.append("Sala %s: %s   |   reloj virtual: %d" % (sala.id, sala.nombre, modelo.reloj))
        lineas.append("Vida %d/%d  Ataque %d(+%d)  Defensa %d(+%d)  Velocidad %d"
                      % (jugador.vida, jugador.vidaMax, jugador.ataque, jugador.bonoAtaque,
                         jugador.defensa, jugador.bonoDefensa, jugador.velocidad))
        efectos = modelo.efectos.descripcionjugador(modelo)
        if len(efectos) > 0:
            lineas.append("Efectos: " + ", ".join(efectos))

        salidas = []
        for salida in sala.salidas:
            estado = "cerrada" if salida.puerta.cerrada else "abierta"
            salidas.append("%s->%s (%s)" % (salida.direccion, salida.destino.nombre, estado))
        lineas.append("Salidas: " + ("; ".join(salidas) if len(salidas) > 0 else "ninguna"))

        if len(sala.enemigos) > 0:
            lineas.append("Enemigos:")
            for i in range(len(sala.enemigos)):
                enemigo = sala.enemigos[i]
                lineas.append("  %d) %s  vida %d/%d" % (i + 1, enemigo.etiqueta(), enemigo.vida, enemigo.vidaMax))
        if len(sala.objetos) > 0:
            lineas.append("En el suelo:")
            for i in range(len(sala.objetos)):
                lineas.append("  %d) %s" % (i + 1, modelo.nombreDe(sala.objetos[i].tipoId)))
        for trampa in sala.trampas:
            lineas.append("Trampa: %s (%s)" % (modelo.nombreDe(trampa.tipoId),
                                               "armada" if trampa.armada else "desarmada"))
        actual = modelo.inventario.actual()
        cantidad = len(modelo.inventario.objetos())
        if actual is not None:
            lineas.append("Inventario (%d objetos), viendo: %s" % (cantidad, modelo.nombreDe(actual.tipoId)))
        else:
            lineas.append("Inventario vacío")
        lineas.append("-" * 60)
        for mensaje in modelo.bitacora.ultimos():
            lineas.append(mensaje)
        print("\n".join(lineas))

    def mostrarFinal(self, modelo):
        resultado = modelo.resultadoPartida()
        titulo = "VICTORIA" if resultado.estado == VICTORIA else "DERROTA"
        print("\n*** %s ***" % titulo)
        print("Acciones: %d | Enemigos derrotados: %d | Tiempo final: %d"
              % (resultado.acciones, resultado.derrotados, resultado.tiempoFinal))