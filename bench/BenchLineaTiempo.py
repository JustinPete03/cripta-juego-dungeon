# Benchmark de Línea de Tiempo y Puntos de Control (§5.5, §6.1, PR-007, PR-008 Parte II).
# Mide memoria y tiempo de consulta para varios K (5, 20, 50, sin checkpoints),
# y tiempo de consulta < 50 ms en partida de al menos 5 000 acciones.

import time
import random
import json
import sys

from tests.FuentePrueba import FuentePrueba
from model.Acciones import Accion
from model.Constantes import ACC_ESPERAR, ACC_MOVER, EN_CURSO
from model.Inventario import Inventario
from model.Diario import Diario
from model.efectosTrampa import efectosTrampa
from model.Juego import Modelo


def _crearPartidaSimulada(nAcciones=1000, checkpointCada=20, semilla=2026):
    azar = random.Random(semilla)
    proveedor = FuentePrueba(ancho=8, alto=8, semillaCripta=semilla, vidaJugador=10000000, enemigosPorSala=1)
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
        nombreK = "K = %d" % k if k < 10000 else "Sin checkpoints (K = ∞)"
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
    print("  Simulando partida de %d acciones con K=%d por defecto..." % (nAcciones, kDefecto))
    modelo = _crearPartidaSimulada(nAcciones=nAcciones, checkpointCada=kDefecto, semilla=2026)
    lt = modelo.lineaTiempo

    azar = random.Random(42)
    # 20 consultas en puntos aleatorios a lo largo de toda la historia
    puntosConsulta = [azar.randint(10, nAcciones) for _ in range(20)]

    tiempos = []
    for numAcc in puntosConsulta:
        t0 = time.perf_counter()
        _ = lt.consultarAccion(modelo, numAcc)
        tiempos.append(time.perf_counter() - t0)

    tiempos.sort()
    medianaMs = tiempos[len(tiempos) // 2] * 1000
    peorMs = max(tiempos) * 1000
    promedioMs = (sum(tiempos) / len(tiempos)) * 1000

    print("  Resultados para 20 consultas arbitrarias (1 a %d):" % nAcciones)
    print("    Tiempo promedio : %.2f ms" % promedioMs)
    print("    Tiempo mediana  : %.2f ms" % medianaMs)
    print("    Peor caso       : %.2f ms" % peorMs)
    print("  ¿Cumple requisito PR-007 (< 50 ms)?: %s" %
          ("SÍ (%.2f ms < 50 ms)" % medianaMs if medianaMs < 50 else "NO"))


def main():
    benchComparacionValoresK()
    benchConsultaPartidaLarga5000Acciones()


if __name__ == "__main__":
    main()
