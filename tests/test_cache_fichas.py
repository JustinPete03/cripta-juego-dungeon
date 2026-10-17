from model.cache.CacheFichas import CacheFichas
from model.cache.AlmacenFichas import AlmacenFichas

def idsCache(cache):
    ids = []
    actual = cache.lista.primero
    while actual is not None:
        ids.append(actual.idFicha)
        actual = actual.siguiente
    return ids

def testEstadoInicial():
    cache = CacheFichas()
    assert cache.capacidad == 25
    assert cache.lista.tamanio == 0
    assert cache.aciertos == 0
    assert cache.fallos == 0
    assert cache.desalojos == 0
    assert cache.vecesSobreTope == 0
    assert cache.maximoAlcanzado == 0

def testAciertoYFallo():
    cache = CacheFichas()
    cache.guardarFicha("a", "ficha_a")
    assert cache.consultarFicha("a") == "ficha_a"
    assert cache.consultarFicha("z") is None
    assert cache.aciertos == 1
    assert cache.fallos == 1

def testGuardarExistenteNoDuplica():
    cache = CacheFichas()
    cache.guardarFicha("a", "v1")
    cache.guardarFicha("a", "v2")
    assert cache.lista.tamanio == 1
    assert cache.consultarFicha("a") == "v2"

def testConsultarMueveAlFrente():
    cache = CacheFichas(3)
    cache.guardarFicha("a", "ficha_a")
    cache.guardarFicha("b", "ficha_b")
    cache.guardarFicha("c", "ficha_c")
    assert idsCache(cache) == ["c", "b", "a"]
    cache.consultarFicha("a")
    assert idsCache(cache) == ["a", "c", "b"]

def testDesalojaElMenosReciente():
    cache = CacheFichas(2)
    cache.guardarFicha("a", "ficha_a")
    cache.guardarFicha("b", "ficha_b")
    cache.consultarFicha("a")
    cache.guardarFicha("c", "ficha_c")
    assert idsCache(cache) == ["c", "a"]
    assert cache.consultarFicha("b") is None
    assert cache.consultarFicha("a") == "ficha_a"
    assert cache.desalojos == 1

def testNoDesalojaFichaEnUso():
    cache = CacheFichas(2)
    cache.guardarFicha("a", "ficha_a")
    cache.guardarFicha("b", "ficha_b")
    cache.retenerFicha("a")
    cache.guardarFicha("c", "ficha_c")
    assert idsCache(cache) == ["c", "a"]
    assert cache.consultarFicha("a") == "ficha_a"
    assert cache.consultarFicha("b") is None
    assert cache.desalojos == 1

def testTodasEnUsoSuperaElTope():
    cache = CacheFichas(2)
    cache.guardarFicha("a", "ficha_a")
    cache.guardarFicha("b", "ficha_b")
    cache.retenerFicha("a")
    cache.retenerFicha("b")
    cache.guardarFicha("c", "ficha_c")  #nada se puede desalojar
    assert cache.lista.tamanio == 3
    assert cache.vecesSobreTope == 1
    assert cache.maximoAlcanzado == 3
    assert cache.desalojos == 0

def testVuelveAlTopeAlSoltar():
    cache = CacheFichas(2)
    cache.guardarFicha("a", "ficha_a")
    cache.guardarFicha("b", "ficha_b")
    cache.retenerFicha("a")
    cache.retenerFicha("b")
    cache.guardarFicha("c", "ficha_c")
    cache.soltarFicha("a")
    cache.guardarFicha("d", "ficha_d")
    assert cache.lista.tamanio == 2
    assert idsCache(cache) == ["d", "b"]
    assert cache.consultarFicha("a") is None
    assert cache.consultarFicha("c") is None
    assert cache.consultarFicha("b") == "ficha_b"
    assert cache.consultarFicha("d") == "ficha_d"
    assert cache.desalojos == 2

def testCapacidadCeroNoGuarda():
    cache = CacheFichas(0)
    assert cache.guardarFicha("a", "ficha_a") is None
    assert cache.lista.tamanio == 0

def testObtenerFichasCargaFaltantes(): #en este test se comprueba que pasa cuando la caché está vacía y se piden fichas que esta no tiene
    llamadas = []

    def cargadorFalso(lote): #fabrica fichas de ejemplo
        llamadas.append(lote)
        pares = []
        for idFicha in lote:
            pares.append((idFicha, "ficha_" + idFicha))
        return pares

    cache = CacheFichas()
    resultado = cache.obtenerFichas(["a","b","c"], cargadorFalso)

    assert llamadas == [["a", "b", "c"]]
    assert cache.fallos == 3
    assert resultado == [("a", "ficha_a"), ("b", "ficha_b"), ("c", "ficha_c")]
    assert cache.consultarFicha("a") == "ficha_a"

class AlmacenFalso(AlmacenFichas):
    def __init__(self):
        self.guardadas = []

    def guardar(self, idFicha, ficha):
        self.guardadas.append((idFicha, ficha))
        return True

    def leer(self, idFicha):
        for id, ficha in self.guardadas:
            if id == idFicha:
                return ficha
        return None

def testDesalojadaLlegaAlAlmacen():
    almacen = AlmacenFalso()
    cache = CacheFichas(capacidad=2, almacen=almacen)
    cache.guardarFicha("a", "ficha_a")
    cache.guardarFicha("b", "ficha_b")
    cache.guardarFicha("c", "ficha_c")
    assert almacen.leer("a") == "ficha_a"

def testRecuperaDeDiscoSinLlamarAlCargador():
    almacen = AlmacenFalso()
    cache = CacheFichas(capacidad=2, almacen=almacen)
    cache.guardarFicha("a", "ficha_a")
    cache.guardarFicha("b", "ficha_b")
    cache.guardarFicha("c", "ficha_c")
    llamadas = []

    def cargadorFalso(lote):
        llamadas.append(lote)
        return []

    resultado = cache.obtenerFichas(["a"], cargadorFalso)
    assert resultado == [("a", "ficha_a")]
    assert llamadas == []
    assert cache.aciertosDisco == 1
    assert cache.llamadasRed == 0

def testFichaNoEstaEnDiscoVaAlCargador():
    cache = CacheFichas(capacidad=2, almacen=AlmacenFalso())
    llamadas = []

    def cargadorFalso(lote):
        llamadas.append(lote)
        return [(idFicha, "ficha_" + idFicha) for idFicha in lote]

    cache.obtenerFichas(["x"], cargadorFalso)
    assert llamadas == [["x"]]
    assert cache.aciertosDisco == 0
    assert cache.llamadasRed == 1

def testSinAlmacenElComportamientoNoCambia():
    cache = CacheFichas(capacidad=1)
    cache.guardarFicha("a", "ficha_a")
    cache.guardarFicha("b", "ficha_b")
    llamadas = []

    def cargadorFalso(lote):
        llamadas.append(lote)
        return [(idFicha, "ficha_" + idFicha) for idFicha in lote]

    cache.obtenerFichas(["a"], cargadorFalso)
    assert llamadas == [["a"]]
    assert cache.aciertosDisco == 0