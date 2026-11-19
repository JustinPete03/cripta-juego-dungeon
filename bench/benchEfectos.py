# Bench de la seccion 4.1: cuanto cuesta cancelar un evento pendiente de la agenda.
#
# Decision medida: la agenda entrega el Evento y cancelar es marcarlo, O(1).
# Alternativa descartada: la agenda solo guarda datos y, para cancelar, hay que
# recorrer el monticulo buscando el evento, O(n).
#
# Las dos variantes hacen el MISMO trabajo (cancelar el evento pendiente y
# programar el siguiente, que es lo que hace el motor al reprogramar un efecto o
# la proxima accion de un enemigo); solo cambia como se localiza el evento.

import random
import statistics
import time

from model.Agenda import Agenda

MUESTRAS = 51
OPERACIONES_POR_TAMANO = {100: 500, 1000: 200, 10000: 50}


def _llenar(n, semilla):
    agenda = Agenda()
    azar = random.Random(semilla)
    eventos = []
    for _ in range(n):
        eventos.append(agenda.programar(azar.randrange(100000), 1, None))
    return agenda, eventos


def _reprogramarDirecto(agenda, eventos, indices):
    for i in indices:
        agenda.cancelar(eventos[i])
        agenda.programar(eventos[i].tiempo + 100, 1, None)


def _buscarYReprogramar(agenda, eventos, indices):
    monticulo = agenda._heap
    for i in indices:
        objetivo = eventos[i]
        for posicion in range(len(monticulo)):
            if monticulo[posicion][-1] is objetivo:
                objetivo.cancelado = True
                break
        agenda.programar(objetivo.tiempo + 100, 1, None)


def _microsPorOperacion(n, indices, funcion):
    tiempos = []
    for _ in range(MUESTRAS):
        agenda, eventos = _llenar(n, 7)
        inicio = time.perf_counter()
        funcion(agenda, eventos, indices)
        tiempos.append((time.perf_counter() - inicio) / len(indices) * 1e6)
    return statistics.median(tiempos)


def medir(n):
    azar = random.Random(n)
    indices = azar.sample(range(n), min(OPERACIONES_POR_TAMANO.get(n, 200), n))
    directo = _microsPorOperacion(n, indices, _reprogramarDirecto)
    buscando = _microsPorOperacion(n, indices, _buscarYReprogramar)
    print("n=%6d | cancelar directo=%8.2f us  buscando=%9.2f us   (mediana de %d)"
          % (n, directo, buscando, MUESTRAS))


def ejecutar(tamanos=(100, 1000, 10000)):
    for n in tamanos:
        medir(n)


def main():
    ejecutar()


if __name__ == "__main__":
    main()
