# Presentación: convierte el estado del modelo en datos listos para dibujar.
#
# No importa pygame ni dibuja nada: así las escenas gráficas y las pruebas leen la misma
# información, y el modelo sigue sin saber que existe una ventana.

from model.Constantes import EN_CURSO, VICTORIA, DERROTA

# Arte genérico por clase de objeto (el contrato 2.7 define las clases, no los ids de una cripta).
SPRITES_POR_CLASE = (
    ("arma", "daga"),
    ("armadura", "armadura"),
    ("pocion", "pocion"),
    ("antidoto", "antidoto"),
    ("llave", "llave"),
    ("antorcha", "antorcha"),
    ("pergamino_retroceso", "pergamino"),
    ("trampa", "trampa"),
    ("enemigo", "rata"),
)

# Pistas de dibujo por palabra del nombre; si nada coincide, se usa el comportamiento (sección 2.8).
SPRITES_POR_NOMBRE = (
    ("rata", "rata"),
    ("roedor", "rata"),
    ("esqueleto", "esqueleto"),
    ("guardian", "esqueleto"),
    ("murcielago", "murcielago"),
    ("murciélago", "murcielago"),
    ("bat", "murcielago"),
    ("bich", "murcielago"),
)

SPRITES_POR_COMPORTAMIENTO = (
    ("guardian", "esqueleto"),
    ("guardián", "esqueleto"),
    ("errante", "murcielago"),
    ("rastreador", "rata"),
)

DESLICES = (("N", 0, -1), ("S", 0, 1), ("E", 1, 0), ("O", -1, 0))


class FichaVisual:
    def __init__(self, tipoId, nombre, clase, sprite, detalle, peso, valor, resumen=""):
        self.tipoId = tipoId
        self.nombre = nombre
        self.clase = clase
        self.sprite = sprite
        self.detalle = detalle
        self.peso = peso
        self.valor = valor
        self.resumen = resumen


class SueloVisual:
    """Objeto en el suelo de la sala, con el índice que espera ACC_RECOGER."""

    def __init__(self, indice, ficha):
        self.indice = indice
        self.ficha = ficha


class EnemigoVisual:
    """Enemigo con el índice que espera ACC_ATACAR sobre sala.enemigos."""

    def __init__(self, indice, etiqueta, nombre, vida, vidaMax, sprite, comportamiento, activo):
        self.indice = indice
        self.etiqueta = etiqueta
        self.nombre = nombre
        self.vida = vida
        self.vidaMax = vidaMax
        self.sprite = sprite
        self.comportamiento = comportamiento
        self.activo = activo


class SalidaVisual:
    def __init__(self, direccion, destinoId, cerrada, necesitaLlave, tieneLlave, cierreAutomatico,
                 esSalida):
        self.direccion = direccion
        self.destinoId = destinoId
        self.cerrada = cerrada
        self.necesitaLlave = necesitaLlave
        self.tieneLlave = tieneLlave
        self.cierreAutomatico = cierreAutomatico
        self.esSalida = esSalida

    @property
    def transitable(self):
        return not self.cerrada

    @property
    def sePuedeAbrir(self):
        return self.cerrada and (not self.necesitaLlave or self.tieneLlave)


class TrampaVisual:
    def __init__(self, ficha, armada):
        self.ficha = ficha
        self.armada = armada


class SalaVisual:
    def __init__(self, idSala, nombre, reloj, esSalida, salidas, enemigos, suelo, trampas):
        self.id = idSala
        self.nombre = nombre
        self.reloj = reloj
        self.esSalida = esSalida
        self.salidas = salidas
        self.enemigos = enemigos
        self.suelo = suelo
        self.trampas = trampas

    @property
    def enCombate(self):
        for enemigo in self.enemigos:
            if enemigo.activo:
                return True
        return False


class JugadorVisual:
    def __init__(self, nombre, vida, vidaMax, ataque, bonoAtaque, defensa, bonoDefensa,
                 velocidad, acciones, derrotados, efectos):
        self.nombre = nombre
        self.vida = vida
        self.vidaMax = vidaMax
        self.ataque = ataque
        self.bonoAtaque = bonoAtaque
        self.defensa = defensa
        self.bonoDefensa = bonoDefensa
        self.velocidad = velocidad
        self.acciones = acciones
        self.derrotados = derrotados
        self.efectos = efectos

    @property
    def ataqueTotal(self):
        return self.ataque + self.bonoAtaque

    @property
    def defensaTotal(self):
        return self.defensa + self.bonoDefensa


class BolsilloVisual:
    def __init__(self, indice, ficha, cursor, equipado, real):
        self.indice = indice
        self.ficha = ficha
        self.esCursor = cursor
        self.equipado = equipado
        self.real = real


class InventarioVisual:
    def __init__(self, bolsillos, cursor, tamano, capacidad, arma, armadura, cursorVista=-1):
        self.bolsillos = bolsillos
        self.cursor = cursor
        self.tamano = tamano
        self.capacidad = capacidad
        self.arma = arma
        self.armadura = armadura
        self.cursorVista = cursorVista

    @property
    def vacio(self):
        return self.tamano == 0

    @property
    def lleno(self):
        return self.tamano >= self.capacidad


class CeldaVisual:
    def __init__(self, x, y, idSala, nombre, visitada, actual, esSalida, cerrada):
        self.x = x
        self.y = y
        self.idSala = idSala
        self.nombre = nombre
        self.visitada = visitada
        self.actual = actual
        self.esSalida = esSalida
        self.cerrada = cerrada


class ResultadoVisual:
    def __init__(self, titulo, gano, acciones, derrotados, tiempoFinal):
        self.titulo = titulo
        self.gano = gano
        self.acciones = acciones
        self.derrotados = derrotados
        self.tiempoFinal = tiempoFinal


class Instantanea:
    def __init__(self, jugador, sala, inventario, mensajes, totalMensajes, estado,
                 pergaminos, celdas, puedeRetroceder):
        self.jugador = jugador
        self.sala = sala
        self.inventario = inventario
        self.mensajes = mensajes
        self.totalMensajes = totalMensajes
        self.estado = estado
        self.pergaminos = pergaminos
        self.celdas = celdas
        self.puedeRetroceder = puedeRetroceder

    @property
    def terminada(self):
        return self.estado != EN_CURSO


def buscar(indice, clave):
    """Búsqueda lineal sobre una lista de pares; suficiente para listas de tamaño de pantalla."""
    for par in indice:
        if par[0] == clave:
            return par[1]
    return None


def fichaDel(modelo, tipoId):
    try:
        return modelo.proveedor.ficha(tipoId)
    except Exception:
        return {"id": tipoId, "nombre": tipoId, "clase": ""}


def spriteDeObjeto(ficha):
    return buscar(SPRITES_POR_CLASE, ficha.get("clase", "")) or "daga"


def spriteDeEnemigo(ficha, nombre, comportamiento):
    texto = nombre.lower()
    for palabra, sprite in SPRITES_POR_NOMBRE:
        if palabra in texto:
            return sprite
    texto = texto + " " + str(comportamiento).lower()
    for palabra, sprite in SPRITES_POR_COMPORTAMIENTO:
        if texto.find(palabra) >= 0:
            return sprite
    return buscar(SPRITES_POR_COMPORTAMIENTO, str(comportamiento).lower()) or "rata"


def detalleDe(ficha):
    partes = []
    clase = ficha.get("clase", "")
    if clase:
        partes.append(clase)
    claves = (("ataque_bonus", "ataque +"), ("defensa_bonus", "defensa +"), ("cura", "cura"),
              ("modificador_velocidad", "velocidad"), ("duracion", "duración"),
              ("vida_max", "vida"), ("ataque", "ataque"), ("defensa", "defensa"),
              ("velocidad", "velocidad"), ("daño", "daño"),
              ("rearme", "rearme"), ("peso", "peso"), ("valor", "valor"))
    for clave, etiqueta in claves:
        if clave in ficha and ficha[clave] is not None:
            partes.append("%s %s" % (etiqueta, ficha[clave]))
    suelta = ficha.get("suelta")
    if suelta:
        partes.append("suelta %d" % len(suelta))
    return " · ".join(partes)


# El resumen muestra el único dato que decide si el objeto merece un hueco de la bolsa.
RESUMEN_POR_CAMPO = (("ataque_bonus", "ATA +%d"), ("defensa_bonus", "DEF +%d"), ("cura", "VIDA +%d"),
                     ("modificador_velocidad", "VEL +%d"), ("duracion", "DUR %d"),
                     ("daño", "DAÑO %d"), ("dano", "DAÑO %d"), ("vida_max", "VIDA %d"))
RESUMEN_POR_CLASE = {"llave": "LLAVE", "pergamino_retroceso": "RETROCEDER",
                     "antidoto": "QUITAMIELO", "trampa": "PINCHA"}


def resumenDe(ficha):
    clase = ficha.get("clase", "")
    if clase in RESUMEN_POR_CLASE:
        abre = ficha.get("abre") if clase == "llave" else None
        return RESUMEN_POR_CLASE[clase] if not abre else "ABRE %s" % str(abre).upper()
    for clave, formato in RESUMEN_POR_CAMPO:
        valor = ficha.get(clave)
        if isinstance(valor, (int, float)) and valor:
            return formato % valor
    return clase.upper() if clase else ""


def fichaVisual(modelo, tipoId):
    ficha = fichaDel(modelo, tipoId)
    return FichaVisual(tipoId, ficha.get("nombre", tipoId), ficha.get("clase", ""),
                       spriteDeObjeto(ficha), detalleDe(ficha),
                       ficha.get("peso", 0), ficha.get("valor", 0), resumenDe(ficha))


def efectosDelJugador(modelo):
    # El contrato declara descripcionjugador; la vista de consola usa descripcionJugador.
    describe = modelo.efectos.descripcionjugador(modelo)
    return list(describe) if describe else []


def instantaneaDelJugador(modelo):
    jugador = modelo.jugador
    return JugadorVisual("Explorador", jugador.vida, jugador.vidaMax, jugador.ataque,
                         jugador.bonoAtaque, jugador.defensa, jugador.bonoDefensa,
                         jugador.velocidad, jugador.acciones, jugador.derrotados,
                         efectosDelJugador(modelo))


def instantaneaDeSalidas(modelo, sala):
    salidas = []
    for salida in sala.salidas:
        llave = salida.puerta.llave
        necesitaLlave = llave is not None
        tieneLlave = False
        if necesitaLlave:
            try:
                tieneLlave = modelo.inventario.tieneLlave(llave)
            except Exception:
                tieneLlave = False
        salidas.append(SalidaVisual(salida.direccion, salida.destinoId, salida.puerta.cerrada,
                                    necesitaLlave, tieneLlave, salida.puerta.cierreAutomatico,
                                    salida.destinoId == modelo.salaSalidaId))
    return salidas


def instantaneaDeSala(modelo):
    sala = modelo.jugador.sala
    enemigos = []
    for i in range(len(sala.enemigos)):
        enemigo = sala.enemigos[i]
        ficha = fichaDel(modelo, enemigo.tipoId)
        enemigos.append(EnemigoVisual(i, enemigo.etiqueta(), enemigo.nombre, enemigo.vida,
                                      enemigo.vidaMax,
                                      spriteDeEnemigo(ficha, enemigo.nombre, enemigo.comportamiento),
                                      enemigo.comportamiento, enemigo.activo))
    suelo = []
    for i in range(len(sala.objetos)):
        suelo.append(SueloVisual(i, fichaVisual(modelo, sala.objetos[i].tipoId)))
    trampas = []
    for trampa in sala.trampas:
        trampas.append(TrampaVisual(fichaVisual(modelo, trampa.tipoId), trampa.armada))
    return SalaVisual(sala.id, sala.nombre, modelo.reloj, sala.id == modelo.salaSalidaId,
                      instantaneaDeSalidas(modelo, sala), enemigos, suelo, trampas)


def instantaneaDelInventario(modelo, criterio=None):
    inventario = modelo.inventario
    actual = inventario.actual()
    cursor = -1
    bolsillos = []
    reales = inventario.objetos()
    series = []
    for objeto in reales:
        series.append(objeto.serie)
    objetos = reales
    if criterio in ("peso", "valor", "nombre"):
        objetos = inventario.vistaOrdenada(criterio)
    cursorVista = -1
    for i in range(len(objetos)):
        serie = objetos[i].serie
        real = series.index(serie)
        esCursor = actual is not None and serie == actual.serie
        if esCursor:
            cursor = real
            cursorVista = i
        equipado = ""
        if inventario.arma is not None and inventario.arma.objeto.serie == serie:
            equipado = "arma"
        elif inventario.armadura is not None and inventario.armadura.objeto.serie == serie:
            equipado = "armadura"
        bolsillos.append(BolsilloVisual(i, fichaVisual(modelo, objetos[i].tipoId), esCursor,
                                        equipado, real))
    arma = None
    if inventario.arma is not None:
        arma = fichaVisual(modelo, inventario.arma.objeto.tipoId).nombre
    armadura = None
    if inventario.armadura is not None:
        armadura = fichaVisual(modelo, inventario.armadura.objeto.tipoId).nombre
    return InventarioVisual(bolsillos, cursor, inventario.tamano, inventario.capacidad,
                            arma, armadura, cursorVista)


def contarPergaminos(modelo):
    inventario = modelo.inventario
    total = 0
    nodo = inventario.cabeza
    while nodo is not None:
        if fichaDel(modelo, nodo.objeto.tipoId).get("clase") == "pergamino_retroceso":
            total += 1
        nodo = nodo.sig
    return total


def celdasDelMapa(modelo):
    """Minimapa: despliega el esqueleto en una rejilla siguiendo N/S/E/O desde la sala inicial.

    Solo usa el esqueleto ya cargado en el modelo; no inventa posiciones dentro de una sala.
    """
    colocadas = []
    pendientes = [(0, 0, modelo.jugador.sala)]
    puestos = [(0, 0, modelo.jugador.sala.id)]
    tope = modelo.salas.cantidad() * 4 + 16
    while len(pendientes) > 0 and len(colocadas) < tope:
        x, y, sala = pendientes.pop(0)
        colocadas.append((x, y, sala))
        for direccion, dx, dy in DESLICES:
            salida = sala.salida(direccion)
            if salida is None:
                continue
            destino = salida.destino
            if destino is None:
                continue
            yaPuesto = False
            for px, py, pid in puestos:
                if pid == destino.id:
                    yaPuesto = True
                    break
            if yaPuesto:
                continue
            puestos.append((x + dx, y + dy, destino.id))
            pendientes.append((x + dx, y + dy, destino))
    celdas = []
    actual = modelo.jugador.sala.id
    for x, y, sala in colocadas:
        cerrada = False
        for salida in sala.salidas:
            if salida.puerta.cerrada:
                cerrada = True
        celdas.append(CeldaVisual(x, y, sala.id, sala.nombre, sala.rastro >= 0,
                                  sala.id == actual, sala.id == modelo.salaSalidaId, cerrada))
    return celdas


def mensajeNuevo(modelo, anterior):
    """Mensajes añadidos a la bitácora desde la última lectura, del más antiguo al más nuevo."""
    total = modelo.bitacora.total()
    mensajes = modelo.bitacora.ultimos()
    if anterior is None:
        return list(mensajes), total
    nuevos = total - anterior
    if nuevos <= 0:
        return [], total
    if nuevos > len(mensajes):
        nuevos = len(mensajes)
    return mensajes[len(mensajes) - nuevos:], total


def instantanea(modelo, criterio=None, totalAnterior=None):
    mensajes, total = mensajeNuevo(modelo, totalAnterior)
    return Instantanea(instantaneaDelJugador(modelo), instantaneaDeSala(modelo),
                       instantaneaDelInventario(modelo, criterio), mensajes, total,
                       modelo.estado, contarPergaminos(modelo), celdasDelMapa(modelo),
                       puedeRetroceder(modelo))


def puedeRetroceder(modelo):
    diario = getattr(modelo, "diario", None)
    if diario is None or not getattr(diario, "activo", False):
        return False
    return len(getattr(diario, "intervalos", [])) > 0


def resultadoVisual(modelo):
    resultado = modelo.resultadoPartida()
    gano = resultado.estado == VICTORIA
    titulo = "VICTORIA" if gano else "DERROTA"
    if resultado.estado == DERROTA:
        titulo = "DERROTA"
    return ResultadoVisual(titulo, gano, resultado.acciones, resultado.derrotados,
                           resultado.tiempoFinal)
