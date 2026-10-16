import json
import os

#Guarda y lee fichas de catálogo en disco para persistencia entre sesiones. No es un cliente HTTP ni offline, solo maneja archivos locales.
class AlmacenamientoPersistenteCache:
    #Inicializa el almacenamiento persistente de la caché, creando el directorio si no existe.
    def __init__(self, directorio_cache: str = ".cache_cripta"):
        self.directorio = directorio_cache
        os.makedirs(self.directorio, exist_ok=True)
    # Guarda una ficha de catálogo en disco, creando un subdirectorio por versión del catálogo.
    def guardar_ficha_disco(self, version_catalogo: str, id_entidad: str, ficha: dict):
        carpeta_cat = os.path.join(self.directorio, f"cat_{version_catalogo}")
        os.makedirs(carpeta_cat, exist_ok=True)
        ruta = os.path.join(carpeta_cat, f"{id_entidad}.json")
        with open(ruta, "w", encoding="utf-8") as f: json.dump(ficha, f, ensure_ascii=False)
    # Lee una ficha de catálogo desde disco, devolviendo None si no existe o si hay un error de lectura.
    def leer_ficha_disco(self, version_catalogo: str, id_entidad: str) -> dict | None:
        ruta = os.path.join(self.directorio, f"cat_{version_catalogo}", f"{id_entidad}.json")
        if not os.path.exists(ruta): return None
        try:
            with open(ruta, "r", encoding="utf-8") as f: return json.load(f)
        except Exception:
            return None