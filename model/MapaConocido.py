# Estructura de datos del conocimiento del jugador (Niebla de guerra y memoria de puertas).
# Cumple con el Principio I de la Constitución: implementado con Tabla propia sin dict ni set.

from model.Tabla import Tabla

ESTADO_EXPLORADA = "explorada"
ESTADO_AVISTADA = "avistada"
ESTADO_DESCONOCIDA = "desconocida"

# Los tres estados que el mapa puede recordar de una puerta (§3.3, N-02)
PUERTA_ABIERTA = "abierta"
PUERTA_CERRADA = "cerrada"
PUERTA_SIN_OBSERVAR = "sin_observar"


def claveConexion(uId, vId):
    u = int(uId)
    v = int(vId)
    if u < v:
        return "%d-%d" % (u, v)
    return "%d-%d" % (v, u)


class MapaConocido:
    """Gestiona el conocimiento parcial del mapa: salas exploradas, salas avistadas
    y memoria de puertas observadas.

    Dos operaciones distintas (N-01):
      * marcarExplorada(sala): la sala pasa a ser conocida (por ejemplo, la revela la antorcha).
        NO registra ninguna puerta.
      * actualizarPuertasObservadas(sala): el jugador está en esa sala y ve el estado real
        de sus puertas (§3.3: una puerta solo se observa estando en una de sus dos salas).

    explorarSala(sala) hace las dos y SOLO debe usarse cuando el jugador entra a la sala.
    Las vecinas reveladas por la antorcha usan marcarExplorada.

    La memoria nunca consulta el estado real de una puerta que no se observó (N-02).
    Todo es reversible para el Diario (pergamino de retroceso).
    """

    def __init__(self, registrador=None):
        self._exploradas = Tabla()
        self._memoriaPuertas = Tabla()   # claveConexion -> bool (True = cerrada)
        self._registrador = registrador  # función para registrar inversas en el Diario

    def fijarRegistrador(self, registrador):
        self._registrador = registrador

    def _registrar(self, deshacer):
        if self._registrador is not None:
            self._registrador(deshacer)

    def estaExplorada(self, idSala):
        return self._exploradas.contiene(idSala)

    def marcarExplorada(self, sala):
        """Marca una sala como explorada sin observar sus puertas (N-01).
        La usa la antorcha con las vecinas de la sala donde está el jugador."""
        if not self._exploradas.contiene(sala.id):
            self._exploradas.guardar(sala.id, True)
            salaId = sala.id

            def deshacerExplorada():
                self._exploradas.quitar(salaId)
            self._registrar(deshacerExplorada)

    def explorarSala(self, sala):
        """Marca la sala como explorada y observa sus puertas al entrar.
        Para las vecinas reveladas por la antorcha, usa marcarExplorada()."""
        self.marcarExplorada(sala)
        self.actualizarPuertasObservadas(sala)

    def actualizarPuertasObservadas(self, sala):
        """El jugador observa las puertas de todas las salidas de la sala en la que está.
        Debe llamarse al entrar a la sala y cada vez que una puerta de esa sala cambia
        mientras el jugador está en ella."""
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

    def estadoPuertaRecordada(self, uId, vId):
        """Devuelve PUERTA_ABIERTA, PUERTA_CERRADA o PUERTA_SIN_OBSERVAR (§3.3, N-02)."""
        recordada = self._memoriaPuertas.obtener(claveConexion(uId, vId), None)
        if recordada is None:
            return PUERTA_SIN_OBSERVAR
        if recordada:
            return PUERTA_CERRADA
        return PUERTA_ABIERTA

    def puertaRecordadaAbierta(self, uId, vId):
        """True solo si el jugador observó la puerta y la vio abierta (§3.4, N-02).
        Una puerta sin observar NO se considera abierta."""
        return self.estadoPuertaRecordada(uId, vId) == PUERTA_ABIERTA

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