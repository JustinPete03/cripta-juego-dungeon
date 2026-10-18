import json
import os
from adapters.clienteCripta import ClienteCripta


# Modo offline, leyendo datos desde archivos locales (§Modo sin conexión)
class ClienteOffline(ClienteCripta):

    def __init__(self, directorioDatos: str):
        self.directorioDatos = directorioDatos
        self.solicitudesRealizadas = 0  # Lecturas desde almacenamiento local o modo --offline no cuentan (§5.1)
        self._cacheArchivos = {}

    @property
    def directorio(self):
        return self.directorioDatos

    @property
    def solicitudes_realizadas(self):
        return self.solicitudesRealizadas

    def _leerJson(self, nombreArchivo: str) -> dict:
        if nombreArchivo in self._cacheArchivos:
            return self._cacheArchivos[nombreArchivo]

        ruta = os.path.join(self.directorioDatos, nombreArchivo)
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
                self._cacheArchivos[nombreArchivo] = datos
                return datos
        except FileNotFoundError:
            raise RuntimeError(f"[Modo Offline] No se encontró el archivo requerido: {ruta}")
        except json.JSONDecodeError:
            raise RuntimeError(f"[Modo Offline] El archivo JSON está corrupto: {ruta}")

    _leer_json = _leerJson

    def obtenerListaCriptas(self) -> dict:
        return self._leerJson("criptas.json")

    def obtenerDatosGenerales(self, idCripta: str) -> dict:
        return self._leerJson(f"{idCripta}_general.json")

    def obtenerVersionCripta(self, idCripta: str) -> dict:
        # Busca primero si existe un archivo específico {idCripta}_version.json
        rutaVersion = os.path.join(self.directorioDatos, f"{idCripta}_version.json")
        if os.path.exists(rutaVersion):
            return self._leerJson(f"{idCripta}_version.json")
        datos = self.obtenerDatosGenerales(idCripta)
        return {"id": idCripta, "version": datos.get("version", "offline")}

    def obtenerVersionCatalogo(self) -> dict:
        return self._leerJson("catalogo_version.json")

    def obtenerEsqueleto(self, idCripta: str, pagina: int = 1) -> dict:
        nombrePag = f"{idCripta}_salas_p{pagina}.json"
        rutaPag = os.path.join(self.directorioDatos, nombrePag)
        if not os.path.exists(rutaPag) and pagina == 1:
            # Fallback a {idCripta}_salas.json si no está paginado
            nombreGeneral = f"{idCripta}_salas.json"
            if os.path.exists(os.path.join(self.directorioDatos, nombreGeneral)):
                return self._leerJson(nombreGeneral)
        return self._leerJson(nombrePag)

    # Busca en el archivo consolidado de contenido y filtra las salas pedidas
    def obtenerContenidoLote(self, idCripta: str, salas: list) -> dict:
        if not salas:
            return {"contenido": []}
        if len(salas) > 10:
            raise ValueError("El lote de contenido no puede superar las 10 salas por solicitud.")
        datosCompletos = self._leerJson(f"{idCripta}_contenido.json")
        resultado = []
        for item in datosCompletos.get("contenido", []):
            if item.get("sala") in salas:
                resultado.append(item)
        return {"contenido": resultado}

    # Busca en el catálogo offline y filtra los IDs solicitados
    def obtenerCatalogoLote(self, idsCatalogo: list) -> dict:
        if not idsCatalogo:
            return {"entidades": []}
        if len(idsCatalogo) > 10:
            raise ValueError("El lote de catálogo no puede superar los 10 IDs por solicitud.")
        catalogoCompleto = self._leerJson("catalogo.json")
        resultado = []
        for entidad in catalogoCompleto.get("entidades", []):
            if entidad.get("id") in idsCatalogo:
                resultado.append(entidad)
        return {"entidades": resultado}

    def obtenerSolicitudesRealizadas(self) -> int:
        return 0

    # Alias en snake_case
    obtener_lista_criptas = obtenerListaCriptas
    obtener_datos_generales = obtenerDatosGenerales
    obtener_version_cripta = obtenerVersionCripta
    obtener_version_catalogo = obtenerVersionCatalogo
    obtener_esqueleto = obtenerEsqueleto
    obtener_contenido_lote = obtenerContenidoLote
    obtener_catalogo_lote = obtenerCatalogoLote
    obtener_solicitudes_realizadas = obtenerSolicitudesRealizadas