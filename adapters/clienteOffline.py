import json
import os
from adapters.clienteCripta import ClienteCripta

# Modo offline, leyendo datos desde archivos locales.
class ClienteOffline(ClienteCripta):
    def __init__(self, directorio_datos: str):
        self.directorio = directorio_datos
        self.solicitudes_realizadas = 0 #Como lee arhivos locales, no cuenta solicitudes HTTP

    def _leer_json(self, nombre_archivo: str) -> dict:
        ruta = os.path.join(self.directorio, nombre_archivo)
        # Lee un archivo JSON y devuelve su contenido como diccionario. Maneja errores de archivo no encontrado o JSON corrupto.
        try:
            with open(ruta, "r", encoding="utf-8") as archivo: return json.load(archivo)
        except FileNotFoundError:
            raise RuntimeError(f"[Modo Offline] No se encontró el archivo requerido: {ruta}")
        except json.JSONDecodeError:
            raise RuntimeError(f"[Modo Offline] El archivo JSON está corrupto: {ruta}")

    def obtener_lista_criptas(self) -> dict:
        return self._leer_json("criptas.json")

    def obtener_datos_generales(self, id_cripta: str) -> dict:
        return self._leer_json(f"{id_cripta}_general.json")

    def obtener_version_cripta(self, id_cripta: str) -> dict:
        datos = self.obtener_datos_generales(id_cripta)
        return {"id": id_cripta, "version": datos.get("version", "offline")}

    def obtener_version_catalogo(self) -> dict:
        return self._leer_json("catalogo_version.json")

    def obtener_esqueleto(self, id_cripta: str, pagina: int = 1) -> dict:
        return self._leer_json(f"{id_cripta}_salas_p{pagina}.json")
    
    # Busca en un archivo consolidado de contenidoy filtra las salas pedidas
    def obtener_contenido_lote(self, id_cripta: str, salas: list) -> dict:
        datos_completos = self._leer_json(f"{id_cripta}_contenido.json")
        resultado = []
        for item in datos_completos.get("contenido", []):
            if item.get("sala") in salas:
                resultado.append(item)
        return {"contenido": resultado}
        # Busca en el catálogo offline y filtra los IDs solicitados
    def obtener_catalogo_lote(self, ids_catalogo: list) -> dict:
        catalogo_completo = self._leer_json("catalogo.json")
        resultado = []
        for entidad in catalogo_completo.get("entidades", []):
            if entidad.get("id") in ids_catalogo:
                resultado.append(entidad)
        return {"entidades": resultado}
 #
    def obtener_solicitudes_realizadas(self) -> int:
        return 0