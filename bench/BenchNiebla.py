# Benchmark de Niebla de Guerra y Viaje Automático «ir a» (§5.3, §6.1, §6.3 Parte II).
# Mide consultas al mapa conocido, costo de exploración y tiempo de cálculo de «ir a» (< 5 ms).

import time
import random

from model.Entidades import Sala, Salida, Puerta
from model.Salas import IndiceOrdenado
from model.MapaConocido import MapaConocido, ESTADO_EXPLORADA, ESTADO_AVISTADA
from model.Dijkstra import elegirPasoViajeAutomatico


def _crearCriptaSintetica(nSalas=100, semilla=42):
    azar = random.Random(semilla)
    salas = IndiceOrdenado()
    listaSalas = []
    for i in range(1, nSalas + 1):
        s = Sala(i, "Sala %d" % i)
        salas.insertar(i, s)
        listaSalas.append(s)

    for i in range(nSalas):
        actual = listaSalas[i]
        sig = listaSalas[(i + 1) % nSalas]
        costo = azar.randint(10, 150)
        p = Puerta(False, None, None)
        actual.salidas.append(Salida("E", actual, sig.id, p, costo=costo))
        sig.salidas.append(Salida("O", sig, actual.id, p, costo=costo))

        if azar.random() < 0.4:
            destino = listaSalas[azar.randrange(nSalas)]
            if destino.id != actual.id:
                p2 = Puerta(False, None, None)
                c2 = azar.randint(10, 150)
                actual.salidas.append(Salida("N", actual, destino.id, p2, costo=c2))
                destino.salidas.append(Salida("S", destino, actual.id, p2, costo=c2))

    return salas, listaSalas


def benchConsultasMapaConocido():
    print("--- 1. Consultas al mapa conocido (explorada, avistada, memoria de puertas) ---")
    salas, listaSalas = _crearCriptaSintetica(nSalas=200, semilla=99)
    mapa = MapaConocido()

    # Explorar el 50% de las salas
    for i in range(100):
        mapa.explorarSala(listaSalas[i])

    repeticiones = 10000
    # Consulta de estado de sala
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        mapa.estadoSala(listaSalas[50].id, salas)
        mapa.estadoSala(listaSalas[150].id, salas)
    tConsultaUs = (time.perf_counter() - t0) / (repeticiones * 2) * 1000000

    # Consulta de memoria de puerta
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        mapa.puertaRecordadaAbierta(listaSalas[0].id, listaSalas[1].id)
    tPuertaUs = (time.perf_counter() - t0) / repeticiones * 1000000

    print("  Consulta estado sala:    %6.3f µs por operación" % tConsultaUs)
    print("  Consulta memoria puerta: %6.3f µs por operación" % tPuertaUs)


def benchExploracionProporcional():
    print("\n--- 2. Costo de exploración vs Tamaño del mapa conocido (§5.3) ---")
    # Probar que explorar nuevas salas cuesta proporcionalmente a las reveladas (O(1) por sala),
    # no al tamaño del mapa ya conocido
    salas, listaSalas = _crearCriptaSintetica(nSalas=500, semilla=7)

    for salasYaExploradas in [10, 50, 150, 300]:
        mapa = MapaConocido()
        for i in range(salasYaExploradas):
            mapa.explorarSala(listaSalas[i])

        # Medir tiempo de explorar 5 nuevas salas
        repeticiones = 200
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            # Clonar mapa explorando 5 salas adicionales
            for j in range(5):
                mapa.explorarSala(listaSalas[salasYaExploradas + j])
        tExplorarMs = (time.perf_counter() - t0) / repeticiones * 1000
        print("  Mapa previo: %3d salas | Explorar 5 salas nuevas: %6.3f ms" %
              (salasYaExploradas, tExplorarMs))


def benchPasoIrA():
    print("\n--- 3. Cálculo de un paso de «ir a» (§6.1 Límite: 5 ms) ---")
    salas, listaSalas = _crearCriptaSintetica(nSalas=200, semilla=123)
    mapa = MapaConocido()

    # Mapa completamente conocido (peor caso para la búsqueda en anchura/Dijkstra)
    for s in listaSalas:
        mapa.explorarSala(s)

    origen = listaSalas[0]
    destino = listaSalas[150]

    repeticiones = 50
    t0 = time.perf_counter()
    for _ in range(repeticiones):
        salida, costo = elegirPasoViajeAutomatico(origen, destino, salas, mapa)
    tPasoMs = (time.perf_counter() - t0) / repeticiones * 1000

    print("  Tiempo de cálculo de 1 paso de «ir a» (200 salas conocidas): %6.3f ms" % tPasoMs)
    print("  Cumple presupuesto (< 5 ms): %s" % ("SÍ" if tPasoMs < 5.0 else "NO"))
    assert tPasoMs < 5.0, "El paso de ir a excede el límite de 5 ms"


def main():
    benchConsultasMapaConocido()
    benchExploracionProporcional()
    benchPasoIrA()


if __name__ == "__main__":
    main()
