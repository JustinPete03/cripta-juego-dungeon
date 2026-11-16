# Benchmark de Verificación de Resolubilidad (§5.4, §6.1, §6.3 Parte II).
# Mide recorrido incremental O(V + E + K) vs recorrido repetido ingenuo, y tiempo total < 200 ms.

import time
import random

from model.Resolubilidad import verificarResolubilidad
from model.Tabla import Tabla


def _generarCriptaCadenaLlaves(nLlaves=20):
    """Genera una cripta con una cadena estricta de dependencias:
    Sala 1 (inicio, contiene K1) -> Puerta K1 -> Sala 2 (contiene K2) -> ... -> Sala N+1 (salida).
    """
    esqueleto = []
    listaLlaves = []

    for i in range(1, nLlaves + 2):
        salidas = {}
        if i <= nLlaves:
            kReq = "llave_%d" % i
            salidas["E"] = {"sala": i + 1, "cerrada": True, "llave": kReq}
        if i > 1:
            kReq = "llave_%d" % (i - 1)
            salidas["O"] = {"sala": i - 1, "cerrada": True, "llave": kReq}

        esqueleto.append({"id": i, "nombre": "Sala %d" % i, "salidas": salidas})

        if i <= nLlaves:
            # La llave i se encuentra en la sala i
            listaLlaves.append({"id": "llave_%d" % i, "sala": i})

    datosGenerales = {
        "id": "cripta-cadena-%d" % nLlaves,
        "sala_inicial": 1,
        "sala_salida": nLlaves + 1,
        "llave_salida": "llave_%d" % nLlaves
    }

    return datosGenerales, esqueleto, listaLlaves


def _verificarIngenuoRepetido(datosGenerales, esqueleto, listaLlaves):
    """Algoritmo ingenuo: reinicia el BFS desde la sala inicial cada vez que descubre una llave."""
    salaInicial = datosGenerales["sala_inicial"]
    salaSalida = datosGenerales["sala_salida"]
    llaveSalida = datosGenerales["llave_salida"]

    # Indexar llaves por sala
    llavesPorSala = {}
    for k in listaLlaves:
        s = k["sala"]
        if s not in llavesPorSala:
            llavesPorSala[s] = []
        llavesPorSala[s].append(k["id"])

    # Indexar salas
    salasDict = {s["id"]: s for s in esqueleto}

    llavesObtenidas = set()
    cambio = True

    while cambio:
        cambio = False
        alcanzadas = set()
        cola = [salaInicial]
        cabeza = 0

        while cabeza < len(cola):
            u = cola[cabeza]
            cabeza += 1

            if u in alcanzadas:
                continue
            alcanzadas.add(u)

            # Recoger llaves
            for kId in llavesPorSala.get(u, []):
                if kId not in llavesObtenidas:
                    llavesObtenidas.add(kId)
                    cambio = True

            # Si encontramos una llave nueva, reiniciamos el recorrido desde cero
            if cambio:
                break

            infoU = salasDict.get(u)
            if not infoU:
                continue

            for dirNom, sal in infoU.get("salidas", {}).items():
                v = sal["sala"]
                cerrada = sal.get("cerrada", False)
                req = sal.get("llave")
                if cerrada:
                    if req in llavesObtenidas:
                        if v not in alcanzadas:
                            cola.append(v)
                else:
                    if v not in alcanzadas:
                        cola.append(v)

    return (llaveSalida in llavesObtenidas) and (salaSalida in alcanzadas)


def benchIncrementalVsIngenuo():
    print("--- 1. Recorrido incremental O(V + E + K) vs Ingenuo (reinicio por llave) (§5.4) ---")
    tamanos = [10, 25, 50, 100]

    for k in tamanos:
        datos, esqueleto, listaLlaves = _generarCriptaCadenaLlaves(nLlaves=k)

        # Medir incremental
        repeticiones = 50
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            resInc = verificarResolubilidad(datos, esqueleto, listaLlaves)
        tInc = (time.perf_counter() - t0) / repeticiones

        # Medir ingenuo
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            resIng = _verificarIngenuoRepetido(datos, esqueleto, listaLlaves)
        tIng = (time.perf_counter() - t0) / repeticiones

        aceleracion = tIng / tInc if tInc > 0 else 1.0
        print("  K = %3d llaves | Incremental: %7.3f ms | Ingenuo: %7.3f ms | Aceleración: %5.1fx" %
              (k, tInc * 1000, tIng * 1000, aceleracion))


def benchTiempoVerificacionCriptaGrande():
    print("\n--- 2. Tiempo de verificación en cripta grande (200 salas) (§6.1, PR-005 < 200 ms) ---")
    azar = random.Random(2026)
    nSalas = 200
    nLlaves = 30

    esqueleto = []
    for i in range(1, nSalas + 1):
        salidas = {}
        if i < nSalas:
            salidas["E"] = {"sala": i + 1}
        if i > 1:
            salidas["O"] = {"sala": i - 1}
        if azar.random() < 0.4:
            salto = azar.randint(1, nSalas)
            if salto != i:
                salidas["N"] = {"sala": salto}
        esqueleto.append({"id": i, "nombre": "Sala %d" % i, "salidas": salidas})

    # Cerrar 30 puertas con llaves
    listaLlaves = []
    for kIdx in range(1, nLlaves + 1):
        kId = "llave_%02d" % kIdx
        salaPuerta = azar.randint(1, nSalas - 1)
        # Buscar una salida de salaPuerta
        for d in esqueleto[salaPuerta - 1]["salidas"]:
            esqueleto[salaPuerta - 1]["salidas"][d]["cerrada"] = True
            esqueleto[salaPuerta - 1]["salidas"][d]["llave"] = kId
            break
        # Llave accesible en una sala anterior o igual
        salaLlave = azar.randint(1, max(1, salaPuerta // 2 + 1))
        listaLlaves.append({"id": kId, "sala": salaLlave})

    # Llave salida
    esqueleto[-1]["salidas"]["O"]["cerrada"] = True
    esqueleto[-1]["salidas"]["O"]["llave"] = "llave_salida"
    listaLlaves.append({"id": "llave_salida", "sala": 1})

    datosGenerales = {
        "id": "cripta-grande-200",
        "sala_inicial": 1,
        "sala_salida": nSalas,
        "llave_salida": "llave_salida"
    }

    repeticiones = 30
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        resultado = verificarResolubilidad(datosGenerales, esqueleto, listaLlaves)
        tiempos.append(time.perf_counter() - t0)

    tiempos.sort()
    mediana = tiempos[len(tiempos) // 2] * 1000
    print("  Mediana de verificación (200 salas, %d llaves): %.2f ms" % (len(listaLlaves), mediana))
    print("  ¿Cumple requisito PR-005 (< 200 ms)?: %s" % ("SÍ (%.2f ms < 200 ms)" % mediana if mediana < 200 else "NO"))


def main():
    benchIncrementalVsIngenuo()
    benchTiempoVerificacionCriptaGrande()


if __name__ == "__main__":
    main()
