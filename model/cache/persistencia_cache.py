import json
import os
import tempfile

def guardar_cache(ruta_archivo, version, cache):
    fichas_a_guardar = []
    actual = cache.lista.ultimo
    while actual is not None:
        fichas_a_guardar.append((actual.id_ficha, actual.ficha))
        actual = actual.anterior

    datos = {"version": version, "fichas": fichas_a_guardar}

    directorio = os.path.dirname(ruta_archivo) or "."
    ruta_temporal = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=directorio, delete=False, encoding="utf-8") as temp:
            ruta_temporal = temp.name
            json.dump(datos, temp, indent=2)
        os.replace(ruta_temporal, ruta_archivo)
        return True
    except (TypeError, ValueError, OSError):
        if ruta_temporal and os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
        return False

def cargar_cache(ruta_archivo, version_esperada, cache):
    if not os.path.exists(ruta_archivo):
        return False

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (json.JSONDecodeError, OSError):
        return False

    if not isinstance(datos, dict) or datos.get("version") != version_esperada:
        return False

    for id_ficha, ficha in datos.get("fichas", []):
        cache.guardar_ficha(id_ficha, ficha)

    return True
