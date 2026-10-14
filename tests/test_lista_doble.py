from model.cache.nodo import Nodo
from model.cache.lista_doble import ListaDoble

def test_un_solo_nodo():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    lista.agregar_al_frente(a)
    assert lista.primero is a
    assert lista.ultimo is a
    assert lista.tamanio == 1
    assert a.anterior is None
    assert a.siguiente is None

def ids_hacia_adelante(lista):
    ids = []
    actual = lista.primero
    while actual is not None:
        ids.append(actual.idFicha)
        actual = actual.siguiente
    return ids

def ids_hacia_atras(lista):
    ids = []
    actual = lista.ultimo
    while actual is not None:
        ids.append(actual.idFicha)
        actual = actual.anterior
    return ids

def lista_tres_nodos():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    b = Nodo("b","ficha_b")
    c = Nodo("c","ficha_c")
    lista.agregar_al_frente(a)
    lista.agregar_al_frente(b)
    lista.agregar_al_frente(c)
    return lista, [a,b,c]


def test_tres_nodos():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    b = Nodo("b","ficha_b")
    c = Nodo("c","ficha_c")
    lista.agregar_al_frente(a)
    lista.agregar_al_frente(b)
    lista.agregar_al_frente(c)
    assert lista.primero is c
    assert lista.ultimo is a
    assert lista.tamanio == 3
    assert ids_hacia_adelante(lista) == ["c","b","a"]
    assert ids_hacia_atras(lista) == ["a","b","c"]
    assert lista.primero.anterior is None
    assert lista.ultimo.siguiente is None

def test_quitar_primero():
    lista, nodos = lista_tres_nodos()
    [a,b,c] = nodos
    lista.quitar(c)
    assert lista.primero is b
    assert lista.ultimo is a
    assert lista.tamanio == 2
    assert ids_hacia_adelante(lista) == ["b","a"]
    assert ids_hacia_atras(lista) == ["a","b"]
    assert b.anterior is None
    assert c.anterior is None
    assert c.siguiente is None

def test_quitar_ultimo():
    lista, nodos = lista_tres_nodos()
    [a, b, c] = nodos
    lista.quitar(a)
    assert lista.primero is c
    assert lista.ultimo is b
    assert lista.tamanio == 2
    assert ids_hacia_adelante(lista) == ["c", "b"]
    assert ids_hacia_atras(lista) == ["b", "c"]
    assert b.siguiente is None
    assert a.anterior is None
    assert a.siguiente is None

def test_quitar_nodo_unico():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    lista.agregar_al_frente(a)
    lista.quitar(a)
    assert lista.primero is None
    assert lista.ultimo is None
    assert lista.tamanio == 0
    assert ids_hacia_adelante(lista) == []
    assert ids_hacia_atras(lista) == []
    assert a.anterior is None
    assert a.siguiente is None

def test_quitar_del_medio():
    lista, nodos = lista_tres_nodos()
    [a, b, c] = nodos
    lista.quitar(b)
    assert lista.primero is c
    assert lista.ultimo is a
    assert lista.tamanio == 2
    assert ids_hacia_adelante(lista) == ["c","a"]
    assert ids_hacia_atras(lista) == ["a","c"]
    assert c.siguiente is a
    assert a.anterior is c
    assert b.anterior is None
    assert b.siguiente is None

def test_mover_primero_al_frente():
    lista, nodos = lista_tres_nodos()
    [a, b, c] = nodos
    lista.mover_al_frente(c)
    assert lista.primero is c
    assert lista.ultimo is a
    assert lista.tamanio == 3
    assert ids_hacia_adelante(lista) == ["c", "b", "a"]
    assert ids_hacia_atras(lista) == ["a", "b", "c"]
    assert c.anterior is None
    assert a.siguiente is None

def test_mover_del_medio_al_frente():
    lista, nodos = lista_tres_nodos()
    [a, b, c] = nodos
    lista.mover_al_frente(b)
    assert lista.primero is b
    assert lista.ultimo is a
    assert lista.tamanio == 3
    assert ids_hacia_adelante(lista) == ["b", "c", "a"]
    assert ids_hacia_atras(lista) == ["a", "c", "b"]
    assert b.anterior is None
    assert b.siguiente is c
    assert c.anterior is b
    assert c.siguiente is a
    assert a.anterior is c
    assert a.siguiente is None

def test_mover_ultimo_al_frente():
    lista, nodos = lista_tres_nodos()
    [a, b, c] = nodos
    lista.mover_al_frente(a)
    assert lista.primero is a
    assert lista.ultimo is b
    assert lista.tamanio == 3
    assert ids_hacia_adelante(lista) == ["a", "c", "b"]
    assert ids_hacia_atras(lista) == ["b", "c", "a"]
    assert a.anterior is None
    assert b.siguiente is None

def test_mover_nodo_unico():
    lista = ListaDoble()
    a = Nodo("a", "ficha_a")
    lista.agregar_al_frente(a)
    lista.mover_al_frente(a)
    assert lista.primero is a
    assert lista.ultimo is a
    assert lista.tamanio == 1
    assert a.anterior is None
    assert a.siguiente is None
