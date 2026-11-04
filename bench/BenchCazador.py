# Benchmark de Terreno y Cazador (§5.1, §5.2, §6.3 Parte II).
# Compara cálculo compartido vs individual, rango pequeño vs grande, e invalidación vs recálculo.

import time
import random

from model.Entidades import Sala, Salida, Puerta, Enemigo
from model.Salas import IndiceOrdenado
from model.Dijkstra import dijkstraDesde
from model.Cazador import elegirPasoCazador
from model.Juego import Modelo
from model.Inventario import Inventario
from model.Diario import Diario
from tests.FuentePrueba import FuentePrueba


def _crearCriptaSintetica(nSalas=50, semilla=123):
    """Crea un grafo conectado determinista de nSalas."""
    azar = random.Random(semilla)
    salas = IndiceOrdenado()
    listaSalas = []
    for i in range(1, nSalas + 1):
        s = Sala(i, "Sala %d" % i)
        salas.insertar(i, s)
        listaSalas.append(s)

    # Conectar salas formando una cuadrícula o anillo con atajos
    for i in range(nSalas):
        actual = listaSalas[i]
        # Conexión al siguiente
        sig = listaSalas[(i + 1) % nSalas]
        costo = azar.randint(10, 200)
        p = Puerta(False, None, None)
        actual.salidas.append(Salida("E", actual, sig.id, p, costo=costo))
        sig.salidas.append(Salida("O", sig, actual.id, p, costo=costo))

        # Atajo aleatorio
        if azar.random() < 0.3:
            destino = listaSalas[azar.randrange(nSalas)]
            if destino.id != actual.id:
                p2 = Puerta(False, None, None)
                c2 = azar.randint(10, 200)
                actual.salidas.append(Salida("N", actual, destino.id, p2, costo=c2))
                destino.salidas.append(Salida("S", destino, actual.id, p2, costo=c2))

    return salas, listaSalas


def benchCompartidoVsIndividual():
    print("--- 1. Búsqueda de ruta del cazador: Compartido vs Individual ---")
    salas, listaSalas = _crearCriptaSintetica(nSalas=100, semilla=42)
    salaJugador = listaSalas[0]

    for cantidadCazadores in [1, 10, 30, 60]:
        azar = random.Random(42)
        cazadores = []
        for i in range(cantidadCazadores):
            salaC = listaSalas[azar.randint(1, len(listaSalas) - 1)]
            c = Enemigo("c-%d" % i, "ent_cazador", "Cazador", "cazador", 20, 20, 5, 2, 100, rango=500)
            c.sala = salaC
            cazadores.append(c)

        # Cálculo compartido: 1 Dijkstra desde el jugador para todos los cazadores
        t0 = time.perf_counter()
        repeticiones = 50
        for _ in range(repeticiones):
            dist = dijkstraDesde(salaJugador, salas)
            for c in cazadores:
                elegirPasoCazador(c, salaJugador, dist)
        tCompartido = (time.perf_counter() - t0) / repeticiones * 1000

        # Cálculo individual: 1 Dijkstra por cada cazador hacia el jugador
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            for c in cazadores:
                distInd = dijkstraDesde(c.sala, salas, rangoMax=c.rango)
                elegirPasoCazador(c, salaJugador, distInd)
        tIndividual = (time.perf_counter() - t0) / repeticiones * 1000

        print("  Cazadores: %2d | Compartido: %6.2f ms | Individual: %6.2f ms | Ganancia: %.1fx" %
              (cantidadCazadores, tCompartido, tIndividual, tIndividual / max(0.001, tCompartido)))


def benchRangoPequenoVsGrande():
    print("\n--- 2. Rango pequeño vs Rango grande ---")
    salas, listaSalas = _crearCriptaSintetica(nSalas=100, semilla=42)
    salaJugador = listaSalas[0]

    for rango in [50, 150, 500, 2000]:
        c = Enemigo("c-1", "ent_cazador", "Cazador", "cazador", 20, 20, 5, 2, 100, rango=rango)
        c.sala = listaSalas[25]

        repeticiones = 100
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            distInd = dijkstraDesde(c.sala, salas, rangoMax=c.rango)
            elegirPasoCazador(c, salaJugador, distInd)
        tMs = (time.perf_counter() - t0) / repeticiones * 1000
        print("  Rango %4d: %6.2f ms" % (rango, tMs))


def benchInvalidacionVsRecalculo():
    print("\n--- 3. Invalidación de rutas: Reutilización vs Recálculo siempre ---")
    salas, listaSalas = _crearCriptaSintetica(nSalas=100, semilla=42)
    salaJugador = listaSalas[0]

    cazadores = []
    azar = random.Random(99)
    for i in range(20):
        c = Enemigo("c-%d" % i, "ent_cazador", "Cazador", "cazador", 20, 20, 5, 2, 100, rango=1000)
        c.sala = listaSalas[azar.randint(1, len(listaSalas) - 1)]
        cazadores.append(c)

    # Escenario A: Puertas estables (no cambian). Con bandera reutilizamos distancias calculadas
    repeticiones = 100
    t0 = time.perf_counter()
    distancias = dijkstraDesde(salaJugador, salas)
    for _ in range(repeticiones):
        for c in cazadores:
            elegirPasoCazador(c, salaJugador, distancias)
    tReutilizando = (time.perf_counter() - t0) / repeticiones * 1000

    # Escenario B: Recálculo siempre en cada turno
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        dist = dijkstraDesde(salaJugador, salas)
        for c in cazadores:
            elegirPasoCazador(c, salaJugador, dist)
    tRecalculando = (time.perf_counter() - t0) / repeticiones * 1000

    print("  Puertas estables (20 cazadores):")
    print("    Reutilización: %6.3f ms" % tReutilizando)
    print("    Recálculo:     %6.3f ms (Ahorro: %.1fx)" % (tRecalculando, tRecalculando / max(0.0001, tReutilizando)))


def benchCicloEventosConCazadores():
    print("\n--- 4. Presupuesto de procesamiento: Ciclo de eventos con cazadores (§6.1 < 20 ms) ---")
    fuente = FuentePrueba(ancho=8, alto=8, semillaCripta=42, enemigosPorSala=2)
    # Reemplazar comportamientos por cazadores
    for c in fuente.contenidos:
        for e in c["enemigos"]:
            e["tipo"] = "ent_cazador"
    fichas = list(FuentePrueba().salas)  # dummy
    fichasCazador = {
        "ent_cazador": {"id": "ent_cazador", "clase": "enemigo", "nombre": "Cazador",
                        "vida_max": 20, "ataque": 5, "defensa": 2, "velocidad": 100,
                        "comportamiento": "cazador", "rango": 800, "suelta": []}
    }
    fuente.ficha = lambda tipoId: fichasCazador.get(tipoId, {"nombre": "X", "vida_max": 10, "ataque": 1, "defensa": 0, "velocidad": 100, "comportamiento": "guardian", "suelta": []})

    modelo = Modelo(fuente, semilla=1, inventario=Inventario(fuente), diario=Diario())
    modelo.iniciarPartida()

    from model.Constantes import ACC_ESPERAR
    from model.Acciones import Accion

    # Despertar varios enemigos y medir ciclos
    tiempos = []
    for _ in range(15):
        t0 = time.perf_counter()
        modelo.ejecutar(Accion(ACC_ESPERAR))
        tiempos.append((time.perf_counter() - t0) * 1000)

    tiempos.sort()
    mediana = tiempos[len(tiempos) // 2]
    peor = max(tiempos)
    print("  Ciclo con cazadores: Mediana = %.2f ms | Peor = %.2f ms (Límite: 20 ms)" % (mediana, peor))
    assert mediana < 20.0, "La mediana excede el límite de 20 ms"
    print("  Cumple presupuesto: SÍ")


def main():
    benchCompartidoVsIndividual()
    benchRangoPequenoVsGrande()
    benchInvalidacionVsRecalculo()
    benchCicloEventosConCazadores()


if __name__ == "__main__":
    main()
