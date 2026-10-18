from adapters.clienteCripta import ClienteCripta
from model.cache_estructuras import CacheCatalogo, RegistroSalas


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

    def inicializarCripta(self, idCripta: str) -> tuple:
        # Descarga datos generales, todo el esqueleto y precarga la sala inicial (§4.2 / §2.4)
        self.idCriptaActual = idCripta
        datosGen = self.cliente.obtenerDatosGenerales(idCripta)
        self.presupuestoMaximo = datosGen["presupuesto_solicitudes"]

        # Descargar todas las páginas del esqueleto para tener la lista completa de salas y sus salidas
        totalPaginas = datosGen.get("paginas", datosGen.get("total_paginas", 1))
        esqueletoSalas = []
        for pag in range(1, totalPaginas + 1):
            respPag = self.cliente.obtenerEsqueleto(idCripta, pag)
            for sala in respPag.get("salas", []):
                esqueletoSalas.append(sala)

        # Precargar sala inicial y sus salas contiguas antes del instante 0 (§2.4)
        salaInicial = datosGen["sala_inicial"]
        self.precargarVecindad(salaInicial, esqueletoSalas)

        return datosGen, esqueletoSalas

    def asegurarContenidoSala(self, idSala: int, esqueletoSalas: list) -> dict:
        # Garantiza que la sala destino esté en memoria antes de entrar (§2.5 / §4.2)
        contenido = self.salasDescargadas.obtener(idSala)
        if contenido is None:
            self.precargarVecindad(idSala, esqueletoSalas)
            contenido = self.salasDescargadas.obtener(idSala)
        return contenido

    def precargarVecindad(self, idSalaOrigen: int, esqueletoSalas: list):
        # Cola FIFO para recolectar hasta 10 salas cercanas no descargadas (§4.2)
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

        if len(porDescargar) > 0:
            self._descargarLoteSalasYCatalogo(porDescargar)

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
        # Descarga salas en lotes de máximo 10 (§3.4)
        for i in range(0, len(loteSalas), 10):
            subLoteSalas = loteSalas[i : i + 10]
            respuesta = self.cliente.obtenerContenidoLote(self.idCriptaActual, subLoteSalas)
            idsCatalogoFaltantes = []

            for infoSala in respuesta.get("contenido", []):
                self.salasDescargadas.guardar(infoSala["sala"], infoSala)

                # Comprueba sin alterar métricas del jugador: registrar_metrica=False (§5.1)
                for enem in infoSala.get("enemigos", []):
                    tipo = enem["tipo"]
                    if (
                        not self.cacheCatalogo.contiene(tipo, registrar_metrica=False)
                        and tipo not in idsCatalogoFaltantes
                    ):
                        idsCatalogoFaltantes.append(tipo)

                for objId in infoSala.get("objetos", []):
                    if (
                        not self.cacheCatalogo.contiene(objId, registrar_metrica=False)
                        and objId not in idsCatalogoFaltantes
                    ):
                        idsCatalogoFaltantes.append(objId)

                for trampa in infoSala.get("trampas", []):
                    tipo = trampa["tipo"]
                    if (
                        not self.cacheCatalogo.contiene(tipo, registrar_metrica=False)
                        and tipo not in idsCatalogoFaltantes
                    ):
                        idsCatalogoFaltantes.append(tipo)

            # Orden determinista (§4.2 / §4.11) para garantizar reproducibilidad exacta
            idsCatalogoFaltantes.sort()

            # Pedir al catálogo en lotes de máximo 10 IDs
            for j in range(0, len(idsCatalogoFaltantes), 10):
                subLoteCat = idsCatalogoFaltantes[j : j + 10]
                respCat = self.cliente.obtenerCatalogoLote(subLoteCat)
                for ficha in respCat.get("entidades", []):
                    self.cacheCatalogo.insertar(ficha["id"], ficha)

    def generarReporteRendimientoRed(self) -> str:
        """Regla 5.1: Reporta solicitudes realizadas, presupuesto, aciertos y fallos de caché."""
        realizadas = self.cliente.obtenerSolicitudesRealizadas()
        aciertos = self.cacheCatalogo.aciertos
        fallos = self.cacheCatalogo.fallos
        return (
            f"=== REPORTE DE RED Y CACHÉ (§5.1) ===\n"
            f"Solicitudes HTTP realizadas : {realizadas} / {self.presupuestoMaximo}\n"
            f"Estado del presupuesto      : {'CUMPLIDO' if realizadas <= self.presupuestoMaximo else 'EXCEDIDO'}\n"
            f"Aciertos de caché (RAM)     : {aciertos}\n"
            f"Fallos de caché (RAM)       : {fallos}\n"
            f"====================================="
        )

    # Alias en snake_case
    inicializar_cripta = inicializarCripta
    asegurar_contenido_sala = asegurarContenidoSala
    precargar_vecindad = precargarVecindad
    _obtener_salas_contiguas = _obtenerSalasContiguas
    _descargar_lote_salas_y_catalogo = _descargarLoteSalasYCatalogo
    generar_reporte_rendimiento_red = generarReporteRendimientoRed