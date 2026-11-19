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

    for sala in listaSalas:
        for salida in sala.salidas:
            salida.destino = salas.buscar(salida.destinoId)

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


TAMANOS_PASO_IR_A = (200, 1000, 5000)
LIMITE_PASO_IR_A_MS = 5.0


def _medirPasosIrA(salas, listaSalas, cantidadPares, semilla):
    """Mide pares reproducibles con un mapa conocido completo."""
    if len(listaSalas) < 2 or cantidadPares < 1:
        raise ValueError("La medición requiere al menos dos salas y un par de prueba.")

    mapa = MapaConocido()
    for sala in listaSalas:
        mapa.explorarSala(sala)

    azar = random.Random(semilla)
    tiempoTotalMs = 0.0
    peorMs = 0.0
    paresConRuta = 0

    for _ in range(cantidadPares):
        origen, destino = azar.sample(listaSalas, 2)

        inicio = time.perf_counter()
        salida, _ = elegirPasoViajeAutomatico(origen, destino, salas, mapa)
        tiempoMs = (time.perf_counter() - inicio) * 1000

        tiempoTotalMs += tiempoMs
        peorMs = max(peorMs, tiempoMs)
        if salida is not None:
            paresConRuta += 1

    return tiempoTotalMs / cantidadPares, peorMs, paresConRuta


def medirPasosIrA(nSalas, cantidadPares, semilla):
    """Devuelve el promedio y el peor tiempo en una cripta sintética conectada."""
    salas, listaSalas = _crearCriptaSintetica(nSalas=nSalas, semilla=semilla)
    promedio, peor, paresConRuta = _medirPasosIrA(
        salas, listaSalas, cantidadPares, semilla + 1
    )

    if paresConRuta != cantidadPares:
        raise AssertionError("La búsqueda falló en una cripta sintética conectada.")

    return promedio, peor


def benchPasoIrA(tamanos=TAMANOS_PASO_IR_A, *, salasReferencia=None):
    """Mide los casos sintéticos y, si se recibe su índice, la cripta real."""
    print("\n--- 3. Cálculo de un paso de «ir a» con el mapa conocido completo ---")

    for nSalas in tamanos:
        cantidadPares = 200 if nSalas <= 1000 else 50
        promedio, peor = medirPasosIrA(nSalas, cantidadPares, semilla=123)
        print("  Sintética, %5d salas | promedio %7.3f ms | peor medido %7.3f ms"
              % (nSalas, promedio, peor))

    if salasReferencia is None:
        print("  Cripta de referencia pendiente (§6.1, límite menor de 5 ms).")
        return

    listaReferencia = [
        salasReferencia.enPosicion(i)
        for i in range(salasReferencia.cantidad())
    ]
    cantidadPares = 200
    promedio, peor, paresConRuta = _medirPasosIrA(
        salasReferencia, listaReferencia, cantidadPares, semilla=124
    )

    print("  Referencia, %5d salas | promedio %7.3f ms | peor medido %7.3f ms"
          % (len(listaReferencia), promedio, peor))
    print("  Pares con ruta: %d de %d" % (paresConRuta, cantidadPares))

    if paresConRuta == 0:
        raise AssertionError("La muestra de referencia no incluyó ningún par con ruta.")

    if peor >= LIMITE_PASO_IR_A_MS:
        raise AssertionError(
            "El peor paso medido fue %.3f ms. El límite es menor de %.1f ms."
            % (peor, LIMITE_PASO_IR_A_MS)
        )

    print("  El peor tiempo medido quedó por debajo de %.1f ms."
          % LIMITE_PASO_IR_A_MS)


def main():
    benchConsultasMapaConocido()
    benchExploracionProporcional()
    benchPasoIrA()


if __name__ == "__main__":
    main()
