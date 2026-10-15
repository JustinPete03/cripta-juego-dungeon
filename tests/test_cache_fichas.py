from model.cache.cache_fichas import CacheFichas

def ids_cache(cache):
    ids = []
    actual = cache.lista.primero
    while actual is not None:
        ids.append(actual.id_ficha)
        actual = actual.siguiente
    return ids

def test_estado_inicial():
    cache = CacheFichas()
    assert cache.capacidad == 25
    assert cache.lista.tamanio == 0
    assert cache.aciertos == 0
    assert cache.fallos == 0
    assert cache.desalojos == 0
    assert cache.veces_sobre_tope == 0
    assert cache.maximo_alcanzado == 0

def test_acierto_y_fallo():
    cache = CacheFichas()
    cache.guardar_ficha("a", "ficha_a")
    assert cache.consultar_ficha("a") == "ficha_a"
    assert cache.consultar_ficha("z") is None
    assert cache.aciertos == 1
    assert cache.fallos == 1

def test_guardar_existente_no_duplica():
    cache = CacheFichas()
    cache.guardar_ficha("a", "v1")
    cache.guardar_ficha("a", "v2")
    assert cache.lista.tamanio == 1
    assert cache.consultar_ficha("a") == "v2"

def test_consultar_mueve_al_frente():
    cache = CacheFichas(3)
    cache.guardar_ficha("a", "ficha_a")
    cache.guardar_ficha("b", "ficha_b")
    cache.guardar_ficha("c", "ficha_c")
    assert ids_cache(cache) == ["c", "b", "a"]
    cache.consultar_ficha("a")
    assert ids_cache(cache) == ["a", "c", "b"]

def test_desaloja_el_menos_reciente():
    cache = CacheFichas(2)
    cache.guardar_ficha("a", "ficha_a")
    cache.guardar_ficha("b", "ficha_b")
    cache.consultar_ficha("a")
    cache.guardar_ficha("c", "ficha_c")
    assert ids_cache(cache) == ["c", "a"]
    assert cache.consultar_ficha("b") is None
    assert cache.consultar_ficha("a") == "ficha_a"
    assert cache.desalojos == 1

def test_no_desaloja_ficha_en_uso():
    cache = CacheFichas(2)
    cache.guardar_ficha("a", "ficha_a")
    cache.guardar_ficha("b", "ficha_b")
    cache.retener_ficha("a")
    cache.guardar_ficha("c", "ficha_c")
    assert ids_cache(cache) == ["c", "a"]
    assert cache.consultar_ficha("a") == "ficha_a"
    assert cache.consultar_ficha("b") is None
    assert cache.desalojos == 1

def test_todas_en_uso_supera_el_tope():
    cache = CacheFichas(2)
    cache.guardar_ficha("a", "ficha_a")
    cache.guardar_ficha("b", "ficha_b")
    cache.retener_ficha("a")
    cache.retener_ficha("b")
    cache.guardar_ficha("c", "ficha_c")  #nada se puede desalojar
    assert cache.lista.tamanio == 3
    assert cache.veces_sobre_tope == 1
    assert cache.maximo_alcanzado == 3
    assert cache.desalojos == 0

def test_vuelve_al_tope_al_soltar():
    cache = CacheFichas(2)
    cache.guardar_ficha("a", "ficha_a")
    cache.guardar_ficha("b", "ficha_b")
    cache.retener_ficha("a")
    cache.retener_ficha("b")
    cache.guardar_ficha("c", "ficha_c")
    cache.soltar_ficha("a")
    cache.guardar_ficha("d", "ficha_d")
    assert cache.lista.tamanio == 2
    assert ids_cache(cache) == ["d", "b"]
    assert cache.consultar_ficha("a") is None
    assert cache.consultar_ficha("c") is None
    assert cache.consultar_ficha("b") == "ficha_b"
    assert cache.consultar_ficha("d") == "ficha_d"
    assert cache.desalojos == 2

def test_capacidad_cero_no_guarda():
    cache = CacheFichas(0)
    assert cache.guardar_ficha("a", "ficha_a") is None
    assert cache.lista.tamanio == 0

def test_obtener_fichas_carga_faltantes(): #en este test se comprueba que pasa cuando la caché está vacía y se piden fichas que esta no tiene
    llamadas = []

    def cargadorFalso(lote): #fabrica fichas de ejemplo
        llamadas.append(lote)
        pares = []
        for id_ficha in lote:
            pares.append((id_ficha, "ficha_" + id_ficha))
        return pares

    cache = CacheFichas()
    resultado = cache.obtener_fichas(["a","b","c"], cargadorFalso)

    assert llamadas == [["a", "b", "c"]]
    assert cache.fallos == 3
    assert resultado == [("a", "ficha_a"), ("b", "ficha_b"), ("c", "ficha_c")]
    assert cache.consultar_ficha("a") == "ficha_a"