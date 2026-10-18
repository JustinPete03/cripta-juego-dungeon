from adapters.AlmacenFichasDisco import AlmacenFichasDisco

def testGuardarYLeerFicha(tmp_path):
    almacen = AlmacenFichasDisco(str(tmp_path))
    assert almacen.guardar("e-1", {"nombre": "Orco"}) is True
    assert almacen.leer("e-1") == {"nombre": "Orco"}

def testLeerFichaInexistente(tmp_path):
    almacen = AlmacenFichasDisco(str(tmp_path))
    assert almacen.leer("no-existe") is None

def testLeerFichaCorrupta(tmp_path):
    almacen = AlmacenFichasDisco(str(tmp_path))
    almacen.guardar("e-2", {"nombre": "Esqueleto"})
    with open(almacen.ruta("e-2"), "w", encoding="utf-8") as archivo:
        archivo.write("{ esto no es json")
    assert almacen.leer("e-2") is None

def testGuardarNoSerializableNoDejaTemporales(tmp_path):
    almacen =AlmacenFichasDisco(str(tmp_path))
    assert almacen.guardar("e-3", {"x": object()}) is False
    assert almacen.leer("e-3") is None
    assert list(tmp_path.iterdir()) == []

def testIdsConCaracteresRarosNoChocan(tmp_path):
    almacen = AlmacenFichasDisco(str(tmp_path))
    almacen.guardar("a/b", {"v": 1})
    almacen.guardar("a_b", {"v": 2})

def testSobreescribirFichaExistente(tmp_path):
    almacen = AlmacenFichasDisco(str(tmp_path))
    almacen.guardar("e-1", {"vida": 10})
    almacen.guardar("e-1", {"vida": 20})
    assert almacen.leer("e-1") == {"vida": 20}
