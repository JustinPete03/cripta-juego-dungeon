import random
import pytest

from model.ordenamiento.Contador import Contador
from model.ordenamiento.Selector import analizar, seleccionar, ordenar, MAX_INSERTION_SORT_SIZE, MAX_ALMOST_SORTED
from model.ordenamiento.Insertion import insertionSort
from model.ordenamiento.Merge import mergeSort
from model.ordenamiento.Selection import selectionSort

algoritmos = [insertionSort, mergeSort]

def estaOrdenada(lista, clave=lambda x: x, descendente=False):
    for i in range(len(lista) - 1):
        a, b = clave(lista[i]), clave(lista[i + 1])
        if (a > b) if not descendente else (a < b):
            return False
    return True

def mismosElementos(entrada, salida):
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
def testOrdenaListaDesordenada(algoritmo):
    entrada = [5, 3, 9, 1, 3]
    salida = algoritmo(entrada)
    assert estaOrdenada(salida)
    assert mismosElementos(entrada, salida)
    assert entrada == [5, 3, 9, 1, 3]

@pytest.mark.parametrize("algoritmo", algoritmos)
def testListaVacia(algoritmo):
    assert algoritmo([]) == []

@pytest.mark.parametrize("algoritmo", algoritmos)
def testUnElemento(algoritmo):
    assert algoritmo([7]) == [7]

@pytest.mark.parametrize("algoritmo", algoritmos)
def testTodosIguales(algoritmo):
    entrada = [4, 4, 4, 4]
    salida = algoritmo(entrada)
    assert estaOrdenada(salida)
    assert mismosElementos(entrada, salida)

@pytest.mark.parametrize("algoritmo", algoritmos)
def testYaOrdenada(algoritmo):
    entrada = [1, 2, 3, 4, 5]
    assert algoritmo(entrada) == entrada

@pytest.mark.parametrize("algoritmo", algoritmos)
def testInvertida(algoritmo):
    assert algoritmo([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

@pytest.mark.parametrize("algoritmo", algoritmos)
def testDescendente(algoritmo):
    entrada = [3, 1, 2]
    salida = algoritmo(entrada, descendente=True)
    assert salida == [3, 2, 1]
    assert estaOrdenada(salida, descendente=True)

@pytest.mark.parametrize("algoritmo", algoritmos)
def testConClave(algoritmo):
    entrada = [("b", 2), ("a", 3), ("c", 1)]
    salida = algoritmo(entrada, clave=lambda par: par[1])
    assert estaOrdenada(salida, clave=lambda par: par[1])
    assert mismosElementos(entrada, salida)

@pytest.mark.parametrize("algoritmo", algoritmos)
def testIterableNoLista(algoritmo):
    assert algoritmo((3, 1, 2)) == [1, 2, 3]

@pytest.mark.parametrize("algoritmo", algoritmos)
def testEstabilidadAscendente(algoritmo):
    entrada = [(2, 0), (1, 1), (2, 2), (1, 3), (2, 4)]
    salida = algoritmo(entrada, clave=lambda par: par[0])
    assert salida == [(1, 1), (1, 3), (2, 0), (2, 2), (2, 4)]

@pytest.mark.parametrize("algoritmo", algoritmos)
def testEstabilidadDescendente(algoritmo):
    entrada = [(2, 0), (1, 1), (2, 2), (1, 3), (2, 4)]
    salida = algoritmo(entrada, clave=lambda par: par[0], descendente=True)
    assert salida == [(2, 0), (2, 2), (2, 4), (1, 1), (1, 3)]

def testInsertionListaOrdenadaHaceNMenos1Comparaciones():
    contador = Contador()
    insertionSort([1, 2, 3, 4, 5, 6], contador=contador)
    assert contador.comparaciones == 5

def testInsertionYMergeCoinciden():
    azar = random.Random(2026)
    for n in (0, 1, 5, 20, 50, 200):
        entrada = [(azar.randint(0, 9), i) for i in range(n)]
        a = insertionSort(entrada, clave=lambda par: par[0])
        b = mergeSort(entrada, clave=lambda par: par[0])
        assert a == b

def testSeleccionarNPequenoUsaInsercion():
    assert seleccionar({"n": 5, "descensos": 4}) is insertionSort

def testSeleccionarGrandeDesordenadoUsaMerge():
    n = MAX_INSERTION_SORT_SIZE + 100
    assert seleccionar({"n": n, "descensos": n // 2}) is mergeSort

def testSeleccionarGrandeCasiOrdenadoUsaInsercion():
    n = MAX_INSERTION_SORT_SIZE + 100
    assert seleccionar({"n": n, "descensos": 3}) is insertionSort

def testAnalizarCuentaDescensos():
    pares = [(3, 3), (1, 1), (2, 2), (2, 2)]
    props = analizar(pares)
    assert props["n"] == 4
    assert props["descensos"] == 1

def testOrdenarPublicoOrdena():
    assert ordenar([5, 3, 9, 1, 3]) == [1, 3, 3, 5, 9]

def testSelectionOrdena():
    assert selectionSort([3, 1, 2]) == [1, 2, 3]

def testSelectionOrdenaPeroNoEsEstable():
    entrada = [(2, 0), (1, 1), (2, 2), (1, 3), (2, 4)]
    salida = selectionSort(entrada, clave=lambda par: par[0])
    assert estaOrdenada(salida, clave=lambda par: par[0])
    assert salida != [(1, 1), (1, 3), (2, 0), (2, 2), (2, 4)]

def testSelectionSiempreHaceNPorNMenos1Sobre2Comparaciones():
    contador = Contador()
    selectionSort([1, 2, 3, 4, 5, 6], contador=contador)
    assert contador.comparaciones == 15

def testSeleccionarPocosDescensosPeroNGrandeUsaMerge():
    n = MAX_ALMOST_SORTED * 4
    assert seleccionar({"n": n, "descensos": 1}) is mergeSort

def testSeleccionarOrdenadaGrandeUsaInsercion():
    assert seleccionar({"n": 5000, "descensos": 0}) is insertionSort

def testOrdenarMitadesIntercambiadasNoEsCuadratico():
    n = 2048
    entrada = list(range(n // 2, n)) + list(range(n // 2))
    contador = Contador()
    salida = ordenar(entrada, contador=contador)
    assert salida == list(range(n))
    assert contador.comparaciones < 2 * n * 11

def testOrdenarOrdenadaGrandeEsLineal():
    n = 2048
    contador = Contador()
    ordenar(list(range(n)), contador=contador)
    assert contador.comparaciones <= 3 * n

def testOrdenarNoModificaLaEntrada():
    entrada = [3, 1, 2]
    ordenar(entrada)
    assert entrada == [3, 1, 2]

def testOrdenarCuentaLasComparacionesDelAnalisis():
    contador = Contador()
    ordenar([1, 2, 3, 4], contador=contador)
    assert contador.comparaciones == 6

def testOrdenarAceptaParametroCostosa():
    datos = ["pocion", "espada", "anillo"]
    assert ordenar(datos, costosa=True) == ["anillo", "espada", "pocion"]
    assert ordenar(datos, costosa=False) == ["anillo", "espada", "pocion"]

def testSeleccionarComparacionCostosaBajaElTope():
    propiedades = {"n": 12, "descensos": 12}
    assert seleccionar(propiedades, costosa=False) is insertionSort
    assert seleccionar(propiedades, costosa=True) is mergeSort
    assert seleccionar({"n": 8, "descensos": 8}, costosa=True) is insertionSort