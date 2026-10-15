import random
import time
import os

from model.cache.cache_fichas import CacheFichas
from model.cache.persistencia_cache import guardar_cache, cargar_cache

#creamos constantes fijas para evidencias/resultados del analisis
SEMILLA = 2026
TOTAL_FICHAS_CATALOGO = 60
NUMERO_PETICIONES= 1000    #cantidad de peticiones propuesta para la simulacion
ARCHIVO_BENCH_TEMP = "cache_bench_temp.json"
VERSION_BENCH = "1.0.0"

def generar_solicitudes_uniformes(n_peticiones, total_fichas, azar): #este metodo hace que cualquier ficha tenga igual probabilidad de aparecer
    return[f"ficha_{azar.randint(1, total_fichas)}" for _ in range(n_peticiones)]

def generar_solicitudes_sesgadas(n_peticiones, total_fichas, azar): #divide las fichas en dos grupos (20% de fichas frecuentes y un 80% de fichas raras)
    cantidad_frecuentes = max(2, int(total_fichas * 0.2))
    fichas_frecuentes = [f"ficha_{i}" for i in range(1, cantidad_frecuentes + 1)]
    fichas_raras = [f"ficha_{i}" for i in range(cantidad_frecuentes + 1, total_fichas + 1)]

    solicitudes = []
    for _ in range(n_peticiones):
        if azar.random() < 0.8:
            solicitudes.append(azar.choice(fichas_frecuentes))
        else:
            solicitudes.append(azar.choice(fichas_raras))

    return solicitudes

def simular_carga(capacidad, peticiones):
    cache = CacheFichas(capacidad = capacidad)
    llamadas_externas = 0

    def cargador_simulado(lote):
        nonlocal llamadas_externas
        llamadas_externas += len(lote)
        return[(id_f, f"datos_{id_f}") for id_f in lote]

    t0 =time.perf_counter()

    for id_ficha in peticiones:
        cache.obtener_fichas([id_ficha], cargador_simulado)

    tiempo_ms = (time.perf_counter() - t0) * 1000

    total_consultas = cache.aciertos + cache.fallos
    hit_rate = (cache.aciertos / total_consultas * 100) if total_consultas > 0 else 0.0

    return{
        "capacidad": capacidad,
        "aciertos" : cache.aciertos,
        "fallos" : cache.fallos,
        "desalojos" : cache.desalojos,
        "hit_rate" : hit_rate,
        "llamadas_externas" : llamadas_externas,
        "tiempo_ms" : tiempo_ms,
    }

def bench_persistencia(capacidad, peticiones):
    #Inicio sin archivo previo
    cache_vacia = CacheFichas(capacidad = capacidad)
    llamadas_vacia = 0

    def cargador_vacia(lote):
        nonlocal llamadas_vacia
        llamadas_vacia += len(lote)
        return[(id_f, f"datos_{id_f}") for id_f in lote]

    for id_ficha in peticiones:
        cache_vacia.obtener_fichas([id_ficha], cargador_vacia)

    guardar_cache(ARCHIVO_BENCH_TEMP,VERSION_BENCH, cache_vacia)

    #Restaurando desde el disco
    cache_restaurada = CacheFichas(capacidad = capacidad)
    cargar_cache(ARCHIVO_BENCH_TEMP, VERSION_BENCH, cache_restaurada)
    llamadas_restaurada = 0

    def cargador_restaurada(lote):
        nonlocal llamadas_restaurada
        llamadas_restaurada += len(lote)
        return[(id_f, f"datos_{id_f}") for id_f in lote]

    for id_ficha in peticiones:
        cache_restaurada.obtener_fichas([id_ficha], cargador_restaurada)

    if os.path.exists(ARCHIVO_BENCH_TEMP): #eliminar el archivo temporal
        os.remove(ARCHIVO_BENCH_TEMP)

    solicitudes_ahorradas = llamadas_vacia - llamadas_restaurada
    porcentaje_ahorro = (solicitudes_ahorradas / llamadas_vacia * 100) if llamadas_vacia > 0 else 0.0

    return{
        "llamadas_vacia" : llamadas_vacia,
        "llamadas_restaurada" : llamadas_restaurada,
        "ahorro" : solicitudes_ahorradas,
        "porcentaje_ahorro" : porcentaje_ahorro,
    }

def main():
    azar = random.Random(SEMILLA)
    capacidades = (5, 10, 25, 50)

    print(f"semilla={SEMILLA}  peticiones={NUMERO_PETICIONES}")
    print(f"{'patron':<12}{'cap':>6}{'aciertos':>10}{'fallos':>10}{'hit_rate':>12}{'desalojos':>12}{'ms':>10}")

    pruebas = [("uniforme", generar_solicitudes_uniformes(NUMERO_PETICIONES, TOTAL_FICHAS_CATALOGO, azar)), ("sesgado", generar_solicitudes_sesgadas(NUMERO_PETICIONES, TOTAL_FICHAS_CATALOGO, azar))]

    for nombre, solicitudes in pruebas:
        for cap in capacidades:
            res = simular_carga(cap, solicitudes)
            print(f"{nombre:<12}{cap:>6}{res['aciertos']:>10}{res['fallos']:>10}{res['hit_rate']:>11.1f}%{res['desalojos']:>12}{res['tiempo_ms']:>10.2f}")

    print("\n--- persistencia (arranque) ---")
    for n in (25, 50, 100):
        solicitudes_arranque = generar_solicitudes_sesgadas(n, TOTAL_FICHAS_CATALOGO, azar)
        datos = bench_persistencia(25, solicitudes_arranque)
        print(f"peticiones={n:<4} vacia={datos['llamadas_vacia']:<3} restaurada={datos['llamadas_restaurada']:<3} ahorro={datos['porcentaje_ahorro']:.1f}%")


if __name__ == "__main__":
    main()