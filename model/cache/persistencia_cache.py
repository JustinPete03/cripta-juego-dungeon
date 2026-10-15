import json
import os

def guardar_cache(ruta_archivo, version, cache):
    fichas_a_guardar = []
    actual = cache.lista.ultimo
    while actual is not None:
        fichas_a_guardar.append((actual.id_ficha, actual.ficha))
        actual = actual.anterior

    datos = {"version": version, "fichas": fichas_a_guardar}

    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2)


def cargar_cache(ruta_archivo, version_esperada, cache):
    if not os.path.exists(ruta_archivo):
        return False

    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    if datos.get("version") != version_esperada:
        return False

    for id_ficha, ficha in datos.get("fichas", []):
        cache.guardar_ficha(id_ficha, ficha)

    return True
