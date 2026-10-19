# Captura y restauración del estado de la partida.
#
# El guardado necesita convertir el modelo vivo en datos planos y volver de ellos sin repetir
# ninguna regla del motor. Aquí vive sólo ese traductor: el orden y los nombres de las claves son
# parte del formato, así que se escriben una vez y los usan tanto el adapter binario como las
# pruebas de ida y vuelta.
#
# Los dueños de los eventos (jugador, enemigo, puerta, trampa, efecto) se guardan como etiquetas
# cortas porque un archivo no puede contener referencias de memoria vivas.

from model.Constantes import (EV_JUGADOR, EV_ENEMIGO, EV_CIERRE_PUERTA, EV_REARME_TRAMPA)
from model.Agenda import Evento
from model.Bitacora import BitacoraCircular
from model.Entidades import ObjetoInstancia
from model.efectos import efectoActivo
from model.Salas import IndiceOrdenado

VERSION_FORMATO = 2


# ------------------------------------------------------------------ referencias
def _índice(modelo):
    """Índice ordenado id(objeto) -> etiqueta (IndiceOrdenado propio, sin dict)."""
    etiquetas = IndiceOrdenado()
    if modelo.jugador is not None:
        etiquetas.insertar(id(modelo.jugador), "j")
    for i in range(len(modelo.enemigosVivos)):
        etiquetas.insertar(id(modelo.enemigosVivos[i]), "e:%s" % modelo.enemigosVivos[i].instancia)
    activos = getattr(modelo.efectos, "activos", [])
    for i in range(len(activos)):
        etiquetas.insertar(id(activos[i]), "f:%d" % i)
    puertas = _listaPuertas(modelo)
    for i in range(len(puertas)):
        etiquetas.insertar(id(puertas[i]), "p:%d" % i)
    for i in range(modelo.salas.cantidad()):
        sala = modelo.salas.enPosicion(i)
        for trampa in sala.trampas:
            etiquetas.insertar(id(trampa), "t:%s" % trampa.instancia)
    return etiquetas


def _ladoCanonico(sala, salida):
    """Una puerta la comparten dos salidas; se guarda una sola vez, desde el lado de id menor.

    Si el otro lado no la comparte (esqueleto de un solo sentido), este lado es el único."""
    destino = salida.destino
    if destino is None or destino is sala or sala.id < destino.id:
        return True
    for otra in destino.salidas:
        if otra.puerta is salida.puerta:
            return False
    return True


def _listaPuertas(modelo):
    """Puertas en un orden fijo: salas por posición, salidas en su orden canónico."""
    puertas = []
    for i in range(modelo.salas.cantidad()):
        sala = modelo.salas.enPosicion(i)
        for salida in sala.salidas:
            if _ladoCanonico(sala, salida):
                puertas.append(salida.puerta)
    return puertas


def _etiqueta(etiquetas, objeto):
    etiqueta = etiquetas.buscar(id(objeto))
    if etiqueta is None:
        raise ValueError("El guardado no conoce cómo referenciar un objeto del modelo.")
    return etiqueta


# ------------------------------------------------------------------ captura
def _empacarAzar(azar):
    """getstate() devuelve tuplas anidadas; se planas para que quepan en cualquier formato."""
    version, interna, gauss = azar.getstate()
    return [version, list(interna), list(gauss) if gauss is not None else None]


def capturar(modelo):
    etiquetas = _índice(modelo)
    return {
        "versionFormato": VERSION_FORMATO,
        "semilla": modelo.semilla,
        "reloj": modelo.reloj,
        "estado": modelo.estado,
        "siguienteSerieObjeto": modelo.siguienteSerieObjeto,
        "puertaSalidaAbierta": modelo.puertaSalidaAbierta,
        "azar": _empacarAzar(modelo.azar),
        "bitacora": {"total": modelo.bitacora.total(), "mensajes": modelo.bitacora.ultimos()},
        "jugador": _capturarJugador(modelo),
        "inventario": _capturarInventario(modelo),
        "efectos": _capturarEfectos(modelo, etiquetas),
        "agenda": _capturarAgenda(modelo, etiquetas),
        "decision": _capturarDecision(modelo),
        "enemigos": _capturarEnemigos(modelo),
        "salas": _capturarSalas(modelo),
    }


def _capturarJugador(modelo):
    jugador = modelo.jugador
    return {"vida": jugador.vida, "vidaMax": jugador.vidaMax, "ataque": jugador.ataque,
            "defensa": jugador.defensa, "velocidad": jugador.velocidad,
            "tiempoSiguiente": jugador.tiempoSiguiente, "vivo": jugador.vivo,
            "sala": jugador.sala.id, "acciones": jugador.acciones,
            "derrotados": jugador.derrotados, "bonoAtaque": jugador.bonoAtaque,
            "bonoDefensa": jugador.bonoDefensa}


def _capturarInventario(modelo):
    inventario = modelo.inventario
    objetos = []
    cursor = -1
    arma = None
    armadura = None
    nodo = inventario.cabeza
    while nodo is not None:
        if nodo is inventario.cursor:
            cursor = len(objetos)
        if nodo is inventario.arma:
            arma = len(objetos)
        if nodo is inventario.armadura:
            armadura = len(objetos)
        objetos.append([nodo.objeto.tipoId, nodo.objeto.serie])
        nodo = nodo.sig
    return {"capacidad": inventario.capacidad, "objetos": objetos, "cursor": cursor,
            "arma": arma, "armadura": armadura}


def _capturarEfectos(modelo, etiquetas):
    activos = getattr(modelo.efectos, "activos", [])
    salida = []
    for efecto in activos:
        salida.append({"clase": efecto.clase, "actor": _etiqueta(etiquetas, efecto.actor),
                       "cantidad": efecto.cantidad, "fin": efecto.fin,
                       "velocidadAnterior": efecto.velocidadAnterior, "activo": efecto.activo})
    return salida


def _capturarAgenda(modelo, etiquetas):
    eventos = []
    for evento in modelo.agenda.pendientesValidos():
        eventos.append({"t": evento.tiempo, "seq": evento.seq, "tipo": evento.tipo,
                        "propietario": _etiqueta(etiquetas, evento.propietario)})
    return {"secuencia": modelo.agenda.secuencia(), "eventos": eventos}


def _capturarDecision(modelo):
    evento = modelo.eventoDecision
    if evento is None:
        return None
    return {"t": evento.tiempo, "seq": evento.seq}


def _capturarEnemigos(modelo):
    salida = []
    for enemigo in modelo.enemigosVivos:
        salida.append({"instancia": enemigo.instancia, "vida": enemigo.vida,
                       "activo": enemigo.activo, "velocidad": enemigo.velocidad,
                       "sala": enemigo.sala.id})
    return salida


def _capturarSalas(modelo):
    salas = []
    for i in range(modelo.salas.cantidad()):
        sala = modelo.salas.enPosicion(i)
        puertas = []
        for salida in sala.salidas:
            if _ladoCanonico(sala, salida):
                puertas.append([salida.direccion, salida.puerta.cerrada])
        trampas = []
        for trampa in sala.trampas:
            trampas.append([trampa.instancia, trampa.armada])
        objetos = []
        for objeto in sala.objetos:
            objetos.append([objeto.tipoId, objeto.serie])
        enemigos = []                      # el orden dentro de la sala define «atacar k»
        for enemigo in sala.enemigos:
            enemigos.append(enemigo.instancia)
        salas.append({"id": sala.id, "rastro": sala.rastro,
                      "contenido": sala.contenidoIncorporado, "objetos": objetos,
                      "trampas": trampas, "puertas": puertas, "enemigos": enemigos})
    return salas


# ------------------------------------------------------------------ restauración
def restaurar(modelo, datos):
    """Sobrescribe el estado vivo del modelo con lo capturado.

    Se llama sobre un modelo ya puesto en marcha (iniciarPartida construyó el esqueleto y el
    contenido de la sala inicial), de modo que las fichas y las entidades base vienen del mismo
    proveedor que validó las versiones al cargar.
    """
    if datos.get("versionFormato") != VERSION_FORMATO:
        raise ValueError("Formato de partida no soportado: %s" % datos.get("versionFormato"))

    _restaurarSalas(modelo, datos["salas"])
    modelo.siguienteSerieObjeto = datos["siguienteSerieObjeto"]
    _restaurarEnemigos(modelo, datos["enemigos"], datos["salas"])
    _restaurarJugador(modelo, datos["jugador"])
    _restaurarInventario(modelo, datos["inventario"])
    resolutor = _Resolutor(modelo)
    _restaurarEfectos(modelo, datos["efectos"], resolutor)
    _restaurarAgenda(modelo, datos["agenda"], resolutor)
    _restaurarDecision(modelo, datos["decision"])
    _restaurarBitacora(modelo, datos["bitacora"])

    modelo.azar.setstate((datos["azar"][0], tuple(datos["azar"][1]),
                          tuple(datos["azar"][2]) if datos["azar"][2] is not None else None))
    modelo.semilla = datos["semilla"]
    modelo.reloj = datos["reloj"]
    modelo.estado = datos["estado"]
    modelo.puertaSalidaAbierta = datos["puertaSalidaAbierta"]
    _vaciarDiario(modelo)


def _restaurarSalas(modelo, registros):
    for registro in registros:
        sala = modelo.salas.buscar(registro["id"])
        if sala is None:
            raise ValueError("La partida guardada menciona la sala inexistente %s." % registro["id"])
        if registro["contenido"] and not sala.contenidoIncorporado:
            modelo._asegurarContenido(sala)
        sala.rastro = registro["rastro"]
        sala.contenidoIncorporado = registro["contenido"]
        sala.objetos = [ObjetoInstancia(tipoId, serie) for tipoId, serie in registro["objetos"]]
        for instancia, armada in registro["trampas"]:
            for trampa in sala.trampas:
                if trampa.instancia == instancia:
                    trampa.armada = armada
        for direccion, cerrada in registro["puertas"]:
            salida = sala.salida(direccion)
            if salida is not None:
                salida.puerta.cerrada = cerrada


def _restaurarEnemigos(modelo, registros, registrosSalas):
    # Los enemigos deambuladores cambian de sala, así que la lista por sala se rehace entera.
    porInstancia = IndiceOrdenado()
    for i in range(modelo.salas.cantidad()):
        sala = modelo.salas.enPosicion(i)
        for enemigo in sala.enemigos:
            porInstancia.insertar(enemigo.instancia, enemigo)
        del sala.enemigos[:]
    del modelo.enemigosVivos[:]
    for registro in registros:
        enemigo = porInstancia.buscar(registro["instancia"])
        if enemigo is None:
            raise ValueError("La partida guardada menciona el enemigo inexistente %s."
                             % registro["instancia"])
        enemigo.vida = registro["vida"]
        enemigo.activo = registro["activo"]
        enemigo.velocidad = registro["velocidad"]
        enemigo.sala = modelo.salas.buscar(registro["sala"])
        enemigo.vivo = True
        enemigo.evento = None
        modelo.enemigosVivos.append(enemigo)
    # Orden de los enemigos dentro de cada sala, tal como estaba al guardar.
    for registro in registrosSalas:
        sala = modelo.salas.buscar(registro["id"])
        for instancia in registro["enemigos"]:
            enemigo = porInstancia.buscar(instancia)
            if enemigo is None:
                raise ValueError("La partida guardada menciona el enemigo inexistente %s." % instancia)
            sala.enemigos.append(enemigo)


def _restaurarJugador(modelo, datos):
    jugador = modelo.jugador
    jugador.vida = datos["vida"]
    jugador.vidaMax = datos["vidaMax"]
    jugador.ataque = datos["ataque"]
    jugador.defensa = datos["defensa"]
    jugador.velocidad = datos["velocidad"]
    jugador.tiempoSiguiente = datos["tiempoSiguiente"]
    jugador.vivo = datos["vivo"]
    jugador.acciones = datos["acciones"]
    jugador.derrotados = datos["derrotados"]
    jugador.bonoAtaque = datos["bonoAtaque"]
    jugador.bonoDefensa = datos["bonoDefensa"]
    jugador.sala = modelo.salas.buscar(datos["sala"])
    jugador.evento = None


def _restaurarInventario(modelo, datos):
    from model.Inventario import Nodo
    inventario = modelo.inventario
    inventario.capacidad = datos["capacidad"]
    inventario.cabeza = None
    inventario.cola = None
    inventario.cursor = None
    inventario.arma = None
    inventario.armadura = None
    inventario.tamano = 0
    nodos = []
    for tipoId, serie in datos["objetos"]:
        nodo = Nodo(ObjetoInstancia(tipoId, serie))
        inventario._enlazarDespues(nodo, inventario.cola)
        nodos.append(nodo)
    if datos["cursor"] >= 0:
        inventario.cursor = nodos[datos["cursor"]]
    if datos["arma"] is not None:
        inventario.arma = nodos[datos["arma"]]
    if datos["armadura"] is not None:
        inventario.armadura = nodos[datos["armadura"]]


def _restaurarEfectos(modelo, registros, resolutor):
    activos = []
    for registro in registros:
        efecto = efectoActivo(registro["clase"], resolutor.resolver(registro["actor"]),
                              registro["cantidad"], registro["fin"],
                              registro["velocidadAnterior"])
        efecto.activo = registro["activo"]
        activos.append(efecto)
    modelo.efectos.activos = activos


def _restaurarAgenda(modelo, datos, resolutor):
    eventos = []
    for registro in datos["eventos"]:
        evento = Evento(registro["t"], registro["tipo"], resolutor.resolver(registro["propietario"]))
        evento.seq = registro["seq"]
        eventos.append(evento)
    modelo.agenda.reconstruir(eventos, datos["secuencia"])
    _reenlazarEventos(modelo, eventos)


def _reenlazarEventos(modelo, eventos):
    """Devuelve las referencias de vuelta: cada dueño apunta a su evento pendiente."""
    for evento in eventos:
        propietario = evento.propietario
        tipo = evento.tipo
        if tipo == EV_JUGADOR:
            modelo.jugador.evento = evento
        elif tipo == EV_ENEMIGO:
            propietario.evento = evento
        elif tipo == EV_CIERRE_PUERTA:
            propietario.eventoCierre = evento
        elif tipo == EV_REARME_TRAMPA:
            propietario.eventoRearme = evento
        else:
            propietario.evento = evento       # los efectos de Jurnier guardan su evento propio


def _restaurarDecision(modelo, datos):
    if datos is None:
        modelo.eventoDecision = None
        return
    evento = Evento(datos["t"], EV_JUGADOR, modelo.jugador)
    evento.seq = datos["seq"]
    modelo.eventoDecision = evento
    modelo.jugador.evento = None


def _restaurarBitacora(modelo, datos):
    modelo.bitacora = BitacoraCircular(modelo.bitacora.capacidad())
    for mensaje in datos["mensajes"]:
        modelo.bitacora.agregar(mensaje)
    modelo.bitacora.reponerTotal(datos["total"])


def _vaciarDiario(modelo):
    """El historial de deshacer guarda closures sobre objetos que ya no existen."""
    intervalos = getattr(modelo.diario, "intervalos", None)
    if intervalos is not None:
        del intervalos[:]


class _Resolutor:
    """Convierte una etiqueta guardada en el objeto vivo del modelo (índices propios, sin dict)."""

    def __init__(self, modelo):
        self.modelo = modelo
        self.enemigos = IndiceOrdenado()
        for enemigo in modelo.enemigosVivos:
            self.enemigos.insertar(enemigo.instancia, enemigo)
        self.trampas = IndiceOrdenado()
        for i in range(modelo.salas.cantidad()):
            for trampa in modelo.salas.enPosicion(i).trampas:
                self.trampas.insertar(trampa.instancia, trampa)
        self.puertas = _listaPuertas(modelo)

    def resolver(self, etiqueta):
        if etiqueta == "j":
            return self.modelo.jugador
        clase, _, resto = etiqueta.partition(":")
        if clase == "e":
            enemigo = self.enemigos.buscar(resto)
            if enemigo is None:
                raise ValueError("La partida guardada menciona el enemigo inexistente %s." % resto)
            return enemigo
        if clase == "t":
            trampa = self.trampas.buscar(resto)
            if trampa is None:
                raise ValueError("La partida guardada menciona la trampa inexistente %s." % resto)
            return trampa
        if clase == "p":
            indice = int(resto)
            if indice >= len(self.puertas):
                raise ValueError("La partida guardada menciona la puerta %s." % etiqueta)
            return self.puertas[indice]
        if clase == "f":
            return self.modelo.efectos.activos[int(resto)]
        raise ValueError("Etiqueta de referencia desconocida: %s." % etiqueta)