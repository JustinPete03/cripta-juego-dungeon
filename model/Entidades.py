#Entidades del modelo. No conocen HTTP, archivos ni el view.


class Puerta:
    #Una puerta compartida por las dos salidas que conecta (2.1: cada salida conecta dos salas).

    def __init__(self, cerrada, llave, cierreAutomatico):
        self.cerrada = cerrada
        self.llave = llave
        self.cierreAutomatico = cierreAutomatico
        self.eventoCierre = None


class Salida:
    def __init__(self, direccion, origen, destinoId, puerta):
        self.direccion = direccion
        self.origen = origen
        self.destinoId = destinoId
        self.destino = None          # referencia directa a la Sala (rastro en O(salidas))
        self.puerta = puerta


class Sala:
    def __init__(self, idSala, nombre):
        self.id = idSala
        self.nombre = nombre
        self.salidas = []            # máximo 4, en orden canónico N, S, E, O
        self.rastro = -1             # -1: el jugador nunca estuvo (2.9)
        self.contenidoIncorporado = False
        self.enemigos = []           # activos y dormidos que están en esta sala
        self.objetos = []            # ObjetoInstancia en el suelo
        self.trampas = []

    def salida(self, direccion):
        for salida in self.salidas:
            if salida.direccion == direccion:
                return salida
        return None


class ObjetoInstancia:
    def __init__(self, tipoId, serie):
        self.tipoId = tipoId
        self.serie = serie           # número local para distinguir instancias


class Trampa:
    def __init__(self, instancia, tipoId):
        self.instancia = instancia
        self.tipoId = tipoId
        self.armada = True
        self.eventoRearme = None


class Actor:
    def __init__(self, vida, vidaMax, ataque, defensa, velocidad):
        self.vida = vida
        self.vidaMax = vidaMax
        self.ataque = ataque
        self.defensa = defensa
        self.velocidad = velocidad
        self.tiempoSiguiente = 0
        self.evento = None           # evento pendiente (para cancelarlo al morir)
        self.vivo = True


class Jugador(Actor):
    def __init__(self, vidaMax, ataque, defensa, velocidad):
        Actor.__init__(self, vidaMax, vidaMax, ataque, defensa, velocidad)
        self.sala = None
        self.acciones = 0            # acciones que consumen tiempo (2.12)
        self.derrotados = 0
        self.bonoAtaque = 0
        self.bonoDefensa = 0


class Enemigo(Actor):
    def __init__(self, instancia, tipoId, nombre, comportamiento,
                 vida, vidaMax, ataque, defensa, velocidad):
        Actor.__init__(self, vida, vidaMax, ataque, defensa, velocidad)
        self.instancia = instancia
        self.tipoId = tipoId
        self.nombre = nombre
        self.comportamiento = comportamiento
        self.sala = None
        self.activo = False

    def etiqueta(self):
        return "%s (%s)" % (self.nombre, self.instancia)


def claveInstancia(instancia):
    #Orden natural de ids de instancia: e-9 antes que e-10.
    pos = instancia.rfind("-")
    prefijo = instancia[:pos + 1]
    sufijo = instancia[pos + 1:]
    if sufijo.isdigit():
        return (prefijo, int(sufijo), instancia)
    return (instancia, -1, instancia)


def ordenarEnemigosPorInstancia(enemigos):
 #Inserción estable; las listas a activar son pequeñas. Devuelve una lista nueva.
    resultado = []
    for enemigo in enemigos:
        clave = claveInstancia(enemigo.instancia)
        i = len(resultado)
        while i > 0 and claveInstancia(resultado[i - 1].instancia) > clave:
            i -= 1
        resultado.insert(i, enemigo)
    return resultado