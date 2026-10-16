# Mediciones de 4.5 (inventario) y 4.6 (retroceso). Ejecutar: python -m bench.bench_retroceso
# Mide también las ALTERNATIVAS DESCARTADAS (arreglo contiguo, buffer circular, copia de estado).
import copy
import random
import sys
import threading
import time
import tracemalloc

from model.Constantes import ACC_ESPERAR
from model.Acciones import Accion
from model.Diario import Diario
from model.Entidades import ObjetoInstancia
from model.Inventario import Inventario, Nodo
from model.Juego import Modelo
from tests.FuentePrueba import FuentePrueba


def _tiempo(f, repeticiones):
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        f()
    return (time.perf_counter() - t0) / repeticiones * 1e6          # microsegundos


# ---------------------------------------------------------------- 4.5 inventario
def benchInventario():
    print("\n== 4.5 Inventario: lista doblemente enlazada vs arreglo contiguo ==")
    print("(equipar = llevar un elemento cualquiera al frente; soltar = sacar uno cualquiera)")
    print("%8s | %14s %14s | %14s %14s" % ("n", "enlazada equip", "arreglo equip", "enlazada soltar", "arreglo soltar"))
    for n in (10, 100, 1000, 10000):
        inv = Inventario(None)
        nodos = []
        for i in range(n):
            nodo = Nodo(ObjetoInstancia("x", i))
            inv._enlazarDespues(nodo, inv.cola)
            nodos.append(nodo)
        arreglo = list(range(n))
        azar = random.Random(1)
        indices = [azar.randrange(n) for _ in range(2000)]
        k = [0]

        def equipEnlazada():
            nodo = nodos[indices[k[0] % 2000]]
            k[0] += 1
            inv._desenlazar(nodo)
            inv._enlazarDespues(nodo, None)

        def equipArreglo():
            i = indices[k[0] % 2000] % len(arreglo)
            k[0] += 1
            arreglo.insert(0, arreglo.pop(i))

        def soltarEnlazada():
            nodo = nodos[indices[k[0] % 2000]]
            k[0] += 1
            inv._desenlazar(nodo)
            inv._enlazarDespues(nodo, inv.cola)          # lo devolvemos para mantener n

        def soltarArreglo():
            i = indices[k[0] % 2000] % len(arreglo)
            k[0] += 1
            arreglo.append(arreglo.pop(i))

        a = _tiempo(equipEnlazada, 2000)
        k[0] = 0
        b = _tiempo(equipArreglo, 2000)
        k[0] = 0
        c = _tiempo(soltarEnlazada, 2000)
        k[0] = 0
        d = _tiempo(soltarArreglo, 2000)
        print("%8d | %12.2f us %12.2f us | %12.2f us %12.2f us" % (n, a, b, c, d))


# ---------------------------------------------------------------- 4.6 historial
class HistorialCircular:
    """Alternativa: buffer circular de 5 intervalos (sin desplazar)."""
    CAP = 5

    def __init__(self):
        self.buf = [None] * self.CAP
        self.cima = -1
        self.cuenta = 0

    def agregar(self, intervalo):
        self.cima = (self.cima + 1) % self.CAP
        self.buf[self.cima] = intervalo
        if self.cuenta < self.CAP:
            self.cuenta += 1


def benchHistorial():
    print("\n== 4.6 Historial de 5 intervalos: vector con desplazamiento vs buffer circular ==")
    d = Diario()
    c = HistorialCircular()

    def vector():
        d.abrirIntervalo()
        d.cerrarIntervalo()

    def circular():
        c.agregar([])

    print("vector (desplaza 4):  %.3f us por intervalo" % _tiempo(vector, 200000))
    print("buffer circular:      %.3f us por intervalo" % _tiempo(circular, 200000))


def _modelo(ancho, alto, diario, fraccionActiva):
    """fraccionActiva: parte de las salas cuyos enemigos están activos (1.0 = estrés total)."""
    fuente = FuentePrueba(ancho=ancho, alto=alto, enemigosPorSala=2, vidaJugador=10 ** 9, trampas=False)
    modelo = Modelo(fuente, 1, Inventario(fuente), diario)
    modelo.iniciarPartida()
    total = modelo.salas.cantidad()
    for i in range(total):
        s = modelo.salas.enPosicion(i)
        modelo._asegurarContenido(s)
        if i < total * fraccionActiva:
            modelo._activarDormidos(s)
    return modelo


def _porAccion(m, reps=15):
    t0 = time.perf_counter()
    for _ in range(reps):
        m.ejecutar(Accion(ACC_ESPERAR))
    return (time.perf_counter() - t0) / reps * 1e6


def _kb(f):
    tracemalloc.start()
    base = tracemalloc.get_traced_memory()[0]
    resultado = f()
    kb = (tracemalloc.get_traced_memory()[0] - base) / 1024
    tracemalloc.stop()
    return kb, resultado


def _estado(m):
    return (m.salas, m.jugador, m.enemigosVivos, m.agenda._heap)


def benchRetroceso():
    print("\n== 4.6 Diario de cambios vs copia del estado completo (la copia está PROHIBIDA; solo se mide) ==")
    print("Tiempo = ciclo completo de una accion 'esperar' (incluye a los enemigos que actuan).")
    print("Memoria = lo que retienen 5 intervalos (diario) o 5 copias del estado.")
    for nombre, fraccion in (("POCOS enemigos activos (10% de las salas)", 0.1),
                             ("ESTRES: todos los enemigos activos", 1.0)):
        print("\n-- %s" % nombre)
        print("%6s %8s | %12s %12s %12s | %11s %11s" %
              ("salas", "activos", "sin diario", "con diario", "con copia", "diario KB", "copias KB"))
        for ancho, alto in ((5, 4), (10, 10), (20, 15)):
            sin = _modelo(ancho, alto, Diario(), fraccion)
            sin.diario.activo = False
            tSin = _porAccion(sin)

            con = _modelo(ancho, alto, Diario(), fraccion)
            activos = 0
            for e in con.enemigosVivos:
                if e.activo:
                    activos += 1
            tCon = _porAccion(con)

            cop = _modelo(ancho, alto, Diario(), fraccion)
            cop.diario.activo = False
            t0 = time.perf_counter()
            for _ in range(10):
                copy.deepcopy(_estado(cop))
                cop.ejecutar(Accion(ACC_ESPERAR))
            tCop = (time.perf_counter() - t0) / 10 * 1e6

            m3 = _modelo(ancho, alto, Diario(), fraccion)
            kbDiario, _ = _kb(lambda: [m3.ejecutar(Accion(ACC_ESPERAR)) for _ in range(5)])
            m4 = _modelo(ancho, alto, Diario(), fraccion)
            m4.diario.activo = False
            kbCopias, _ = _kb(lambda: [copy.deepcopy(_estado(m4)) for _ in range(5)])
            print("%6d %8d | %10.0f us %10.0f us %10.0f us | %9.0f   %9.0f" %
                  (ancho * alto, activos, tSin, tCon, tCop, kbDiario, kbCopias))


def _todo():
    benchInventario()
    benchHistorial()
    benchRetroceso()


if __name__ == "__main__":
    # deepcopy del grafo de salas es recursivo: se necesita más pila (dato en sí mismo para 4.6)
    sys.setrecursionlimit(200000)
    for megas in (512, 256, 128, 64, 32):      # Windows rechaza tamaños muy grandes
        try:
            threading.stack_size(megas * 1024 * 1024)
            break
        except ValueError:
            continue
    hilo = threading.Thread(target=_todo)
    hilo.start()
    hilo.join()