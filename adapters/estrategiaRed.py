from adapters.clienteCripta import ClienteCripta
from model.Interfaces import PresupuestoAgotado
from model.Tabla import Conjunto
from model.cache_estructuras import CacheCatalogo, RegistroSalas
from model.ordenamiento.Selector import ordenar


class GestorRedPrecarga:
    def __init__(self, cliente: ClienteCripta, cacheCatalogo: CacheCatalogo):
        self.cliente = cliente
        self.cacheCatalogo = cacheCatalogo
        self.salasDescargadas = RegistroSalas()
        self.presupuestoMaximo = 0
        self.idCriptaActual = ""

    # Compatibilidad con atributos en snake_case
    @property
    def cache_catalogo(self):
        return self.cacheCatalogo

    @property
    def salas_descargadas(self):
        return self.salasDescargadas

    @property
    def presupuesto_maximo(self):
        return self.presupuestoMaximo

    @property
    def id_cripta_actual(self):
        return self.idCriptaActual

    def presupuestoRestante(self):
        """Solicitudes que faltan antes de exceder el máximo de la cripta; None si no aplica.

        No aplica en modo offline ni antes de conocer el presupuesto: la versión del catálogo y los
        datos generales se piden para saberlo y una lectura local nunca cuenta (sección 3.4)."""
        if not self.presupuestoMaximo or not self.cliente.cuentaComoRed():
            return None
        return self.presupuestoMaximo - self.cliente.obtenerSolicitudesRealizadas()

    def _reservar(self, cuantas: int):
        restante = self.presupuestoRestante()
        if restante is not None and cuantas > restante:
            raise PresupuestoAgotado("quedan %d de %d solicitudes y esta operación necesita %d"
                                     % (restante, self.presupuestoMaximo, cuantas))

    def _recortarPorPresupuesto(self, porDescargar):
        restante = self.presupuestoRestante()
        if restante is None or restante > 1:
            return porDescargar
        if restante <= 0:
            return []
        # Con una sola solicitud en la recámara se precarga nada más la sala del jugador: el lote
        # de catálogo que trae necesitaría viajes propios y excedería el máximo (sección 3.3).
        return porDescargar[:1]

    def inicializarCripta(self, idCripta: str) -> tuple:
        # Descarga datos generales, todo el esqueleto y precarga la sala inicial (sección 4.2 / sección 2.4)
        self.idCriptaActual = idCripta
        datosGen = self.cliente.obtenerDatosGenerales(idCripta)
        self.presupuestoMaximo = datosGen["presupuesto_solicitudes"]

        # Descargar todas las páginas del esqueleto para tener la lista completa de salas y sus salidas.
        # El mando lo tiene la respuesta: datosGen declara "paginas", pero si el servicio cambia el
        # tamaño de página quedarnos con el primero dejaría salas sin descubrir.
        esqueletoSalas = []
        pagina = 1
        totalPaginas = 1
        while pagina <= totalPaginas:
            self._reservar(1)
            respPag = self.cliente.obtenerEsqueleto(idCripta, pagina)
            for sala in respPag.get("salas", []):
                esqueletoSalas.append(sala)
            totalPaginas = max(totalPaginas, int(respPag.get("total_paginas", pagina)))
            pagina += 1

        # Precargar sala inicial y sus salas contiguas antes del instante 0 (sección 2.4)
        salaInicial = datosGen["sala_inicial"]
        self.precargarVecindad(salaInicial, esqueletoSalas)

        return datosGen, esqueletoSalas

    def asegurarContenidoSala(self, idSala: int, esqueletoSalas: list) -> dict:
        # Garantiza que la sala destino esté en memoria antes de entrar (sección 2.5 / sección 4.2)
        contenido = self.salasDescargadas.obtener(idSala)
        if contenido is None:
            self.precargarVecindad(idSala, esqueletoSalas)
            contenido = self.salasDescargadas.obtener(idSala)
        if contenido is None:
            # La precarga se recorta con el presupuesto y la sala pudo quedarse fuera del lote.
            # Entrar sin contenido no es una opción, así que se pide sola; si ni siquiera cabe una
            # solicitud, PresupuestoAgotado sube al modelo y la acción se rechaza con mensaje.
            self._descargarLoteSalasYCatalogo([idSala])
            contenido = self.salasDescargadas.obtener(idSala)
        return contenido

    def precargarVecindad(self, idSalaOrigen: int, esqueletoSalas: list):
        # Cola FIFO para recolectar hasta 10 salas cercanas no descargadas (sección 4.2)
        porDescargar = []
        colaPendientes = [idSalaOrigen]
        indiceFrente = 0
        registradasEnCola = [idSalaOrigen]

        while indiceFrente < len(colaPendientes) and len(porDescargar) < 10:
            salaActual = colaPendientes[indiceFrente]
            indiceFrente += 1

            if not self.salasDescargadas.contiene(salaActual):
                porDescargar.append(salaActual)
                if len(porDescargar) == 10:
                    break

            # Buscar las salidas contiguas en orden canónico (N, S, E, O)
            salasContiguas = self._obtenerSalasContiguas(salaActual, esqueletoSalas)
            for idContigua in salasContiguas:
                if idContigua not in registradasEnCola:
                    registradasEnCola.append(idContigua)
                    colaPendientes.append(idContigua)

        porDescargar = self._recortarPorPresupuesto(porDescargar)
        if len(porDescargar) == 0:
            return
        try:
            self._descargarLoteSalasYCatalogo(porDescargar)
        except PresupuestoAgotado:
            # Precargar es una cortesía: quedarse corto solo cuesta un viaje cuando el jugador entra.
            pass

    def _obtenerSalasContiguas(self, idSala: int, esqueletoSalas: list) -> list:
        contiguas = []
        for s in esqueletoSalas:
            if s["id"] == idSala:
                salidas = s.get("salidas", {})
                for direccion in ["N", "S", "E", "O"]:
                    if direccion in salidas:
                        contiguas.append(salidas[direccion]["sala"])
                break
        return contiguas

    def _descargarLoteSalasYCatalogo(self, loteSalas: list):
        # Descarga salas en lotes de máximo 10 (sección 3.4)
        for i in range(0, len(loteSalas), 10):
            subLoteSalas = loteSalas[i : i + 10]
            self._reservar(1)
            respuesta = self.cliente.obtenerContenidoLote(self.idCriptaActual, subLoteSalas)
            idsCatalogo = []

            for infoSala in respuesta.get("contenido", []):
                self.salasDescargadas.guardar(infoSala["sala"], infoSala)
                for enem in infoSala.get("enemigos", []):
                    idsCatalogo.append(enem["tipo"])
                idsCatalogo.extend(infoSala.get("objetos", []))
                for trampa in infoSala.get("trampas", []):
                    idsCatalogo.append(trampa["tipo"])

            self.asegurarCatalogo(idsCatalogo)

    def asegurarCatalogo(self, idsFichas: list):
        """Pide en lotes de 10 solo las fichas que faltan en RAM y en disco."""
        vistos = Conjunto()
        pendientes = []
        for idFicha in idsFichas:
            if vistos.contiene(idFicha):
                continue
            vistos.agregar(idFicha)
            # registrar_metrica=False: la precarga no debe contar como acierto del jugador (5.1)
            if not self.cacheCatalogo.contiene(idFicha, registrar_metrica=False):
                pendientes.append(idFicha)
        if not pendientes:
            return
        # Orden determinista (sección 4.2 / 4.11) para que el replay sea reproducible.
        # Es el ordenamiento del proyecto, no sorted(): misma sección 4.9 y su selector.
        pendientes = ordenar(pendientes)
        for i in range(0, len(pendientes), 10):
            self._reservar(1)
            respuesta = self.cliente.obtenerCatalogoLote(pendientes[i : i + 10])
            for ficha in respuesta.get("entidades", []):
                self.cacheCatalogo.insertar(ficha["id"], ficha)

    def generarReporteRendimientoRed(self) -> str:
        """Regla 5.1: Reporta solicitudes realizadas, presupuesto, aciertos y fallos de caché."""
        realizadas = self.cliente.obtenerSolicitudesRealizadas()
        restante = self.presupuestoRestante()
        if restante is None:
            estado = "sin límite: las lecturas locales no cuentan como red (sección 3.4)"
        else:
            estado = "%s, quedan %d" % ("CUMPLIDO" if realizadas <= self.presupuestoMaximo
                                        else "EXCEDIDO", max(0, restante))
        return (
            f"=== REPORTE DE RED Y CACHÉ (sección 5.1) ===\n"
            f"Solicitudes HTTP realizadas : {realizadas} / {self.presupuestoMaximo}\n"
            f"Estado del presupuesto      : {estado}\n"
            f"Aciertos de caché (RAM)     : {self.cacheCatalogo.aciertos}\n"
            f"Fallos de caché (RAM)       : {self.cacheCatalogo.fallos}\n"
            f"Fichas desalojadas          : {self.cacheCatalogo.desalojos}\n"
            f"Salas registradas           : {self.salasDescargadas.cantidad}\n"
            f"====================================="
        )

    # Alias en snake_case
    inicializar_cripta = inicializarCripta
    asegurar_contenido_sala = asegurarContenidoSala
    precargar_vecindad = precargarVecindad
    _obtener_salas_contiguas = _obtenerSalasContiguas
    _descargar_lote_salas_y_catalogo = _descargarLoteSalasYCatalogo
    asegurar_catalogo = asegurarCatalogo
    presupuesto_restante = presupuestoRestante
    generar_reporte_rendimiento_red = generarReporteRendimientoRed