from model.cache.nodo import Nodo
from model.cache.lista_doble import ListaDoble

def test_un_solo_nodo():
    lista = ListaDoble()
    a = Nodo("a","ficha_a")
    lista.agregar_al_frente(a)
    assert lista.primero is a
    assert lista.ultimo is a
    assert lista.tamanio == 1

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