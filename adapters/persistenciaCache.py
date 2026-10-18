import json
import os
import tempfile


# Guarda y lee fichas de catálogo en disco para persistencia entre sesiones (sección 4.4)
class AlmacenamientoPersistenteCache:
    def __init__(self, directorioCache: str = ".cache_cripta"):
        self.directorioCache = directorioCache
        os.makedirs(self.directorioCache, exist_ok=True)

    @property
    def directorio(self):
        return self.directorioCache

    def guardarFichaDisco(self, versionCatalogo: str, idEntidad: str, ficha: dict):
        carpetaCat = os.path.join(self.directorioCache, f"cat_{versionCatalogo}")
        os.makedirs(carpetaCat, exist_ok=True)
        ruta = os.path.join(carpetaCat, f"{idEntidad}.json")

        rutaTemp = None
        try:
            with tempfile.NamedTemporaryFile("w", dir=carpetaCat, delete=False, encoding="utf-8") as temp:
                rutaTemp = temp.name
                json.dump(ficha, temp, ensure_ascii=False)
            os.replace(rutaTemp, ruta)
        except Exception:
            if rutaTemp and os.path.exists(rutaTemp):
                try:
                    os.remove(rutaTemp)
                except OSError:
                    pass

    def leerFichaDisco(self, versionCatalogo: str, idEntidad: str) -> dict | None:
        ruta = os.path.join(self.directorioCache, f"cat_{versionCatalogo}", f"{idEntidad}.json")
        if not os.path.exists(ruta):
            return None
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # Alias en snake_case
    guardar_ficha_disco = guardarFichaDisco
    leer_ficha_disco = leerFichaDisco