import argparse
import os

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


def ejecutar_benchmarks():
    from bench.ordenamientos import main as bench_ordenamientos
    from bench.cache import main as bench_cache
    from bench.benchGuardado import main as bench_guardado
    from bench.BenchEfectos import main as bench_efectos
    print("------Bench de Ordenamientos------")
    bench_ordenamientos()
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Cache------")
    bench_cache()
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Guardado (binario vs JSON)------")
    bench_guardado()
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Efectos (cancelar)------")
    bench_efectos()


def crear_cliente(args):
    if args.offline:
        from adapters.clienteOffline import ClienteOffline
        return ClienteOffline(args.offline)
    from adapters.clienteHttp import ClienteHTTP
    return ClienteHTTP(BASE_URL)


def elegir_cripta(cliente):
    criptas = cliente.obtener_lista_criptas().get("criptas", [])
    if len(criptas) == 0:
        raise RuntimeError("El servicio no devolvió criptas.")
    print("Criptas disponibles:")
    for i in range(len(criptas)):
        c = criptas[i]
        print("  %d) %s - %s (%d salas, dificultad %s)"
              % (i + 1, c["id"], c["nombre"], c["salas"], c["dificultad"]))
    while True:
        texto = input("Elige una cripta (número): ").strip()
        if texto.isdigit() and 1 <= int(texto) <= len(criptas):
            return criptas[int(texto) - 1]["id"]


def construir_modelo(cliente, id_cripta, semilla, cache_size):
    from adapters.ProveedorRed import ProveedorRed
    from model.Juego import Modelo
    from model.Inventario import Inventario
    from model.Diario import Diario
    from model.efectos import EfectosJuego

    proveedor = ProveedorRed(cliente, id_cripta, cache_size)
    efectos = EfectosJuego()
    modelo = Modelo(proveedor, semilla, Inventario(proveedor), Diario(), efectos)
    efectos.registrarEn(modelo)
    return proveedor, modelo


def jugar(args, cliente):
    from adapters.bitacoraReplay import GestorBitacoraReplay
    from adapters.tablaPuntajes import GestorTablaPuntajes
    from controller.ControladorJuego import Controlador
    from view.Consola import VistaConsola

    id_cripta = args.cripta if args.cripta else elegir_cripta(cliente)
    semilla = args.semilla if args.semilla is not None else int.from_bytes(os.urandom(4), "big")
    nombre = args.nombre if args.nombre else (input("Nombre del jugador: ").strip() or "Jugador")

    proveedor, modelo = construir_modelo(cliente, id_cripta, semilla, args.cache_size)
    version_cripta = proveedor.datos["version"]

    registro = GestorBitacoraReplay(args.log)
    registro.iniciar_nueva_bitacora(id_cripta, version_cripta, proveedor.cache.versionCatalogo, semilla)

    controlador = Controlador(modelo, VistaConsola(), registro, GestorTablaPuntajes())
    controlador.nombre = nombre
    controlador.idCripta = id_cripta
    controlador.versionCripta = version_cripta

    modelo.iniciarPartida()
    print("Semilla: %d  |  bitácora: %s" % (semilla, args.log))
    controlador.bucleInteractivo()
    print(proveedor.reporte())


def reproducir(args, cliente):
    from adapters.bitacoraReplay import GestorBitacoraReplay
    from controller.ControladorJuego import Controlador

    registro = GestorBitacoraReplay(args.replay)
    meta, acciones = registro.cargar_y_validar_replay(cliente)
    proveedor, modelo = construir_modelo(cliente, meta["id_cripta"], meta["semilla"], args.cache_size)
    modelo.iniciarPartida()
    controlador = Controlador(modelo)          # sin vista: --replay no la usa
    ok, motivo = controlador.reproducir(acciones)
    resultado = modelo.resultadoPartida()
    print("Replay %s. Estado=%d reloj=%d acciones=%d derrotados=%d"
          % ("completo" if ok else "INTERRUMPIDO: " + motivo, resultado.estado,
             resultado.tiempoFinal, resultado.acciones, resultado.derrotados))
    print(proveedor.reporte())


def main():
    parser = argparse.ArgumentParser(description="Cripta Dungeon")
    parser.add_argument("--bench", action="store_true", help="ejecuta los benchmarks")
    parser.add_argument("--offline", metavar="DIR", help="lee las respuestas desde una carpeta")
    parser.add_argument("--replay", metavar="LOG", help="reproduce una partida desde su bitácora")
    parser.add_argument("--cache-size", type=int, default=25, help="fichas en memoria (def. 25)")
    parser.add_argument("--cripta", help="id de la cripta (si no, se elige de una lista)")
    parser.add_argument("--semilla", type=int, help="semilla del azar (si no, aleatoria)")
    parser.add_argument("--nombre", help="nombre del jugador")
    parser.add_argument("--log", default="partida.log", help="archivo de bitácora de la partida")
    args = parser.parse_args()

    if args.bench:
        ejecutar_benchmarks()
        return

    try:
        cliente = crear_cliente(args)
        if args.replay:
            reproducir(args, cliente)
        else:
            jugar(args, cliente)
    except RuntimeError as error:
        print("ERROR: %s" % error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
