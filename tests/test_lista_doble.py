from model.cache.Nodo import Nodo
from model.cache.ListaDoble import ListaDoble

def testUnSoloNodo():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    lista.agregarAlFrente(a)
    assert lista.primero is a
    assert lista.ultimo is a
    assert lista.tamanio == 1
    assert a.anterior is None
    assert a.siguiente is None

def idsHaciaAdelante(lista):
    ids = []
    actual = lista.primero
    while actual is not None:
        ids.append(actual.idFicha)
        actual = actual.siguiente
    return ids

def idsHaciaAtras(lista):
    ids = []
    actual = lista.ultimo
    while actual is not None:
        ids.append(actual.idFicha)
        actual = actual.anterior
    return ids

def listaTresNodos():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    b = Nodo("b","ficha_b")
    c = Nodo("c","ficha_c")
    lista.agregarAlFrente(a)
    lista.agregarAlFrente(b)
    lista.agregarAlFrente(c)
    return lista, [a,b,c]

def testTresNodos():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    b = Nodo("b","ficha_b")
    c = Nodo("c","ficha_c")
    lista.agregarAlFrente(a)
    lista.agregarAlFrente(b)
    lista.agregarAlFrente(c)
    assert lista.primero is c
    assert lista.ultimo is a
    assert lista.tamanio == 3
    assert idsHaciaAdelante(lista) == ["c", "b", "a"]
    assert idsHaciaAtras(lista) == ["a", "b", "c"]
    assert lista.primero.anterior is None
    assert lista.ultimo.siguiente is None

def testQuitarPrimero():
    lista, nodos = listaTresNodos()
    [a,b,c] = nodos
    lista.quitar(c)
    assert lista.primero is b
    assert lista.ultimo is a
    assert lista.tamanio == 2
    assert idsHaciaAdelante(lista) == ["b", "a"]
    assert idsHaciaAtras(lista) == ["a", "b"]
    assert b.anterior is None
    assert c.anterior is None
    assert c.siguiente is None

def testQuitarUltimo():
    lista, nodos = listaTresNodos()
    [a, b, c] = nodos
    lista.quitar(a)
    assert lista.primero is c
    assert lista.ultimo is b
    assert lista.tamanio == 2
    assert idsHaciaAdelante(lista) == ["c", "b"]
    assert idsHaciaAtras(lista) == ["b", "c"]
    assert b.siguiente is None
    assert a.anterior is None
    assert a.siguiente is None

def testQuitarNodoUnico():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    lista.agregarAlFrente(a)
    lista.quitar(a)
    assert lista.primero is None
    assert lista.ultimo is None
    assert lista.tamanio == 0
    assert idsHaciaAdelante(lista) == []
    assert idsHaciaAtras(lista) == []
    assert a.anterior is None
    assert a.siguiente is None

def testQuitarDelMedio():
    lista, nodos = listaTresNodos()
    [a, b, c] = nodos
    lista.quitar(b)
    assert lista.primero is c
    assert lista.ultimo is a
    assert lista.tamanio == 2
    assert idsHaciaAdelante(lista) == ["c", "a"]
    assert idsHaciaAtras(lista) == ["a", "c"]
    assert c.siguiente is a
    assert a.anterior is c
    assert b.anterior is None
    assert b.siguiente is None

def testMoverPrimeroAlFrente():
    lista, nodos = listaTresNodos()
    [a, b, c] = nodos
    lista.moverAlFrente(c)
    assert lista.primero is c
    assert lista.ultimo is a
    assert lista.tamanio == 3
    assert idsHaciaAdelante(lista) == ["c", "b", "a"]
    assert idsHaciaAtras(lista) == ["a", "b", "c"]
    assert c.anterior is None
    assert a.siguiente is None

def testMoverDelMedioAlFrente():
    lista, nodos = listaTresNodos()
    [a, b, c] = nodos
    lista.moverAlFrente(b)
    assert lista.primero is b
    assert lista.ultimo is a
    assert lista.tamanio == 3
    assert idsHaciaAdelante(lista) == ["b", "c", "a"]
    assert idsHaciaAtras(lista) == ["a", "c", "b"]
    assert b.anterior is None
    assert b.siguiente is c
    assert c.anterior is b
    assert c.siguiente is a
    assert a.anterior is c
    assert a.siguiente is None

def testMoverUltimoAlFrente():
    lista, nodos = listaTresNodos()
    [a, b, c] = nodos
    lista.moverAlFrente(a)
    assert lista.primero is a
    assert lista.ultimo is b
    assert lista.tamanio == 3
    assert idsHaciaAdelante(lista) == ["a", "c", "b"]
    assert idsHaciaAtras(lista) == ["b", "c", "a"]
    assert a.anterior is None
    assert b.siguiente is None

def testMoverNodoUnico():
    lista = ListaDoble()
    a = Nodo("a", "ficha_a")
    lista.agregarAlFrente(a)
    lista.moverAlFrente(a)
    assert lista.primero is a
    assert lista.ultimo is a
    assert lista.tamanio == 1
    assert a.anterior is None
    assert a.siguiente is None
