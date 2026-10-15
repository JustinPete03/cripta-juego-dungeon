from model.cache.cache_fichas import CacheFichas
from model.cache.persistencia_cache import guardar_cache, cargar_cache

def test_guardar_y_cargar_cache_exitoso(tmp_path):
    archivo_temporal = tmp_path / "cache_prueba.json"
    cache_original = CacheFichas(capacidad=5)
    cache_original.guardar_ficha("f1", {"nombre": "Orco"})
    cache_original.guardar_ficha("f2", {"nombre": "Esqueleto"})

    guardar_cache(str(archivo_temporal), "1.0.0", cache_original)

    cache_nueva = CacheFichas(capacidad=5)
    exito = cargar_cache(str(archivo_temporal), "1.0.0", cache_nueva)

    assert exito is True
    assert cache_nueva.consultar_ficha("f1") == {"nombre": "Orco"}
    assert cache_nueva.consultar_ficha("f2") == {"nombre": "Esqueleto"}


def test_cargar_archivo_inexistente(tmp_path):
    archivo_falso = tmp_path / "no_existe.json"
    cache = CacheFichas()

    exito = cargar_cache(str(archivo_falso), "1.0.0", cache)

    assert exito is False
    assert cache.lista.tamanio == 0


def test_cargar_version_invalida(tmp_path):
    archivo_temporal = tmp_path / "cache_vieja.json"
    cache = CacheFichas()
    cache.guardar_ficha("f1", {"nombre": "Mago"})

    guardar_cache(str(archivo_temporal), "1.0.0", cache)

    cache_destino = CacheFichas()
    exito = cargar_cache(str(archivo_temporal), "2.0.0", cache_destino)

    assert exito is False
    assert cache_destino.consultar_ficha("f1") is None

def test_cargar_archivo_corrupto(tmp_path):
    archivo_corrupto = tmp_path / "corrupto.json"
    with open(archivo_corrupto, "w", encoding="utf-8") as f:
        f.write("{ json incompleto...")

    cache = CacheFichas()
    exito = cargar_cache(str(archivo_corrupto), "1.0.0", cache)

    assert exito is False
    assert cache.lista.tamanio == 0

def test_guardar_y_cargar_preserva_orden_lru(tmp_path):
    archivo = tmp_path / "orden_lru.json"
    cache = CacheFichas(capacidad=3)
    cache.guardar_ficha("a", 1)
    cache.guardar_ficha("b", 2)
    cache.guardar_ficha("c", 3)
    cache.consultar_ficha("a")

    guardar_cache(str(archivo), "1.0.0", cache)

    cache_restaurada = CacheFichas(capacidad=3)
    cargar_cache(str(archivo), "1.0.0", cache_restaurada)

    assert cache_restaurada.lista.primero.id_ficha == "a"
    assert cache_restaurada.lista.ultimo.id_ficha == "b"