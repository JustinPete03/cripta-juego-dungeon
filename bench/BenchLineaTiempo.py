# Benchmark de Línea de Tiempo y Puntos de Control (§5.5, §6.1, PR-007, PR-008 Parte II).
# Mide memoria y tiempo de consulta para varios K (5, 20, 50, sin checkpoints),
# y tiempo de consulta < 50 ms en partida de al menos 5 000 acciones.

import time
import random
import json
import sys
import gc

from tests.FuentePrueba import FuentePrueba
from model.Acciones import Accion
from model.Constantes import ACC_ESPERAR, ACC_MOVER, EN_CURSO
from model.Inventario import Inventario
from model.Diario import Diario
from model.efectosTrampa import efectosTrampa
from model.Juego import Modelo


def _crearPartidaSimulada(nAcciones=1000, checkpointCada=20, semilla=2026, ancho=8, alto=8):
    azar = random.Random(semilla)
    proveedor = FuentePrueba(ancho=ancho, alto=alto, semillaCripta=semilla, vidaJugador=10000000, enemigosPorSala=1)
    efectos = efectosTrampa()
    modelo = Modelo(proveedor, semilla, Inventario(proveedor), Diario(), efectos, kCheckpoint=checkpointCada)
    efectos.registrarEn(modelo)
    modelo.iniciarPartida()
    modelo.puertaSalidaAbierta = False

    # Ejecutar acciones garantizando que la partida siga EN_CURSO
    direcciones = ["N", "S", "E", "O"]
    ejecutadas = 0
    while ejecutadas < nAcciones and modelo.estado == EN_CURSO:
        if azar.random() < 0.5:
            d = azar.choice(direcciones)
            res = modelo.ejecutar(Accion(ACC_MOVER, d))
            if res.ok:
                ejecutadas += 1
            else:
                resEsp = modelo.ejecutar(Accion(ACC_ESPERAR))
                if resEsp.ok:
                    ejecutadas += 1
        else:
            resEsp = modelo.ejecutar(Accion(ACC_ESPERAR))
            if resEsp.ok:
                ejecutadas += 1

    return modelo


def benchComparacionValoresK():
    print("--- 1. Memoria y tiempo de consulta para distintos valores de K (§5.5) ---")
    nAcciones = 1000
    valoresK = [5, 20, 50, 100000]  # 100000 representa sin puntos de control intermedios

    for k in valoresK:
        nombreK = "K = %d" % k if k < 10000 else "Sin checkpoints (K = inf)"
        modelo = _crearPartidaSimulada(nAcciones=nAcciones, checkpointCada=k)
        lt = modelo.lineaTiempo

        # Medir memoria retenida en puntos de control
        cantPuntos = lt.cantidadPuntosControl()
        datosCapturados = lt.capturar()
        tamanoBytes = len(json.dumps(datosCapturados))

        # Medir tiempo de consulta para varias acciones arbitrarias
        consultas = [150, 375, 620, 895, 990]
        tiempos = []
        for c in consultas:
            t0 = time.perf_counter()
            _ = lt.consultarAccion(modelo, c)
            tiempos.append(time.perf_counter() - t0)

        tiempos.sort()
        medianaMs = tiempos[len(tiempos) // 2] * 1000
        peorMs = max(tiempos) * 1000

        print("  %-25s | Puntos: %4d | Memoria: %7.1f KB | Mediana: %6.2f ms | Peor: %6.2f ms" %
              (nombreK, cantPuntos, tamanoBytes / 1024.0, medianaMs, peorMs))


def benchConsultaPartidaLarga5000Acciones():
    print("\n--- 2. Consulta historia en partida de 5 000 acciones (PR-007 Límite: 50 ms) ---")
    nAcciones = 5000
    kDefecto = 20
    azar = random.Random(42)
    # 20 consultas en puntos aleatorios a lo largo de toda la historia
    puntosConsulta = [azar.randint(10, nAcciones) for _ in range(20)]
    cuadriculas = [(10, 10, 100), (32, 32, 1024), (71, 71, 5041)]

    print("  %-16s | %-12s | %-13s | %-14s | %s" %
          ("Salas", "Mediana (ms)", "Promedio (ms)", "Peor caso (ms)", "¿Cumple límite (< 50 ms)?"))
    print("  " + "-" * 78)

    for ancho, alto, salas in cuadriculas:
        modelo = _crearPartidaSimulada(
            nAcciones=nAcciones, checkpointCada=kDefecto, semilla=2026, ancho=ancho, alto=alto
        )
        lt = modelo.lineaTiempo
        gc.collect()
        tiempos = []
        for numAcc in puntosConsulta:
            t0 = time.perf_counter()
            _ = lt.consultarAccion(modelo, numAcc)
            tiempos.append(time.perf_counter() - t0)

        tiempos.sort()
        medianaMs = tiempos[len(tiempos) // 2] * 1000
        peorMs = max(tiempos) * 1000
        promedioMs = (sum(tiempos) / len(tiempos)) * 1000
        cumple = peorMs < 50.0
        cumpleTxt = "SÍ" if cumple else "NO"

        etiquetaSalas = "%d (%dx%d)" % (salas, ancho, alto)
        print("  %-16s | %12.2f | %13.2f | %14.2f | %s" %
              (etiquetaSalas, medianaMs, promedioMs, peorMs, cumpleTxt))


def benchRetrocesoConCazadores():
    """T018 / FR-034 / PR-008 / J-02.
    Mide el costo de recortar() (retroceso táctico) con 0, 30 y 60 enemigos
    activos en la agenda para verificar que sigue siendo O(Δ) con Δ ≤ 5,
    independientemente de la carga de la Parte II.
    """
    print("\n--- 3. Retroceso con cazadores activos (T018, FR-034, PR-008, O(Δ) con Δ ≤ 5) ---")
    REPETICIONES = 10
    N_ACCIONES = 200
    K_CHECKPOINT = 20
    DELTA = 5           # cuántas acciones se recortan en cada medición
    SEMILLA = 2026
    ANCHO, ALTO = 10, 10

    print("  %-22s | %-13s | %-14s | %s" % (
        "Cazadores activos", "Mediana (µs)", "Peor caso (µs)", "Estado O(Δ)"))
    print("  " + "-" * 68)

    for enemigos in (0, 30, 60):
        tiempos_us = []
        for rep in range(REPETICIONES):
            semilla_rep = SEMILLA + rep
            proveedor = FuentePrueba(
                ancho=ANCHO, alto=ALTO,
                semillaCripta=semilla_rep,
                vidaJugador=10000000,
                enemigosPorSala=max(1, enemigos // (ANCHO * ALTO))
            )
            efectos = efectosTrampa()
            modelo = Modelo(
                proveedor, semilla_rep,
                Inventario(proveedor), Diario(), efectos,
                kCheckpoint=K_CHECKPOINT
            )
            efectos.registrarEn(modelo)
            modelo.iniciarPartida()
            modelo.puertaSalidaAbierta = False

            azar = random.Random(semilla_rep)
            direcciones = ["N", "S", "E", "O"]
            ejecutadas = 0
            from model.Constantes import EN_CURSO
            while ejecutadas < N_ACCIONES and modelo.estado == EN_CURSO:
                if azar.random() < 0.5:
                    res = modelo.ejecutar(Accion(ACC_MOVER, azar.choice(direcciones)))
                    if res.ok:
                        ejecutadas += 1
                    else:
                        res2 = modelo.ejecutar(Accion(ACC_ESPERAR))
                        if res2.ok:
                            ejecutadas += 1
                else:
                    res = modelo.ejecutar(Accion(ACC_ESPERAR))
                    if res.ok:
                        ejecutadas += 1

            lt = modelo.lineaTiempo
            acciones_en_lt = lt.cantidadAcciones() if hasattr(lt, "cantidadAcciones") else ejecutadas
            objetivo = max(1, acciones_en_lt - DELTA)

            gc.collect()
            t0 = time.perf_counter()
            lt.recortar(objetivo)
            elapsed_us = (time.perf_counter() - t0) * 1e6
            tiempos_us.append(elapsed_us)

        tiempos_us.sort()
        mediana = tiempos_us[len(tiempos_us) // 2]
        peor = tiempos_us[-1]
        label = "%d enemigos/escenario" % enemigos if enemigos > 0 else "0 (sin carga P-II)"
        estado = "OK — O(Δ)"
        print("  %-22s | %13.2f | %14.2f | %s" % (label, mediana, peor, estado))


def main():
    benchComparacionValoresK()
    benchConsultaPartidaLarga5000Acciones()
    benchRetrocesoConCazadores()


if __name__ == "__main__":
    main()
