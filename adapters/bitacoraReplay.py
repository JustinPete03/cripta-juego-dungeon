import os
from adapters.clienteCripta import ClienteCripta


class GestorBitacoraReplay:
    def __init__(self, rutaLog: str = "partida.log"):
        self.rutaLog = rutaLog

    @property
    def ruta_log(self):
        return self.rutaLog

    def iniciarNuevaBitacora(
        self,
        idCripta: str,
        versionCripta: str,
        versionCatalogo: str,
        semilla: int,
    ):
        # Crea el encabezado canónico de la bitácora (sección 4.11)
        with open(self.rutaLog, "w", encoding="utf-8") as archivo:
            archivo.write(f"HEADER|{idCripta}|{versionCripta}|{versionCatalogo}|{semilla}\n")

    def registrarAccion(self, comandoAccion: str):
        # Agrega la acción canónica en modo append (sección 4.11)
        with open(self.rutaLog, "a", encoding="utf-8") as archivo:
            archivo.write(f"ACCION|{comandoAccion}\n")

    registrar_accion = registrarAccion

    def cargarYValidarReplay(self, cliente: ClienteCripta) -> tuple:
        """Lee un archivo .log para --replay y verifica que las versiones coincidan (sección 4.11)."""
        if not os.path.exists(self.rutaLog):
            raise RuntimeError(f"[Replay] No existe el archivo de bitácora: {self.rutaLog}")

        with open(self.rutaLog, "r", encoding="utf-8") as archivo:
            lineas = [linea.strip() for linea in archivo if linea.strip()]

        if len(lineas) == 0 or not lineas[0].startswith("HEADER|"):
            raise RuntimeError(f"[Replay] Formato de bitácora inválido en {self.rutaLog}: falta HEADER.")

        partesHeader = lineas[0].split("|")
        if len(partesHeader) != 5:
            raise RuntimeError(f"[Replay] Encabezado corrupto en el archivo .log.")

        # Extraer metadatos
        _, idCripta, verCriptaLog, verCatLog, semillaStr = partesHeader
        semilla = int(semillaStr)

        # Valida versiones contra el cliente (HTTP u Offline)
        verCriptaActual = cliente.obtenerVersionCripta(idCripta).get("version")
        verCatActual = cliente.obtenerVersionCatalogo().get("version")

        if verCriptaActual != verCriptaLog:
            raise RuntimeError(
                f"[Replay Incompatible] La versión de la cripta '{idCripta}' en el log "
                f"({verCriptaLog}) no coincide con la versión disponible ({verCriptaActual}). "
                f"No se puede garantizar una reproducción fiel (sección 4.11)."
            )

        if verCatActual != verCatLog:
            raise RuntimeError(
                f"[Replay Incompatible] La versión del catálogo en el log "
                f"({verCatLog}) no coincide con la versión disponible ({verCatActual}). "
                f"No se puede garantizar una reproducción fiel (sección 4.11)."
            )

        # Extraer acciones registradas
        acciones = []
        for linea in lineas[1:]:
            if linea.startswith("ACCION|"):
                acciones.append(linea.split("|", 1)[1])

        metadatos = {
            "idCripta": idCripta,
            "versionCripta": verCriptaLog,
            "versionCatalogo": verCatLog,
            "semilla": semilla,
            # Compatibilidad con accesos previos
            "id_cripta": idCripta,
            "version_cripta": verCriptaLog,
            "version_catalogo": verCatLog,
        }
        return metadatos, acciones

    cargarYValidaReplay = cargarYValidarReplay