# Benchmark de Verificación de Resolubilidad (§5.4, §6.1, §6.3 Parte II).
# Mide recorrido incremental O(V + E + K) vs recorrido repetido ingenuo, y tiempo total < 200 ms.

import time
import random

from model.Resolubilidad import verificarResolubilidad
from model.Tabla import Tabla
from model.Salas import IndiceOrdenado


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
            listaLlaves.append({"id": "llave_%d" % i, "sala": i})

    datosGenerales = {
        "id": "cripta-cadena-%d" % nLlaves,
        "sala_inicial": 1,
        "sala_salida": nLlaves + 1,
        "llave_salida": "llave_%d" % nLlaves
    }

    return datosGenerales, esqueleto, listaLlaves


def _generarCriptaCadenaConCiclo(nLlaves=20):
    """Genera una cripta con un ciclo de dependencias no resoluble (R-03):
    K1 bloquea Sala 2, que contiene K2... hasta KN, y KN está bloqueando K1.
    """
    esqueleto = []
    salidas1 = {"E": {"sala": 2, "cerrada": True, "llave": "k_1"}}
    esqueleto.append({"id": 1, "nombre": "S1", "salidas": salidas1})
    listaLlaves = []

    for i in range(2, nLlaves + 2):
        salidas = {"O": {"sala": i - 1, "cerrada": True, "llave": f"k_{i-1}"}}
        if i <= nLlaves:
            salidas["E"] = {"sala": i + 1, "cerrada": True, "llave": f"k_{i}"}
            listaLlaves.append({"id": f"k_{i}", "sala": i})
        else:
            listaLlaves.append({"id": "k_1", "sala": i})
        esqueleto.append({"id": i, "nombre": f"S{i}", "salidas": salidas})

    datosGenerales = {
        "id": f"cripta-ciclo-{nLlaves}",
        "sala_inicial": 1,
        "sala_salida": nLlaves + 1,
        "llave_salida": "k_salida"
    }
    listaLlaves.append({"id": "k_salida", "sala": nLlaves + 1})
    return datosGenerales, esqueleto, listaLlaves


def _verificarIngenuoRepetido(datosGenerales, esqueleto, listaLlaves):
    """Algoritmo ingenuo (§5.4, R-03): reinicia el BFS desde la sala inicial cada vez que descubre una llave.
    Implementado con las mismas estructuras propias (Tabla e IndiceOrdenado) para aislar la diferencia
    algorítmica O(K(V+E)) vs O(V+E+K), evitando sesgos de estructuras nativas en C.
    """
    salaInicial = datosGenerales["sala_inicial"]
    salaSalida = datosGenerales["sala_salida"]
    llaveSalida = datosGenerales["llave_salida"]

    # Indexar llaves por sala usando Tabla propia
    llavesPorSala = Tabla()
    for k in listaLlaves:
        s = k["sala"]
        enS = llavesPorSala.obtener(s, [])
        enS.append(k["id"])
        llavesPorSala.guardar(s, enS)

    # Indexar salas usando IndiceOrdenado propio
    salasIndice = IndiceOrdenado()
    for s in esqueleto:
        salasIndice.insertar(s["id"], s)

    llavesObtenidas = Tabla()
    cambio = True

    while cambio:
        cambio = False
        alcanzadas = Tabla()
        cola = [salaInicial]
        cabeza = 0

        while cabeza < len(cola):
            u = cola[cabeza]
            cabeza += 1

            if alcanzadas.contiene(u):
                continue
            alcanzadas.guardar(u, True)

            # Recoger llaves disponibles
            for kId in llavesPorSala.obtener(u, []):
                if not llavesObtenidas.contiene(kId):
                    llavesObtenidas.guardar(kId, True)
                    cambio = True

            # Si encontramos una llave nueva, reiniciamos el recorrido completo desde cero
            if cambio:
                break

            infoU = salasIndice.buscar(u)
            if not infoU:
                continue

            for dirNom, sal in infoU.get("salidas", {}).items():
                v = sal["sala"]
                cerrada = sal.get("cerrada", False)
                req = sal.get("llave")
                if cerrada:
                    if req and llavesObtenidas.contiene(req):
                        if not alcanzadas.contiene(v):
                            cola.append(v)
                else:
                    if not alcanzadas.contiene(v):
                        cola.append(v)

    return llavesObtenidas.contiene(llaveSalida) and alcanzadas.contiene(salaSalida)


def benchIncrementalVsIngenuo():
    print("--- 1. Recorrido incremental O(V + E + K) vs Ingenuo O(K·(V + E)) (§5.4, R-03) ---")
    print("      (Ambos usando Tabla e IndiceOrdenado propios para comparar algoritmos)")
    print("  %5s | %10s %12s | %10s %12s | %10s" %
          ("K", "Inc (ms)", "ms/llave", "Ing (ms)", "ms/llave", "Ganancia"))
    print("  " + "-" * 72)

    tamanos = [100, 500, 1000, 2000, 5000]

    for k in tamanos:
        datos, esqueleto, listaLlaves = _generarCriptaCadenaLlaves(nLlaves=k)

        # Repeticiones calibradas según tamaño
        repInc = 10 if k <= 1000 else 3
        repIng = 5 if k <= 500 else (2 if k <= 1000 else 1)

        # Medir incremental
        t0 = time.perf_counter()
        for _ in range(repInc):
            resInc = verificarResolubilidad(datos, esqueleto, listaLlaves)
        tInc = (time.perf_counter() - t0) / repInc

        # Medir ingenuo
        t0 = time.perf_counter()
        for _ in range(repIng):
            resIng = _verificarIngenuoRepetido(datos, esqueleto, listaLlaves)
        tIng = (time.perf_counter() - t0) / repIng

        msLlaveInc = (tInc * 1000) / k
        msLlaveIng = (tIng * 1000) / k
        aceleracion = tIng / tInc if tInc > 0 else 1.0

        print("  %5d | %9.2f ms  %8.4f ms | %9.2f ms  %8.4f ms | %8.1fx" %
              (k, tInc * 1000, msLlaveInc, tIng * 1000, msLlaveIng, aceleracion))


def benchCasoNoResolubleCiclo():
    print("\n--- 2. Caso No Resoluble: Cadena con Ciclo y Reporte (§5.4, R-03) ---")
    print("  %5s | %10s %14s | %12s" %
          ("K", "Tiempo (ms)", "Ciclo Detectado", "Determinismo"))
    print("  " + "-" * 52)

    tamanos = [100, 500, 1000, 2000, 5000]
    for k in tamanos:
        datos, esqueleto, listaLlaves = _generarCriptaCadenaConCiclo(nLlaves=k)
        repeticiones = 5 if k <= 1000 else 2
        t0 = time.perf_counter()
        for _ in range(repeticiones):
            res1 = verificarResolubilidad(datos, esqueleto, listaLlaves)
        tCiclo = (time.perf_counter() - t0) / repeticiones
        res2 = verificarResolubilidad(datos, esqueleto, listaLlaves)

        det = (res1.ciclo == res2.ciclo)
        lenCiclo = len(res1.ciclo) if res1.ciclo else 0
        print("  %5d | %9.2f ms  %11d llaves | %12s" %
              (k, tCiclo * 1000, lenCiclo, "SÍ (idéntico)" if det else "NO"))


def benchTiempoVerificacionCriptaGrande():
    print("\n--- 3. Tiempo de Verificación en Criptas Grandes (§6.1, PR-005 < 200 ms, R-04) ---")
    print("  %6s %8s | %12s %12s | %15s" %
          ("Salas", "Llaves", "Mediana (ms)", "Peor Caso (ms)", "¿Cumple < 200 ms?"))
    print("  " + "-" * 62)

    azar = random.Random(2026)
    configuraciones = [
        (200, 30),
        (500, 60),
        (1000, 100),
        (2000, 150)
    ]

    for nSalas, nLlaves in configuraciones:
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

        listaLlaves = []
        for kIdx in range(1, nLlaves + 1):
            kId = "llave_%03d" % kIdx
            salaPuerta = azar.randint(1, nSalas - 1)
            for d in esqueleto[salaPuerta - 1]["salidas"]:
                esqueleto[salaPuerta - 1]["salidas"][d]["cerrada"] = True
                esqueleto[salaPuerta - 1]["salidas"][d]["llave"] = kId
                break
            salaLlave = azar.randint(1, max(1, salaPuerta // 2 + 1))
            listaLlaves.append({"id": kId, "sala": salaLlave})

        esqueleto[-1]["salidas"]["O"]["cerrada"] = True
        esqueleto[-1]["salidas"]["O"]["llave"] = "llave_salida"
        listaLlaves.append({"id": "llave_salida", "sala": 1})

        datosGenerales = {
            "id": f"cripta-grande-{nSalas}",
            "sala_inicial": 1,
            "sala_salida": nSalas,
            "llave_salida": "llave_salida"
        }

        repeticiones = 15
        tiempos = []
        for _ in range(repeticiones):
            t0 = time.perf_counter()
            verificarResolubilidad(datosGenerales, esqueleto, listaLlaves)
            tiempos.append((time.perf_counter() - t0) * 1000)

        tiempos.sort()
        mediana = tiempos[len(tiempos) // 2]
        peorCaso = tiempos[-1]
        cumple = (peorCaso < 200.0)

        print("  %6d %8d | %11.2f ms %11.2f ms | %15s" %
              (nSalas, len(listaLlaves), mediana, peorCaso,
               "SÍ (%.2f < 200)" % peorCaso if cumple else "NO"))


def main():
    benchIncrementalVsIngenuo()
    benchCasoNoResolubleCiclo()
    benchTiempoVerificacionCriptaGrande()


if __name__ == "__main__":
    main()
