import json
import os
import tempfile

from model.cache.AlmacenFichas import AlmacenFichas

#guarda una ficha por archivo JSON dentro de una carpeta
class AlmacenFichasDisco(AlmacenFichas) :

    def __init__(self, directorio = ".cacheFichas"):
        self.directorio = directorio
        os.makedirs(self.directorio, exist_ok=True)

    def ruta(self, idFicha):
        nombre = str(idFicha).encode("utf-8").hex()
        return os.path.join(self.directorio, nombre + ".json")

    def guardar(self, idFicha, ficha):
        rutaTemporal = None
        try:
            with tempfile.NamedTemporaryFile("w", dir = self.directorio, delete = False, encoding = "utf-8") as temp:
                rutaTemporal = temp.name
                json.dump(ficha, temp, ensure_ascii=False)
            os.replace(rutaTemporal, self.ruta(idFicha))
            return True
        except (TypeError, ValueError, OSError):
            if rutaTemporal and os.path.exists(rutaTemporal):
                os.remove(rutaTemporal)
            return False

    def leer(self, idFicha):
        ruta = self.ruta(idFicha)
        if not os.path.exists(ruta):
            return None
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except(json.JSONDecodeError, OSError):
            return None
