# Línea de tiempo y puntos de control (§3.6, §5.5 Parte II).
# Cumple con el Principio I de la Constitución y gestiona puntos de control cada K acciones.

from model.Acciones import Accion
from model.Constantes import (EN_CURSO, EV_JUGADOR)


def nombreEfecto(clase):
    if clase == 0:
        return "Veneno"
    elif clase == 1:
        return "Regeneración"
    elif clase == 2:
        return "Antorcha"
    elif clase == 3:
        return "Velocidad"
    return "Efecto-%s" % clase


class PuntoControl:
    __slots__ = ("numAccion", "reloj", "snapshot")

    def __init__(self, numAccion, reloj, snapshot):
        self.numAccion = numAccion
        self.reloj = reloj
        self.snapshot = snapshot


class RegistroAccion:
    __slots__ = ("numAccion", "accion", "reloj")

    def __init__(self, numAccion, accion, reloj):
        self.numAccion = numAccion
        self.accion = accion
        self.reloj = reloj


def formatearResumenHistoria(modelo, numAccion=None, reloj=None):
    """Genera el resumen de historia exigido por §3.6."""
    if reloj is None:
        reloj = modelo.reloj
    lineas = []
    if numAccion is not None:
        lineas.append("=== HISTORIA: Estado antes de Acción #%d (Reloj: %d) ===" % (numAccion, reloj))
    else:
        lineas.append("=== HISTORIA: Estado en Reloj: %d ===" % reloj)

    sala = modelo.jugador.sala
    lineas.append("Sala actual: Sala %d (%s)" % (sala.id, sala.nombre))

    j = modelo.jugador
    lineas.append("Jugador: Vida %d/%d | Ataque %d (+%d) | Defensa %d (+%d) | Vel %d" %
                  (j.vida, j.vidaMax, j.ataque, j.bonoAtaque, j.defensa, j.bonoDefensa, j.velocidad))

    invObjs = modelo.inventario.objetos()
    if invObjs:
        nombresInv = [modelo.nombreDe(obj.tipoId) for obj in invObjs]
        lineas.append("Inventario (%d): %s" % (len(invObjs), ", ".join(nombresInv)))
    else:
        lineas.append("Inventario: (vacío)")

    activos = getattr(modelo.efectos, "activos", [])
    if activos:
        textosEf = []
        for ef in activos:
            nom = nombreEfecto(ef.clase)
            restante = max(0, ef.fin - modelo.reloj) if ef.fin > 0 else 0
            textosEf.append("%s (restante: %d)" % (nom, restante))
        lineas.append("Efectos activos (%d): %s" % (len(activos), ", ".join(textosEf)))
    else:
        lineas.append("Efectos activos: (ninguno)")

    enemigosSala = sala.enemigos
    lineas.append("Enemigos en la sala (%d):" % len(enemigosSala))
    for e in enemigosSala:
        nom = modelo.nombreDe(e.tipoId) if hasattr(modelo, "nombreDe") else e.tipoId
        lineas.append("  * %s [ID: %s, Vida: %d/%d]" % (nom, e.instancia, e.vida, e.vidaMax))

    if hasattr(modelo, "mapaConocido"):
        exploradas = modelo.mapaConocido.listaExploradas()
        avistadas = modelo.mapaConocido.listaAvistadas(modelo.salas)
        lineas.append("Mapa conocido: %d salas exploradas, %d salas avistadas" %
                      (len(exploradas), len(avistadas)))

    return "\n".join(lineas)


def _crearModeloAuxiliar(proveedor, semilla, snapshot):
    """Instancia y restaura un modelo réplica para re-simulación sin tocar la partida en curso."""
    from model.Inventario import Inventario
    from model.Diario import Diario
    from model.efectosTrampa import efectosTrampa
    from model.Juego import Modelo

    efectos = efectosTrampa()
    modeloAux = Modelo(proveedor, semilla, Inventario(proveedor), Diario(), efectos)
    efectos.registrarEn(modeloAux)
    modeloAux.iniciarPartida()
    modeloAux.restaurarEstado(snapshot)
    return modeloAux


class LineaTiempo:
    """Administra puntos de control cada K acciones y la reconstrucción histórica (§3.6, §5.5)."""

    def __init__(self, k=20):
        self.k = max(1, k)
        self._puntosControl = []  # lista de objetos PuntoControl
        self._acciones = []       # lista de objetos RegistroAccion

    def registrarPuntoControl(self, numAccion, reloj, snapshot):
        """Registra un punto de control con el estado completo del modelo.
        Aprovecha el invariante de orden creciente para verificar únicamente el último punto en O(1).
        """
        if self._puntosControl and self._puntosControl[-1].numAccion == numAccion:
            ultimo = self._puntosControl[-1]
            ultimo.reloj = reloj
            ultimo.snapshot = snapshot
            return
        self._puntosControl.append(PuntoControl(numAccion, reloj, snapshot))

    def debeCrearPuntoControl(self, numAccion):
        """Indica si corresponde un punto de control tras ejecutar numAccion."""
        return (numAccion % self.k == 0)

    def registrarAccion(self, numAccion, accion, relojDecision):
        """Registra una acción canónica realizada por el jugador."""
        self._acciones.append(RegistroAccion(numAccion, accion, relojDecision))

    def recortar(self, nuevoTotalAcciones):
        """Descarta las acciones y puntos de control revertidos con pergamino (§3.6, §5.5).
        El costo real es proporcional a la cantidad de acciones descartadas O(Δ) con Δ <= 5,
        ya que el pergamino de retroceso revierte como máximo 5 acciones del jugador.
        """
        # Elimina en el lugar el rango final sin copiar la lista remanente (costo O(Δ))
        if nuevoTotalAcciones < len(self._acciones):
            del self._acciones[nuevoTotalAcciones:]

        # Elimina puntos de control posteriores
        idx = len(self._puntosControl) - 1
        while idx >= 0 and self._puntosControl[idx].numAccion > nuevoTotalAcciones:
            self._puntosControl.pop()
            idx -= 1

    def cantidadPuntosControl(self):
        return len(self._puntosControl)

    def cantidadAcciones(self):
        return len(self._acciones)

    def buscarPuntoControlMasCercanoAccion(self, k):
        """Encuentra el punto de control anterior más cercano a la acción k usando búsqueda binaria propia O(log P)."""
        target = k - 1
        low = 0
        high = len(self._puntosControl) - 1
        ans = 0
        while low <= high:
            mid = (low + high) // 2
            if self._puntosControl[mid].numAccion <= target:
                ans = mid
                low = mid + 1
            else:
                high = mid - 1
        return self._puntosControl[ans]

    def buscarPuntoControlMasCercanoTiempo(self, t):
        """Encuentra el punto de control anterior más cercano al tiempo t usando búsqueda binaria propia O(log P)."""
        low = 0
        high = len(self._puntosControl) - 1
        ans = 0
        while low <= high:
            mid = (low + high) // 2
            if self._puntosControl[mid].reloj <= t:
                ans = mid
                low = mid + 1
            else:
                high = mid - 1
        return self._puntosControl[ans]

    def consultarAccion(self, modeloBase, k):
        """Reconstruye el estado justo antes de la acción #k del jugador (§3.6)."""
        total = len(self._acciones)
        if k < 1 or k > total + 1:
            raise ValueError(
                "No se puede consultar la acción #%d: hasta ahora se han realizado %d acciones." % (k, total)
            )

        # Si se consulta la acción actual pendiente, el modeloBase ya está en ese estado
        if k == total + 1:
            return formatearResumenHistoria(modeloBase, numAccion=k, reloj=modeloBase.reloj)

        # Ubicar punto de control anterior
        cp = self.buscarPuntoControlMasCercanoAccion(k)
        modeloAux = _crearModeloAuxiliar(modeloBase.proveedor, modeloBase.semilla, cp.snapshot)

        # Re-simular hacia adelante desde cp.numAccion hasta k - 1
        accionesAEjecutar = self._acciones[cp.numAccion : k - 1]
        for item in accionesAEjecutar:
            modeloAux.ejecutar(item.accion)

        return formatearResumenHistoria(modeloAux, numAccion=k, reloj=modeloAux.reloj)

    def consultarTiempo(self, modeloBase, t):
        """Reconstruye el estado en el instante t (§3.6)."""
        if t < 0:
            raise ValueError("El instante de tiempo no puede ser negativo (t=%d)." % t)
        if t > modeloBase.reloj:
            raise ValueError(
                "No se puede consultar el futuro: el reloj actual es %d y se consultó t=%d."
                % (modeloBase.reloj, t)
            )
        if t == modeloBase.reloj:
            return formatearResumenHistoria(modeloBase, reloj=t)

        # Ubicar punto de control más cercano anterior o igual a t
        cp = self.buscarPuntoControlMasCercanoTiempo(t)
        modeloAux = _crearModeloAuxiliar(modeloBase.proveedor, modeloBase.semilla, cp.snapshot)

        # Re-simular acciones
        # Buscamos cuáles acciones ocurrieron antes o en t
        idx = cp.numAccion
        total = len(self._acciones)

        while idx < total:
            item = self._acciones[idx]
            relojAccion = item.reloj

            if relojAccion > t:
                # La acción ocurre en el futuro respecto a t: no se ejecuta la acción del jugador,
                # pero los eventos de la agenda hasta t sí deben procesarse
                modeloAux._correrEventosHasta(t)
                break
            elif relojAccion == t:
                # Si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla (§3.6)
                # Nos detenemos antes de ejecutarla
                break
            else:
                # relojAccion < t: verificamos si la SIGUIENTE acción también ocurre <= t
                sigReloj = self._acciones[idx + 1].reloj if idx + 1 < total else None
                if sigReloj is not None and sigReloj <= t:
                    modeloAux.ejecutar(item.accion)
                else:
                    # Esta es la última acción del jugador antes de t
                    modeloAux.ejecutarHasta(item.accion, t)
                    break
            idx += 1

        if idx >= total and modeloAux.reloj < t:
            modeloAux._correrEventosHasta(t)

        return formatearResumenHistoria(modeloAux, reloj=t)

    # ----------------------------------------------------------- Serialización
    def capturar(self):
        puntosSerializados = []
        for p in self._puntosControl:
            puntosSerializados.append({
                "numAccion": p.numAccion,
                "reloj": p.reloj,
                "snapshot": p.snapshot
            })

        accionesSerializadas = []
        for item in self._acciones:
            acc = item.accion
            accionesSerializadas.append([item.numAccion, acc.tipo, acc.argumento, item.reloj])

        return {
            "k": self.k,
            "puntosControl": puntosSerializados,
            "acciones": accionesSerializadas
        }

    def restaurar(self, datos):
        self.k = datos.get("k", 20)
        self._puntosControl = []
        for p in datos.get("puntosControl", []):
            if isinstance(p, PuntoControl):
                self._puntosControl.append(p)
            else:
                self._puntosControl.append(PuntoControl(p["numAccion"], p["reloj"], p["snapshot"]))
        self._acciones = []
        for reg in datos.get("acciones", []):
            numAccion, tipo, arg, reloj = reg
            self._acciones.append(RegistroAccion(numAccion, Accion(tipo, arg), reloj))
