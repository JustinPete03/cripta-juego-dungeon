import random
import pytest

from model.ordenamiento.contador import Contador
from model.ordenamiento.selector import analizar, seleccionar, ordenar, MAX_INSERTION_SORT_SIZE, MAX_ALMOST_SORTED
from model.ordenamiento.insertion import insertion_sort
from model.ordenamiento.merge import merge_sort
from model.ordenamiento.selection import selection_sort

algoritmos = [insertion_sort, merge_sort]

def esta_ordenada(lista, clave=lambda x: x, descendente=False):
    for i in range(len(lista) - 1):
        a, b = clave(lista[i]), clave(lista[i + 1])
        if (a > b) if not descendente else (a < b):
            return False
    return True

def mismos_elementos(entrada, salida):
    if len(entrada) != len(salida):
        return False
    pendientes = list(salida)
    for x in entrada:
        if x in pendientes:
            pendientes.remove(x)
        else:
            return False
    return True

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_ordena_lista_desordenada(algoritmo):
    entrada = [5, 3, 9, 1, 3]
    salida = algoritmo(entrada)
    assert esta_ordenada(salida)
    assert mismos_elementos(entrada, salida)
    assert entrada == [5, 3, 9, 1, 3]

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_lista_vacia(algoritmo):
    assert algoritmo([]) == []

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_un_elemento(algoritmo):
    assert algoritmo([7]) == [7]

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_todos_iguales(algoritmo):
    entrada = [4, 4, 4, 4]
    salida = algoritmo(entrada)
    assert esta_ordenada(salida)
    assert mismos_elementos(entrada, salida)

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_ya_ordenada(algoritmo):
    entrada = [1, 2, 3, 4, 5]
    assert algoritmo(entrada) == entrada

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_invertida(algoritmo):
    assert algoritmo([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_descendente(algoritmo):
    entrada = [3, 1, 2]
    salida = algoritmo(entrada, descendente=True)
    assert salida == [3, 2, 1]
    assert esta_ordenada(salida, descendente=True)

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_con_clave(algoritmo):
    entrada = [("b", 2), ("a", 3), ("c", 1)]
    salida = algoritmo(entrada, clave=lambda par: par[1])
    assert esta_ordenada(salida, clave=lambda par: par[1])
    assert mismos_elementos(entrada, salida)

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_iterable_no_lista(algoritmo):
    assert algoritmo((3, 1, 2)) == [1, 2, 3]

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_estabilidad_ascendente(algoritmo):
    entrada = [(2, 0), (1, 1), (2, 2), (1, 3), (2, 4)]
    salida = algoritmo(entrada, clave=lambda par: par[0])
    assert salida == [(1, 1), (1, 3), (2, 0), (2, 2), (2, 4)]

@pytest.mark.parametrize("algoritmo", algoritmos)
def test_estabilidad_descendente(algoritmo):
    entrada = [(2, 0), (1, 1), (2, 2), (1, 3), (2, 4)]
    salida = algoritmo(entrada, clave=lambda par: par[0], descendente=True)
    assert salida == [(2, 0), (2, 2), (2, 4), (1, 1), (1, 3)]

def test_insertion_lista_ordenada_hace_n_menos_1_comparaciones():
    contador = Contador()
    insertion_sort([1, 2, 3, 4, 5, 6], contador=contador)
    assert contador.comparaciones == 5

def test_insertion_y_merge_coinciden():
    azar = random.Random(2026)
    for n in (0, 1, 5, 20, 50, 200):
        entrada = [(azar.randint(0, 9), i) for i in range(n)]
        a = insertion_sort(entrada, clave=lambda par: par[0])
        b = merge_sort(entrada, clave=lambda par: par[0])
        assert a == b

def test_seleccionar_n_pequeno_usa_insercion():
    assert seleccionar({"n": 5, "descensos": 4}) is insertion_sort

def test_seleccionar_grande_desordenado_usa_merge():
    n = MAX_INSERTION_SORT_SIZE + 100
    assert seleccionar({"n": n, "descensos": n // 2}) is merge_sort

def test_seleccionar_grande_casi_ordenado_usa_insercion():
    n = MAX_INSERTION_SORT_SIZE + 100
    assert seleccionar({"n": n, "descensos": 3}) is insertion_sort

def test_analizar_cuenta_descensos():
    pares = [(3, 3), (1, 1), (2, 2), (2, 2)]
    props = analizar(pares)
    assert props["n"] == 4
    assert props["descensos"] == 1

def test_ordenar_publico_ordena():
    assert ordenar([5, 3, 9, 1, 3]) == [1, 3, 3, 5, 9]

def test_selection_ordena():
    assert selection_sort([3, 1, 2]) == [1, 2, 3]

def test_selection_ordena_pero_no_es_estable():
    entrada = [(2, 0), (1, 1), (2, 2), (1, 3), (2, 4)]
    salida = selection_sort(entrada, clave=lambda par: par[0])
    assert esta_ordenada(salida, clave=lambda par: par[0])
    assert salida != [(1, 1), (1, 3), (2, 0), (2, 2), (2, 4)]

def test_selection_siempre_hace_n_por_n_menos_1_sobre_2_comparaciones():
    contador = Contador()
    selection_sort([1, 2, 3, 4, 5, 6], contador=contador)
    assert contador.comparaciones == 15

def test_seleccionar_pocos_descensos_pero_n_grande_usa_merge():
    n = MAX_ALMOST_SORTED * 4
    assert seleccionar({"n": n, "descensos": 1}) is merge_sort

def test_seleccionar_ordenada_grande_usa_insercion():
    assert seleccionar({"n": 5000, "descensos": 0}) is insertion_sort

def test_ordenar_mitades_intercambiadas_no_es_cuadratico():
    n = 2048
    entrada = list(range(n // 2, n)) + list(range(n // 2))
    contador = Contador()
    salida = ordenar(entrada, contador=contador)
    assert salida == list(range(n))
    assert contador.comparaciones < 2 * n * 11

def test_ordenar_ordenada_grande_es_lineal():
    n = 2048
    contador = Contador()
    ordenar(list(range(n)), contador=contador)
    assert contador.comparaciones <= 3 * n

def test_ordenar_no_modifica_la_entrada():
    entrada = [3, 1, 2]
    ordenar(entrada)
    assert entrada == [3, 1, 2]

def test_ordenar_cuenta_las_comparaciones_del_analisis():
    contador = Contador()
    ordenar([1, 2, 3, 4], contador=contador)
    assert contador.comparaciones == 6