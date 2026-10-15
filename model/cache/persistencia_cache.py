import json
import os

from model.cache import cache_fichas
from model.cache import lista_doble

def guardar_cache(rutaArchivo, version, cache):
    fichas_a_guardar = []
    actual = cache.lista.ultimo
    while actual is not None:
        fichas_a_guardar.append((actual.id_ficha, actual.ficha))
        actual = actual.anterior

    datos = {"version": version, "fichas": fichas_a_guardar}

    with open(rutaArchivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2)


def cargar_cache(rutaArchivo, versionEsperada, cache):
    if not os.path.exists(rutaArchivo):
        return False

    with open(rutaArchivo, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    if datos.get("version") != versionEsperada:
        return False

    for id_ficha, ficha in datos.get("fichas", []):
        cache.guardar_ficha(id_ficha, ficha)

    return True
