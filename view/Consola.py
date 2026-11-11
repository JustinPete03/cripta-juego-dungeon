# Vista de consola mejorada para La Cripta.
# Proporciona una interfaz visual detallada, estructurada y de alta jugabilidad.
# Muestra costos de terreno, distingue claramente a cazadores, y ofrece barras de estado legibles.

from model.Constantes import EN_CURSO, VICTORIA, DERROTA


def _barraVida(vida, vidaMax, ancho=12):
    if vidaMax <= 0:
        return "[------------] 0/0"
    vidaClamped = max(0, min(vida, vidaMax))
    llenos = max(0, min(ancho, int(round((vidaClamped / vidaMax) * ancho))))
    vacios = ancho - llenos
    return f"[{'█' * llenos}{'░' * vacios}] {vida}/{vidaMax}"


class VistaConsola:
    def leerComando(self):
        try:
            return input("\n[Acción] > ")
        except EOFError:
            return None

    def mostrarTexto(self, texto):
        print(texto)

    def mostrar(self, modelo):
        jugador = modelo.jugador
        sala = jugador.sala
        anchoBox = 68

        lineas = [""]
        # Encabezado de la Sala y Reloj
        lineas.append("╔" + "═" * anchoBox + "╗")
        tituloSala = f" 📍 SALA {sala.id}: {sala.nombre.upper()} "
        relojStr = f" ⏱️ Reloj: t={modelo.reloj} "
        espacioMedio = anchoBox - len(tituloSala) - len(relojStr)
        if espacioMedio < 0:
            espacioMedio = 1
        lineas.append("║" + tituloSala + (" " * espacioMedio) + relojStr + "║")
        lineas.append("╠" + "═" * anchoBox + "╣")

        # Estado del Jugador (Vida con barra, Atributos y Efectos)
        barraHP = _barraVida(jugador.vida, jugador.vidaMax, 10)
        lineaStats = (
            f"║  ❤️ HP: {barraHP} | ⚔️ ATK: {jugador.ataque}(+{jugador.bonoAtaque}) "
            f"| 🛡️ DEF: {jugador.defensa}(+{jugador.bonoDefensa}) | ⚡ VEL: {jugador.velocidad}"
        )
        lineaStats = lineaStats.ljust(anchoBox + 1) + "║"
        lineas.append(lineaStats)

        efectos = modelo.efectos.descripcionjugador(modelo)
        if len(efectos) > 0:
            efectosStr = f"║  ✨ Efectos activos: {', '.join(efectos)}"
            lineas.append(efectosStr.ljust(anchoBox + 1) + "║")

        lineas.append("╠" + "─" * anchoBox + "╣")

        # Salidas con costo y estado de puerta (§7.3)
        lineas.append("║ 🚪 SALIDAS DISPONIBLES:")
        if len(sala.salidas) == 0:
            lineas.append("║    (No hay salidas aparentes en esta sala)".ljust(anchoBox + 1) + "║")
        else:
            for s in sala.salidas:
                if s.puerta.cerrada:
                    llaveReq = f" (Llave: {s.puerta.llave})" if s.puerta.llave else ""
                    cierreAuto = " [Auto-cierre]" if s.puerta.cierreAutomatico else ""
                    estadoPuerta = f"🔒 CERRADA{llaveReq}{cierreAuto}"
                else:
                    estadoPuerta = "🔓 ABIERTA"
                destinoNombre = s.destino.nombre if s.destino else f"Sala {s.destinoId}"
                lineaSalida = f"║   [{s.direccion}] ➔ {destinoNombre} (Sala {s.destinoId}) | Costo: {s.costo:>3} | {estadoPuerta}"
                lineas.append(lineaSalida.ljust(anchoBox + 1) + "║")

        # Enemigos presentes (distinguiendo cazadores con rango, §7.3)
        if len(sala.enemigos) > 0:
            lineas.append("╠" + "─" * anchoBox + "╣")
            lineas.append("║ 💀 ENEMIGOS EN LA SALA:")
            for i, enemigo in enumerate(sala.enemigos):
                if enemigo.comportamiento == "cazador":
                    etiquetaTipo = f"🏹 [CAZADOR PREDADOR - Rango: {enemigo.rango}]"
                elif enemigo.comportamiento == "rastreador":
                    etiquetaTipo = "🐾 [Rastreador olfativo]"
                elif enemigo.comportamiento == "errante":
                    etiquetaTipo = "🦇 [Patrullero errante]"
                else:
                    etiquetaTipo = "🛡️ [Guardián de sala]"

                barraEnem = _barraVida(enemigo.vida, enemigo.vidaMax, 8)
                lineaEnem = f"║   {i + 1}) {enemigo.etiqueta()} {etiquetaTipo} {barraEnem}"
                lineas.append(lineaEnem.ljust(anchoBox + 1) + "║")

        # Trampas en la sala
        if len(sala.trampas) > 0:
            lineas.append("╠" + "─" * anchoBox + "╣")
            lineas.append("║ ⚠️ TRAMPAS:")
            for trampa in sala.trampas:
                estadoT = "ARMADA" if trampa.armada else "DESARMADA (Recargando)"
                nomT = modelo.nombreDe(trampa.tipoId)
                lineaTrampa = f"║   • {nomT} [{estadoT}]"
                lineas.append(lineaTrampa.ljust(anchoBox + 1) + "║")

        # Objetos en el suelo
        if len(sala.objetos) > 0:
            lineas.append("╠" + "─" * anchoBox + "╣")
            lineas.append("║ 💎 OBJETOS EN EL SUELO:")
            for i, obj in enumerate(sala.objetos):
                nomObj = modelo.nombreDe(obj.tipoId)
                lineaObj = f"║   {i + 1}) {nomObj}"
                lineas.append(lineaObj.ljust(anchoBox + 1) + "║")

        # Inventario
        lineas.append("╠" + "─" * anchoBox + "╣")
        actual = modelo.inventario.actual()
        cantInv = len(modelo.inventario.objetos())
        capMax = getattr(modelo.inventario, "capacidad", 10)
        viendoStr = modelo.nombreDe(actual.tipoId) if actual is not None else "(nada)"
        lineaInv = f"║ 🎒 MOCHILA [{cantInv}/{capMax}] | Viendo: {viendoStr}"
        lineas.append(lineaInv.ljust(anchoBox + 1) + "║")

        # Barra de ayuda rápida de comandos
        lineas.append("╠" + "─" * anchoBox + "╣")
        lineas.append("║ 🎮 COMANDOS: n/s/e/o | ir a <sala> | abrir <dir> | atacar [k]       ║")
        lineas.append("║             recoger [k] | usar | equipar | soltar | sig/ant | inv    ║")
        lineas.append("║             mapa | historia <t>/#k | retroceso | guardar | ayuda     ║")
        lineas.append("╚" + "═" * anchoBox + "╝")

        # Bitácora de eventos recientes
        ultimos = list(modelo.bitacora.ultimos())
        if ultimos:
            lineas.append("📜 Últimos eventos:")
            for mensaje in ultimos[-5:]:
                lineas.append(f"   {mensaje}")

        print("\n".join(lineas))

    def mostrarFinal(self, modelo):
        resultado = modelo.resultadoPartida()
        print("\n" + "=" * 60)
        if resultado.estado == VICTORIA:
            print("  🏆 ¡¡¡ VICTORIA !!! HAS ESCAPADO DE LA CRIPTA 🏆")
        elif resultado.estado == DERROTA:
            print("  💀 HAS SUCUMBIDO ANTE LOS PELIGROS DE LA CRIPTA 💀")
        else:
            print(f"  🏁 PARTIDA FINALIZADA ({resultado.estado})")
        print("-" * 60)
        print(f"  • Acciones ejecutadas : {resultado.acciones}")
        print(f"  • Enemigos derrotados : {resultado.derrotados}")
        print(f"  • Tiempo virtual final: {resultado.tiempoFinal}")
        print("=" * 60 + "\n")
