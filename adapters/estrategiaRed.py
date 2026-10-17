from adapters.clienteCripta import ClienteCripta
from model.cache_estructuras import CacheCatalogo, RegistroSalas


class GestorRedPrecarga:
    def __init__(self, cliente: ClienteCripta, cache_catalogo: CacheCatalogo):
        self.cliente = cliente
        self.cache_catalogo = cache_catalogo
        self.salas_descargadas = RegistroSalas()
        self.presupuesto_maximo = 0
        self.id_cripta_actual = ""

    def inicializar_cripta(self, id_cripta: str) -> tuple:
       # Descarga datos generales, todo el esqueleto y precarga la sala inicial.
        self.id_cripta_actual = id_cripta
        datos_gen = self.cliente.obtener_datos_generales(id_cripta)
        self.presupuesto_maximo = datos_gen["presupuesto_solicitudes"]

        # Descargar todas las páginas del esqueleto para tener la lista completa de salas y sus salidas
        total_paginas = datos_gen.get("paginas", 1)
        esqueleto_salas = []
        for pag in range(1, total_paginas + 1):
            resp_pag = self.cliente.obtener_esqueleto(id_cripta, pag)
            for sala in resp_pag.get("salas", []): esqueleto_salas.append(sala)

        # Precargar sala inicial y sus salas contiguas antes del instante 0
        sala_inicial = datos_gen["sala_inicial"]
        self.precargar_vecindad(sala_inicial, esqueleto_salas)

        return datos_gen, esqueleto_salas

    def asegurar_contenido_sala(
        self, id_sala: int, esqueleto_salas: list
    ) -> dict:
        # Garantiza que la sala destino esté en memoria antes de entrar 
        contenido = self.salas_descargadas.obtener(id_sala)
        if contenido is None:
            self.precargar_vecindad(id_sala, esqueleto_salas)
            contenido = self.salas_descargadas.obtener(id_sala)
        return contenido

    def precargar_vecindad(self, id_sala_origen: int, esqueleto_salas: list):
        # Usa una Cola FIFO para recolectar hasta 10 salas cercanas no descargadas 
        por_descargar = []
        cola_pendientes = [id_sala_origen]
        indice_frente = 0
        registradas_en_cola = [id_sala_origen]
        while (
            indice_frente < len(cola_pendientes) and len(por_descargar) < 10): 
            sala_actual = cola_pendientes[indice_frente]
            indice_frente += 1 # Avanzar el frente de la cola

            if not self.salas_descargadas.contiene(sala_actual): #  Si la sala no está en memoria, agregarla a la lista de descarga
                por_descargar.append(sala_actual)
                if len(por_descargar) == 10: break  #Si ya tenemos 10 salas, no necesitamos buscar más

            # Buscar las salidas contiguas en la lista del esqueleto
            salas_contiguas = self._obtener_salas_contiguas(sala_actual, esqueleto_salas)
            for id_contigua in salas_contiguas:
                if id_contigua not in registradas_en_cola:
                    registradas_en_cola.append(id_contigua)
                    cola_pendientes.append(id_contigua) 
        # Si hay salas pendientes de descargar, hacer la solicitud al servidor
        if len(por_descargar) > 0: self._descargar_lote_salas_y_catalogo(por_descargar)

    def _obtener_salas_contiguas(
        self, id_sala: int, esqueleto_salas: list) -> list:
        # Busca en el esqueleto de la cripta las salas contiguas a la sala dada, según sus salidas.
        contiguas = []
        for s in esqueleto_salas:
            if s["id"] == id_sala:
                salidas = s.get("salidas", {})
                for direccion in ["N", "S", "E", "O"]:
                    if direccion in salidas: contiguas.append(salidas[direccion]["sala"])
                break
        return contiguas

    def _descargar_lote_salas_y_catalogo(self, lote_salas: list):
        # Solicita al cliente el contenido de las salas y luego descarga los elementos del catálogo que no estén en caché.
        respuesta = self.cliente.obtener_contenido_lote(self.id_cripta_actual, lote_salas)
        ids_catalogo_faltantes = []

        for info_sala in respuesta.get("contenido", []):
            self.salas_descargadas.guardar(info_sala["sala"], info_sala)

            # Recolectar IDs de enemigos, objetos y trampas que no estén en caché
            for enem in info_sala.get("enemigos", []):
                tipo = enem["tipo"]
                if (
                    not self.cache_catalogo.contiene(tipo)
                    and tipo not in ids_catalogo_faltantes
                ):
                    ids_catalogo_faltantes.append(tipo)

            for obj_id in info_sala.get("objetos", []):
                if (
                    not self.cache_catalogo.contiene(obj_id)
                    and obj_id not in ids_catalogo_faltantes
                ):
                    ids_catalogo_faltantes.append(obj_id)

            for trampa in info_sala.get("trampas", []):
                tipo = trampa["tipo"]
                if (
                    not self.cache_catalogo.contiene(tipo)
                    and tipo not in ids_catalogo_faltantes
                ):
                    ids_catalogo_faltantes.append(tipo)

        # Pedir al catálogo en lotes de máximo 10 IDs
        for i in range(0, len(ids_catalogo_faltantes), 10):
            sub_lote = ids_catalogo_faltantes[i : i + 10]
            resp_cat = self.cliente.obtener_catalogo_lote(sub_lote)
            for ficha in resp_cat.get("entidades", []): self.cache_catalogo.insertar(ficha["id"], ficha)

#Se crea un reporte de rendimiento de la red y la caché, mostrando solicitudes realizadas, presupuesto, aciertos y fallos de caché.
    def generar_reporte_rendimiento_red(self) -> str:
        """Regla 5.1: Reporta solicitudes realizadas, presupuesto, aciertos y fallos de caché."""
        realizadas = self.cliente.obtener_solicitudes_realizadas()
        aciertos = self.cache_catalogo.aciertos
        fallos = self.cache_catalogo.fallos
        return (
            f"=== REPORTE DE RED Y CACHÉ (§5.1) ===\n"
            f"Solicitudes HTTP realizadas : {realizadas} / {self.presupuesto_maximo}\n"
            f"Estado del presupuesto      : {'CUMPLIDO' if realizadas <= self.presupuesto_maximo else 'EXCEDIDO'}\n"
            f"Aciertos de caché (RAM)     : {aciertos}\n"
            f"Fallos de caché (RAM)       : {fallos}\n"
            f"====================================="
        )