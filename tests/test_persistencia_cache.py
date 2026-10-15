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