import json
import os
import tempfile

def guardarCache(rutaArchivo, version, cache):
    fichasAGuardar = []
    actual = cache.lista.ultimo
    while actual is not None:
        fichasAGuardar.append((actual.idFicha, actual.ficha))
        actual = actual.anterior

    datos = {"version": version, "fichas": fichasAGuardar}

    directorio = os.path.dirname(rutaArchivo) or "."
    rutaTemporal = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=directorio, delete=False, encoding="utf-8") as temp:
            rutaTemporal = temp.name
            json.dump(datos, temp, indent=2)
        os.replace(rutaTemporal, rutaArchivo)
        return True
    except (TypeError, ValueError, OSError):
        if rutaTemporal and os.path.exists(rutaTemporal):
            os.remove(rutaTemporal)
        return False

def cargarCache(rutaArchivo, versionEsperada, cache):
    if not os.path.exists(rutaArchivo):
        return False

    try:
        with open(rutaArchivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (json.JSONDecodeError, OSError):
        return False

    if not isinstance(datos, dict) or datos.get("version") != versionEsperada:
        return False

    for idFicha, ficha in datos.get("fichas", []):
        cache.guardarFicha(idFicha, ficha)

    return True
