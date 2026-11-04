# Línea de tiempo y puntos de control (§3.6, §5.5 Parte II).
# Cumple con el Principio I de la Constitución y gestiona puntos de control cada K acciones.

from model.Acciones import Accion
from model.Constantes import (EN_CURSO, EV_JUGADOR)


NOMBRES_EFECTO = {
    0: "Veneno",
    1: "Regeneración",
    2: "Antorcha",
    3: "Velocidad"
}


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
            nom = NOMBRES_EFECTO.get(ef.clase, "Efecto-%s" % ef.clase)
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
        self._puntosControl = []  # lista de dicts: {"numAccion": int, "reloj": int, "snapshot": dict}
        self._acciones = []       # lista de dicts: {"numAccion": int, "accion": Accion, "reloj": int}

    def registrarPuntoControl(self, numAccion, reloj, snapshot):
        """Registra un punto de control con el estado completo del modelo."""
        # Si ya existe un punto de control para este número de acción, se reemplaza
        for p in self._puntosControl:
            if p["numAccion"] == numAccion:
                p["reloj"] = reloj
                p["snapshot"] = snapshot
                return
        self._puntosControl.append({
            "numAccion": numAccion,
            "reloj": reloj,
            "snapshot": snapshot
        })

    def debeCrearPuntoControl(self, numAccion):
        """Indica si corresponde un punto de control tras ejecutar numAccion."""
        return (numAccion % self.k == 0)

    def registrarAccion(self, numAccion, accion, relojDecision):
        """Registra una acción canónica realizada por el jugador."""
        self._acciones.append({
            "numAccion": numAccion,
            "accion": accion,
            "reloj": relojDecision
        })

    def recortar(self, nuevoTotalAcciones):
        """Descarta las acciones y puntos de control revertidos con pergamino (§3.6, §5.5)."""
        # Recorta la lista de acciones a nuevoTotalAcciones en O(1)
        if nuevoTotalAcciones < len(self._acciones):
            self._acciones = self._acciones[:nuevoTotalAcciones]

        # Elimina puntos de control posteriores
        idx = len(self._puntosControl) - 1
        while idx >= 0 and self._puntosControl[idx]["numAccion"] > nuevoTotalAcciones:
            self._puntosControl.pop()
            idx -= 1

    def cantidadPuntosControl(self):
        return len(self._puntosControl)

    def cantidadAcciones(self):
        return len(self._acciones)

    def buscarPuntoControlMasCercanoAccion(self, k):
        """Encuentra el punto de control anterior más cercano a la acción k."""
        mejor = self._puntosControl[0]
        for p in self._puntosControl:
            if p["numAccion"] <= k - 1:
                if p["numAccion"] >= mejor["numAccion"]:
                    mejor = p
            else:
                break
        return mejor

    def buscarPuntoControlMasCercanoTiempo(self, t):
        """Encuentra el punto de control anterior más cercano al tiempo t."""
        mejor = self._puntosControl[0]
        for p in self._puntosControl:
            if p["reloj"] <= t:
                if p["reloj"] >= mejor["reloj"]:
                    mejor = p
            else:
                break
        return mejor

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
        modeloAux = _crearModeloAuxiliar(modeloBase.proveedor, modeloBase.semilla, cp["snapshot"])

        # Re-simular hacia adelante desde cp["numAccion"] hasta k - 1
        accionesAEjecutar = self._acciones[cp["numAccion"] : k - 1]
        for item in accionesAEjecutar:
            modeloAux.ejecutar(item["accion"])

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
        modeloAux = _crearModeloAuxiliar(modeloBase.proveedor, modeloBase.semilla, cp["snapshot"])

        # Re-simular acciones
        # Buscamos cuáles acciones ocurrieron antes o en t
        idx = cp["numAccion"]
        total = len(self._acciones)

        while idx < total:
            item = self._acciones[idx]
            relojAccion = item["reloj"]

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
                sigReloj = self._acciones[idx + 1]["reloj"] if idx + 1 < total else None
                if sigReloj is not None and sigReloj <= t:
                    modeloAux.ejecutar(item["accion"])
                else:
                    # Esta es la última acción del jugador antes de t
                    modeloAux.ejecutarHasta(item["accion"], t)
                    break
            idx += 1

        if idx >= total and modeloAux.reloj < t:
            modeloAux._correrEventosHasta(t)

        return formatearResumenHistoria(modeloAux, reloj=t)

    # ----------------------------------------------------------- Serialización
    def capturar(self):
        accionesSerializadas = []
        for item in self._acciones:
            acc = item["accion"]
            accionesSerializadas.append([item["numAccion"], acc.tipo, acc.argumento, item["reloj"]])

        return {
            "k": self.k,
            "puntosControl": self._puntosControl,
            "acciones": accionesSerializadas
        }

    def restaurar(self, datos):
        self.k = datos.get("k", 20)
        self._puntosControl = datos.get("puntosControl", [])
        self._acciones = []
        for reg in datos.get("acciones", []):
            numAccion, tipo, arg, reloj = reg
            self._acciones.append({
                "numAccion": numAccion,
                "accion": Accion(tipo, arg),
                "reloj": reloj
            })
