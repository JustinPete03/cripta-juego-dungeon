import os

from model.cache.CacheFichas import CacheFichas
from model.cache.PersistenciaCache import guardarCache, cargarCache

def testGuardarYCargarCacheExitoso(tmp_path):
    archivoTemporal = tmp_path / "cache_prueba.json"
    cacheOriginal = CacheFichas(capacidad=5)
    cacheOriginal.guardarFicha("f1", {"nombre": "Orco"})
    cacheOriginal.guardarFicha("f2", {"nombre": "Esqueleto"})

    guardarCache(str(archivoTemporal), "1.0.0", cacheOriginal)

    cacheNueva = CacheFichas(capacidad=5)
    exito = cargarCache(str(archivoTemporal), "1.0.0", cacheNueva)

    assert exito is True
    assert cacheNueva.consultarFicha("f1") == {"nombre": "Orco"}
    assert cacheNueva.consultarFicha("f2") == {"nombre": "Esqueleto"}

def testCargarArchivoInexistente(tmp_path):
    archivoFalso = tmp_path / "no_existe.json"
    cache = CacheFichas()

    exito = cargarCache(str(archivoFalso), "1.0.0", cache)

    assert exito is False
    assert cache.lista.tamanio == 0

def testCargarVersionInvalida(tmp_path):
    archivoTemporal = tmp_path / "cache_vieja.json"
    cache = CacheFichas()
    cache.guardarFicha("f1", {"nombre": "Mago"})

    guardarCache(str(archivoTemporal), "1.0.0", cache)

    cacheDestino = CacheFichas()
    exito = cargarCache(str(archivoTemporal), "2.0.0", cacheDestino)

    assert exito is False
    assert cacheDestino.consultarFicha("f1") is None

def testCargarArchivoCorrupto(tmp_path):
    archivoCorrupto = tmp_path / "corrupto.json"
    with open(archivoCorrupto, "w", encoding="utf-8") as f:
        f.write("{ json incompleto...")

    cache = CacheFichas()
    exito = cargarCache(str(archivoCorrupto), "1.0.0", cache)

    assert exito is False
    assert cache.lista.tamanio == 0

def testGuardarYCargarPreservaOrdenLRU(tmp_path):
    archivo = tmp_path / "orden_lru.json"
    cache = CacheFichas(capacidad=3)
    cache.guardarFicha("a", 1)
    cache.guardarFicha("b", 2)
    cache.guardarFicha("c", 3)
    cache.consultarFicha("a")

    guardarCache(str(archivo), "1.0.0", cache)

    cacheRestaurada = CacheFichas(capacidad=3)
    cargarCache(str(archivo), "1.0.0", cacheRestaurada)

    assert cacheRestaurada.lista.primero.idFicha == "a"
    assert cacheRestaurada.lista.ultimo.idFicha == "b"

def testGuardarFichaNoSerializableNoDejaTemporales(tmp_path):
    archivo = tmp_path / "cache.json"
    cache = CacheFichas(capacidad=3)
    cache.guardarFicha("f1", {"nombre": "Orco"})
    assert guardarCache(str(archivo), "1.0.0", cache) is True

    cache.guardarFicha("f2", {1, 2})  #un set no es serializable a JSON
    assert guardarCache(str(archivo), "1.0.0", cache) is False

    assert os.listdir(tmp_path) == ["cache.json"]

    cacheNueva = CacheFichas(capacidad=3)
    assert cargarCache( str(archivo), "1.0.0", cacheNueva) is True
    assert cacheNueva.consultarFicha("f1") == {"nombre": "Orco"}
    assert cacheNueva.consultarFicha("f2") is None