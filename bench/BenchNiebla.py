# Benchmark de Niebla de Guerra y Viaje Automático (§5.3, §6.1, §6.3).

import random
import time

from model.Dijkstra import elegirPasoViajeAutomatico
from model.Entidades import Puerta, Sala, Salida
from model.MapaConocido import MapaConocido
from model.Salas import IndiceOrdenado


TAMANOS_PASO_IR_A = (200, 1000, 5000)
LIMITE_PASO_IR_A_MS = 5.0


def _crearCriptaSintetica(nSalas=100, semilla=42):
    azar = random.Random(semilla)
    salas = IndiceOrdenado()
    listaSalas = []

    for idSala in range(1, nSalas + 1):
        sala = Sala(idSala, "Sala %d" % idSala)
        salas.insertar(idSala, sala)
        listaSalas.append(sala)

    for i, actual in enumerate(listaSalas):
        siguiente = listaSalas[(i + 1) % nSalas]
        costo = azar.randint(10, 150)
        puerta = Puerta(False, None, None)
        actual.salidas.append(Salida("E", actual, siguiente.id, puerta, costo=costo))
        siguiente.salidas.append(Salida("O", siguiente, actual.id, puerta, costo=costo))

        if azar.random() < 0.4:
            destino = listaSalas[azar.randrange(nSalas)]
            if destino is not actual:
                puertaExtra = Puerta(False, None, None)
                costoExtra = azar.randint(10, 150)
                actual.salidas.append(
                    Salida("N", actual, destino.id, puertaExtra, costo=costoExtra)
                )
                destino.salidas.append(
                    Salida("S", destino, actual.id, puertaExtra, costo=costoExtra)
                )

    for sala in listaSalas:
        for salida in sala.salidas:
            salida.destino = salas.buscar(salida.destinoId)

    return salas, listaSalas


def benchConsultasMapaConocido():
    print("--- 1. Consultas al mapa conocido ---")
    salas, listaSalas = _crearCriptaSintetica(nSalas=200, semilla=99)
    mapa = MapaConocido()

    for sala in listaSalas[:100]:
        mapa.explorarSala(sala)

    repeticiones = 10000
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        mapa.estadoSala(listaSalas[50].id, salas)
        mapa.estadoSala(listaSalas[150].id, salas)
    consultaSalaUs = (time.perf_counter() - inicio) * 1_000_000 / (2 * repeticiones)

    inicio = time.perf_counter()
    for _ in range(repeticiones):
        mapa.puertaRecordadaAbierta(listaSalas[0].id, listaSalas[1].id)
    consultaPuertaUs = (time.perf_counter() - inicio) * 1_000_000 / repeticiones

    print("  Consulta estado sala:    %6.3f µs por operación" % consultaSalaUs)
    print("  Consulta memoria puerta: %6.3f µs por operación" % consultaPuertaUs)


def benchExploracionProporcional():
    print("\n--- 2. Costo de explorar cinco salas nuevas (§5.3) ---")
    _, listaSalas = _crearCriptaSintetica(nSalas=500, semilla=7)
    repeticiones = 200

    for cantidadPrevias in (10, 50, 150, 300):
        previas = listaSalas[:cantidadPrevias]
        nuevas = listaSalas[cantidadPrevias:cantidadPrevias + 5]
        tiempoTotal = 0.0

        for _ in range(repeticiones):
            mapa = MapaConocido()
            for sala in previas:
                mapa.explorarSala(sala)

            inicio = time.perf_counter()
            for sala in nuevas:
                mapa.explorarSala(sala)
            tiempoTotal += time.perf_counter() - inicio

        promedioMs = tiempoTotal * 1000 / repeticiones
        print("  Mapa previo: %3d salas | Explorar 5 salas nuevas: %6.3f ms"
              % (cantidadPrevias, promedioMs))


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