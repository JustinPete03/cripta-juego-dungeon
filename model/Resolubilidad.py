# Verificación de resolubilidad (§3.5, §5.4).
# Cumple con el Principio I de la Constitución: implementado con Tabla propia sin dict ni set.

from model.Tabla import Tabla
from model.Salas import IndiceOrdenado
from model.Constantes import DIRECCIONES
from model.ordenamiento.Selector import ordenar


class ResultadoResolubilidad:
    def __init__(self, resoluble, ordenLlaves=None, llavesInalcanzables=None,
                 fronteraBloqueada=None, ciclo=None):
        self.resoluble = resoluble
        self.ordenLlaves = ordenLlaves or []
        self.llavesInalcanzables = llavesInalcanzables or []
        self.fronteraBloqueada = fronteraBloqueada or []  # lista de dicts
        self.ciclo = ciclo  # lista de IDs de llaves formando el ciclo o None

    def reporte(self):
        lineas = []
        if self.resoluble:
            lineas.append("=== REPORTE DE RESOLUBILIDAD: RESOLUBLE ===")
            lineas.append("La cripta puede ganarse con éxito.")
            lineas.append("Orden determinista de obtención de llaves (%d):" % len(self.ordenLlaves))
            for i, k in enumerate(self.ordenLlaves, 1):
                lineas.append("  %d) %s" % (i, k))
        else:
            lineas.append("=== REPORTE DE RESOLUBILIDAD: NO RESOLUBLE ===")
            lineas.append("La cripta NO puede ganarse bajo los supuestos de las reglas.")
            lineas.append("\nLlaves inalcanzables (%d):" % len(self.llavesInalcanzables))
            for k in self.llavesInalcanzables:
                lineas.append("  - %s" % k)

            lineas.append("\nFrontera bloqueada (%d puertas adyacentes):" % len(self.fronteraBloqueada))
            for item in self.fronteraBloqueada:
                ub = item.get("ubicacion", "desconocida")
                lineas.append("  * Puerta Sala %s -> Sala %s requiere '%s' (Ubicación: %s)" %
                              (item["origen"], item["destino"], item["llave"], ub))

            if self.ciclo:
                lineas.append("\nCiclo de dependencia detectado:")
                cadenaCiclo = " -> ".join(self.ciclo)
                lineas.append("  [ %s ]" % cadenaCiclo)
                lineas.append("  (La llave está ubicada detrás de puertas que requieren la misma llave)")

        return "\n".join(lineas)


def verificarResolubilidad(datosGenerales, esqueleto, listaLlaves):
    """Determina si la cripta puede ganarse bajo los supuestos de §3.5.
    
    Algoritmo incremental O(V + E + K) utilizando Tabla propia.
    """
    salaInicialId = datosGenerales["sala_inicial"]
    salaSalidaId = datosGenerales["sala_salida"]
    llaveSalida = datosGenerales["llave_salida"]

    # 1. Indexar esqueleto por ID de sala
    salasIndice = IndiceOrdenado()
    idsSalas = []
    for datosSala in esqueleto:
        sId = datosSala["id"]
        idsSalas.append(sId)
        salidasFormateadas = []
        salidas = datosSala.get("salidas", {})
        for d in DIRECCIONES:
            if d in salidas:
                info = salidas[d]
                salidasFormateadas.append({
                    "direccion": d,
                    "destinoId": info["sala"],
                    "cerrada": bool(info.get("cerrada", False)),
                    "llave": info.get("llave")
                })
        salasIndice.insertar(sId, {
            "id": sId,
            "nombre": datosSala.get("nombre", "Sala %s" % sId),
            "salidas": salidasFormateadas
        })

    # Sincronización bidireccional de puertas (§2.1)
    for sId in idsSalas:
        infoU = salasIndice.buscar(sId)
        if not infoU:
            continue
        for sal in infoU["salidas"]:
            if sal["cerrada"]:
                vId = sal["destinoId"]
                infoV = salasIndice.buscar(vId)
                if infoV:
                    for salV in infoV["salidas"]:
                        if salV["destinoId"] == sId:
                            salV["cerrada"] = True
                            if sal["llave"] and not salV.get("llave"):
                                salV["llave"] = sal["llave"]

    # 2. Indexar ubicación de llaves de forma ordenada
    llavesPorSala = Tabla()
    infoLlave = Tabla()
    todasLasLlaves = []

    listaLlavesOrdenada = ordenar(listaLlaves, clave=lambda k: k["id"])
    for regLlave in listaLlavesOrdenada:
        kId = regLlave["id"]
        todasLasLlaves.append(kId)
        infoLlave.guardar(kId, regLlave)
        sId = regLlave["sala"]
        enSala = llavesPorSala.obtener(sId, [])
        enSala.append(regLlave)
        llavesPorSala.guardar(sId, enSala)

    # 3. Estructuras de recorrido incremental
    alcanzadas = Tabla()
    llavesObtenidas = Tabla()
    ordenObtencion = []
    puertasEsperandoLlave = Tabla()  # idLlave -> list of (uId, vId)
    fronteraTotal = []

    cola = [salaInicialId]
    cabeza = 0

    while cabeza < len(cola):
        uId = cola[cabeza]
        cabeza += 1

        if alcanzadas.contiene(uId):
            continue
        alcanzadas.guardar(uId, True)

        # Recoger llaves disponibles en uId
        llavesEnU = llavesPorSala.obtener(uId, [])
        for reg in llavesEnU:
            kId = reg["id"]
            if not llavesObtenidas.contiene(kId):
                llavesObtenidas.guardar(kId, True)
                ordenObtencion.append(kId)
                # Despertar puertas bloqueadas por esta llave
                esperando = puertasEsperandoLlave.obtener(kId, [])
                for origenId, destinoId in esperando:
                    if not alcanzadas.contiene(destinoId):
                        cola.append(destinoId)

        # Explorar salidas
        infoU = salasIndice.buscar(uId)
        if infoU is None:
            continue

        for salida in infoU["salidas"]:
            vId = salida["destinoId"]
            cerrada = salida["cerrada"]
            reqLlave = salida["llave"]

            if cerrada:
                if reqLlave is not None:
                    if llavesObtenidas.contiene(reqLlave):
                        # Llave ya en posesión: puerta accesible
                        if not alcanzadas.contiene(vId):
                            cola.append(vId)
                    else:
                        # Puerta bloqueada esperando llave
                        esperando = puertasEsperandoLlave.obtener(reqLlave, [])
                        esperando.append((uId, vId))
                        puertasEsperandoLlave.guardar(reqLlave, esperando)
                        fronteraTotal.append((uId, vId, reqLlave))
                else:
                    # Cerrada sin llave asignada: infranqueable
                    pass
            else:
                # Salida abierta
                if not alcanzadas.contiene(vId):
                    cola.append(vId)

    # 4. Comprobar resolubilidad (§3.5, FR-028)
    # Debe poder obtener llave_salida y llegar a sala_salida
    tieneLlaveSalida = llavesObtenidas.contiene(llaveSalida)
    llegaASalida = alcanzadas.contiene(salaSalidaId)

    # Verificar si la puerta hacia salaSalidaId requiere llave_salida (FR-028)
    puertaSalidaValida = False
    infoSalida = salasIndice.buscar(salaSalidaId)
    if infoSalida:
        salidasSalida = infoSalida["salidas"]
        hayPuertasConLlave = any(s.get("llave") == llaveSalida for s in salidasSalida)
        if hayPuertasConLlave:
            # Al menos un acceso con llaveSalida debe haber sido desbloqueado
            for s in salidasSalida:
                vecina = s["destinoId"]
                if s.get("llave") == llaveSalida and alcanzadas.contiene(vecina) and tieneLlaveSalida:
                    puertaSalidaValida = True
                    break
        else:
            # Si no hay puerta que requiera llave_salida, basta alcanzarla si tiene la llave
            puertaSalidaValida = llegaASalida
    else:
        puertaSalidaValida = False

    resoluble = tieneLlaveSalida and llegaASalida and puertaSalidaValida

    if resoluble:
        return ResultadoResolubilidad(True, ordenLlaves=ordenObtencion)

    # 5. Generar reporte de no resolubilidad
    llavesInalcanzables = []
    for kId in todasLasLlaves:
        if not llavesObtenidas.contiene(kId):
            llavesInalcanzables.append(kId)
    if not llavesObtenidas.contiene(llaveSalida) and llaveSalida not in llavesInalcanzables:
        llavesInalcanzables.append(llaveSalida)

    fronteraBloqueada = []
    for uId, vId, reqLlave in fronteraTotal:
        if alcanzadas.contiene(uId) and not alcanzadas.contiene(vId):
            regL = infoLlave.obtener(reqLlave)
            if regL:
                if "enemigo" in regL:
                    ub = "Sala %s (enemigo %s)" % (regL["sala"], regL["enemigo"])
                else:
                    ub = "Sala %s" % regL["sala"]
            else:
                ub = "Desconocida / ausente"
            fronteraBloqueada.append({
                "origen": uId,
                "destino": vId,
                "llave": reqLlave,
                "ubicacion": ub
            })

    # 6. Detección determinista de ciclos de dependencias
    # Mapeo de dependencias directas: kId -> list of keys that block access to kId
    prerrequisitos = Tabla()

    for item in fronteraBloqueada:
        kReq = item["llave"]
        destInicial = item["destino"]

        visitadosSub = Tabla()
        colaSub = [(destInicial, kReq)]
        cabezaSub = 0

        while cabezaSub < len(colaSub):
            currId, gatingKey = colaSub[cabezaSub]
            cabezaSub += 1

            if visitadosSub.contiene(currId) or alcanzadas.contiene(currId):
                continue
            visitadosSub.guardar(currId, True)

            # Las llaves en currId dependen directamente de gatingKey
            for reg in llavesPorSala.obtener(currId, []):
                kDest = reg["id"]
                if not llavesObtenidas.contiene(kDest):
                    listaP = prerrequisitos.obtener(kDest, [])
                    if gatingKey not in listaP:
                        listaP.append(gatingKey)
                    prerrequisitos.guardar(kDest, listaP)

            # Seguir explorando salidas en la región no alcanzada
            infoCurr = salasIndice.buscar(currId)
            if not infoCurr:
                continue

            for sal in infoCurr["salidas"]:
                sigId = sal["destinoId"]
                if alcanzadas.contiene(sigId) or visitadosSub.contiene(sigId):
                    continue
                if sal["cerrada"]:
                    req = sal["llave"]
                    if req and not llavesObtenidas.contiene(req):
                        colaSub.append((sigId, req))
                    elif not sal["cerrada"] or (req and llavesObtenidas.contiene(req)):
                        colaSub.append((sigId, gatingKey))
                else:
                    colaSub.append((sigId, gatingKey))

    # Buscar ciclos en el grafo de prerrequisitos
    cicloDetectado = None

    def _buscarCiclo(actual, camino):
        prereqs = prerrequisitos.obtener(actual, [])
        for p in prereqs:
            if p == actual:
                return [actual, actual]
            if p in camino:
                idx = camino.index(p)
                return camino[idx:] + [p]
            res = _buscarCiclo(p, camino + [p])
            if res:
                return res
        return None

    for kId in llavesInalcanzables:
        ciclo = _buscarCiclo(kId, [kId])
        if ciclo:
            cicloDetectado = ciclo
            break

    return ResultadoResolubilidad(
        False,
        llavesInalcanzables=llavesInalcanzables,
        fronteraBloqueada=fronteraBloqueada,
        ciclo=cicloDetectado
    )
