#Mediciones de Justin para el Documento de Decisiones (4.1, 4.7, 4.8).

#Se integra al bench de Keilor: correr, llama reportar
#Cada sección mide la estructura elegida Y la alternativa descartada, con la misma carga.

import random
import time

from model.Agenda import Agenda
from model.Bitacora import BitacoraCircular
from model.Entidades import Sala, Salida, Puerta
from model.Rastro import elegirDestinoRastreador


def _tiempo(funcion):
    t = time.perf_counter()
    funcion()
    return time.perf_counter() - t


# 4.1 agenda
def _agendaHeap(n, operaciones):
    azar = random.Random(1)
    agenda = Agenda()
    for _ in range(n):
        agenda.programar(azar.randrange(1000), 1, None)
    for _ in range(operaciones):
        evento = agenda.proximo()
        agenda.programar(evento.tiempo + 1 + azar.randrange(150), 1, None)


def _agendaEscaneoLineal(n, operaciones):
    #Alternativa descartada: lista sin orden, buscar el mínimo recorriendo.
    azar = random.Random(1)
    lista = []
    seq = 0
    for _ in range(n):
        lista.append((azar.randrange(1000), seq))
        seq += 1
    for _ in range(operaciones):
        mejor = 0
        for i in range(1, len(lista)):
            if lista[i] < lista[mejor]:
                mejor = i
        tiempo = lista[mejor][0]
        lista[mejor] = lista[-1]
        lista.pop()
        lista.append((tiempo + 1 + azar.randrange(150), seq))
        seq += 1


def _agendaListaOrdenada(n, operaciones):
    #Alternativa descartada: lista siempre ordenada; sacar el primero e insertar en su lugar.
    azar = random.Random(1)
    lista = []
    seq = 0

    def insertar(elemento):
        bajo = 0
        alto = len(lista)
        while bajo < alto:
            medio = (bajo + alto) // 2
            if lista[medio] < elemento:
                bajo = medio + 1
            else:
                alto = medio
        lista.insert(bajo, elemento)

    for _ in range(n):
        insertar((azar.randrange(1000), seq))
        seq += 1
    for _ in range(operaciones):
        tiempo = lista.pop(0)[0]
        insertar((tiempo + 1 + azar.randrange(150), seq))
        seq += 1


def _benchAgenda(reportar):
    # Carga medida: sacar el próximo y reprogramar al actor, que es lo que hace el motor con cada
    # enemigo activo. La lista ordenada gana por debajo de ~1.300 eventos pendientes porque sus
    # desplazamientos son memmove en C contra ~log2(n) iteraciones de Python en el montículo; a
    # partir de ahí el montículo manda y la lista crece lineal con la ventana de pendientes.
    # El juego puede pasar de esa ventana (600 enemigos del test de sección 5.2 más efectos,
    # trampas y cierres automáticos), y la cota del montículo no depende de cuántos haya.
    for n in (100, 500, 1500, 5000):
        ops = 20000 if n <= 500 else 4000
        reportar("agenda", "heap propio, n=%d, %d ops" % (n, ops), _tiempo(lambda: _agendaHeap(n, ops)))
        reportar("agenda", "ALT lista ordenada, n=%d, %d ops" % (n, ops),
                 _tiempo(lambda: _agendaListaOrdenada(n, ops)))
        reportar("agenda", "ALT escaneo lineal, n=%d, %d ops" % (n, ops),
                 _tiempo(lambda: _agendaEscaneoLineal(n, ops)))


# 4.7 rastro
def _armarSalas(cantidad):
    salas = []
    for i in range(cantidad):
        s = Sala(i + 1, "s")
        s.rastro = (i * 7) % 900
        salas.append(s)
    for i in range(cantidad):
        for k in range(4):
            vecina = salas[(i * 3 + k * 5 + 1) % cantidad]
            salida = Salida("NSEO"[k], salas[i], vecina.id, Puerta(False, None, None))
            salida.destino = vecina
            salas[i].salidas.append(salida)
    return salas


def _rastroVecinas(salas, consultas):
    for q in range(consultas):
        elegirDestinoRastreador(salas[q % len(salas)], 1000)


def _rastroTodas(salas, consultas):
    #Alternativa descartada: recorrer todas las salas buscando el rastro más fresco.
    for q in range(consultas):
        mejor = None
        for s in salas:
            if s.rastro >= 0 and 1000 - s.rastro < 400:
                if mejor is None or s.rastro > mejor.rastro:
                    mejor = s


def _benchRastro(reportar):
    for cantidad in (100, 2000):
        salas = _armarSalas(cantidad)
        consultas = 2000
        reportar("rastro", "solo vecinas, %d salas, %d decisiones" % (cantidad, consultas),
                 _tiempo(lambda: _rastroVecinas(salas, consultas)))
        reportar("rastro", "ALT todas las salas, %d salas, %d decisiones" % (cantidad, consultas),
                 _tiempo(lambda: _rastroTodas(salas, consultas)))


# 4.8 bitácora
def _bitacoraCircular(mensajes):
    b = BitacoraCircular(20)
    for i in range(mensajes):
        b.agregar("mensaje %d" % i)
    b.ultimos()


def _bitacoraPop(mensajes):
    #Alternativa descartada: lista de 20 donde se desplaza con pop(0).
    lista = []
    for i in range(mensajes):
        lista.append("mensaje %d" % i)
        if len(lista) > 20:
            lista.pop(0)


def _bitacoraCrece(mensajes):
        ##Alternativa descartada:
    lista = []
    for i in range(mensajes):
        lista.append("mensaje %d" % i)
    return lista[-20:]


def _benchBitacora(reportar):
    n = 200000
    reportar("bitacora", "circular 20, %d mensajes" % n, _tiempo(lambda: _bitacoraCircular(n)))
    reportar("bitacora", "ALT lista con pop, %d mensajes" % n, _tiempo(lambda: _bitacoraPop(n)))
    reportar("bitacora", "ALT lista que crece, %d mensajes" % n, _tiempo(lambda: _bitacoraCrece(n)))


def correr(reportar):
    _benchAgenda(reportar)
    _benchRastro(reportar)
    _benchBitacora(reportar)


if __name__ == "__main__":
    def imprimir(subsistema, descripcion, segundos):
        print("%-9s %-48s %9.2f ms" % (subsistema, descripcion, segundos * 1000))
    correr(imprimir)
