import os
from adapters.clienteCripta import ClienteCripta


class GestorBitacoraReplay:
    def __init__(self, ruta_log: str = "partida.log"):
        self.ruta_log = ruta_log

    def iniciarNuevaBitacora(
        self,
        id_cripta: str,
        version_cripta: str,
        version_catalogo: str,
        semilla: int,
    ):
        # Crea un encabezado para la partida
        with open(self.ruta_log, "w", encoding="utf-8") as archivo:
            archivo.write(f"HEADER|{id_cripta}|{version_cripta}|{version_catalogo}|{semilla}\n")

    def registrar_accion(self, comando_accion: str):
        # Agrega una accion al jugador
        with open(self.ruta_log, "a", encoding="utf-8") as archivo:
            archivo.write(f"ACCION|{comando_accion}\n")

    def cargarYValidaReplay(self, cliente: ClienteCripta) -> tuple:
        #Lee un archivo .log para --replay y verifica que las versiones coincidan (§4.11).
        if not os.path.exists(self.ruta_log):
            raise RuntimeError(f"[Replay] No existe el archivo de bitácora: {self.ruta_log}")

        with open(self.ruta_log, "r", encoding="utf-8") as archivo:
            lineas = [linea.strip() for linea in archivo if linea.strip()]

        if len(lineas) == 0 or not lineas[0].startswith("HEADER|"):
            raise RuntimeError(f"[Replay] Formato de bitácora inválido en {self.ruta_log}: falta HEADER.")

        partes_header = lineas[0].split("|")
        if len(partes_header) != 5:raise RuntimeError(f"[Replay] Encabezado corrupto en el archivo .log.")
        # Extraemos los metadatos del encabezado
        _, id_cripta, ver_cripta_log, ver_cat_log, semilla_str = partes_header
        semilla = int(semilla_str)

        # Valida versiones contra el servidor o copia local
        ver_cripta_actual = cliente.obtener_version_cripta(id_cripta).get("version")
        ver_cat_actual = cliente.obtener_version_catalogo().get("version")
        # Si las versiones no coinciden, se lanza un error para evitar una reproducción incorrecta
        if ver_cripta_actual != ver_cripta_log:
            raise RuntimeError(
                f"[Replay Incompatible] La versión de la cripta '{id_cripta}' en el log "
                f"({ver_cripta_log}) no coincide con la versión disponible ({ver_cripta_actual}). "
                f"No se puede garantizar una reproducción fiel."
            )
        # Si la versión del catálogo no coincide, también se lanza un error
        if ver_cat_actual != ver_cat_log:
            raise RuntimeError(
                f"[Replay Incompatible] La versión del catálogo en el log "
                f"({ver_cat_log}) no coincide con la versión disponible ({ver_cat_actual}). "
                f"No se puede garantizar una reproducción fiel."
            )
        # Extrae las acciones registradas en la bitácora para reproducirlas
        acciones = []
        for linea in lineas[1:]: 
            if linea.startswith("ACCION|"): acciones.append(linea.split("|", 1)[1])
        # Devuelve los metadatos y la lista de acciones para que el juego pueda reproducir la partida
        metadatos = {
            "id_cripta": id_cripta,
            "version_cripta": ver_cripta_log,
            "version_catalogo": ver_cat_log,
            "semilla": semilla,
        }
        return metadatos, acciones