# Estructura de datos del conocimiento del jugador (Niebla de guerra y memoria de puertas).
# Cumple con el Principio I de la Constitución: implementado con Tabla propia sin dict ni set.

from model.Tabla import Tabla

ESTADO_EXPLORADA = "explorada"
ESTADO_AVISTADA = "avistada"
ESTADO_DESCONOCIDA = "desconocida"


def claveConexion(uId, vId):
    u = int(uId)
    v = int(vId)
    if u < v:
        return "%d-%d" % (u, v)
    return "%d-%d" % (v, u)


class MapaConocido:
    """Gestiona el conocimiento parcial del mapa, las salas exploradas,
    las salas avistadas y la memoria de puertas observadas.
    
    Totalmente reversible para el Diario (pergamino de retroceso).
    """

    def __init__(self, registrador=None):
        self._exploradas = Tabla()
        self._memoriaPuertas = Tabla()   # claveConexion -> bool (cerrada)
        self._registrador = registrador  # funcion para registrar inversas en el Diario

    def fijarRegistrador(self, registrador):
        self._registrador = registrador

    def _registrar(self, deshacer):
        if self._registrador is not None:
            self._registrador(deshacer)

    def estaExplorada(self, idSala):
        return self._exploradas.contiene(idSala)

    def explorarSala(self, sala):
        """Marca una sala como explorada y actualiza la memoria de sus puertas observadas."""
        if not self._exploradas.contiene(sala.id):
            self._exploradas.guardar(sala.id, True)
            salaId = sala.id
            def deshacerExplorada():
                self._exploradas.quitar(salaId)
            self._registrar(deshacerExplorada)

        self.actualizarPuertasObservadas(sala)

    def actualizarPuertasObservadas(self, sala):
        """El jugador observa las puertas de todas las salidas de la sala en la que está."""
        for salida in sala.salidas:
            clave = claveConexion(sala.id, salida.destinoId)
            estadoReal = salida.puerta.cerrada
            estadoAnterior = self._memoriaPuertas.obtener(clave, None)

            if estadoAnterior != estadoReal:
                self._memoriaPuertas.guardar(clave, estadoReal)
                def deshacerPuerta(c=clave, ant=estadoAnterior):
                    if ant is None:
                        self._memoriaPuertas.quitar(c)
                    else:
                        self._memoriaPuertas.guardar(c, ant)
                self._registrar(deshacerPuerta)

    def puertaRecordadaCerrada(self, uId, vId, puertaReal=None):
        clave = claveConexion(uId, vId)
        recordada = self._memoriaPuertas.obtener(clave, None)
        if recordada is not None:
            return bool(recordada)
        if puertaReal is not None:
            return bool(puertaReal.cerrada)
        return False

    def puertaRecordadaAbierta(self, uId, vId, puertaReal=None):
        return not self.puertaRecordadaCerrada(uId, vId, puertaReal)

    def estadoSala(self, idSala, salasIndice):
        """Determina el estado de una sala: explorada, avistada o desconocida."""
        if self.estaExplorada(idSala):
            return ESTADO_EXPLORADA

        sala = salasIndice.buscar(idSala)
        if sala is not None:
            for salida in sala.salidas:
                if self.estaExplorada(salida.destinoId):
                    return ESTADO_AVISTADA

        return ESTADO_DESCONOCIDA

    def listaExploradas(self):
        return self._exploradas.claves()

    def listaAvistadas(self, salasIndice):
        avistadas = []
        avistadasSet = Tabla()
        for idExplorada in self.listaExploradas():
            sala = salasIndice.buscar(idExplorada)
            if sala is None:
                continue
            for salida in sala.salidas:
                destId = salida.destinoId
                if not self.estaExplorada(destId) and not avistadasSet.contiene(destId):
                    avistadasSet.guardar(destId, True)
                    avistadas.append(destId)
        return avistadas
