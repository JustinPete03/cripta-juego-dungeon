import argparse
import os

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


def ejecutarBenchmarks():
    from bench.Ordenamientos import main as benchOrdenamientos
    from bench.Cache import main as benchCache
    from bench.benchGuardado import main as benchGuardado
    try:
        from bench.benchEfectos import main as benchEfectos
    except ImportError:
        from bench.BenchEfectos import main as benchEfectos

    print("------Bench de Ordenamientos (§4.9)------")
    benchOrdenamientos()
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Cache (§4.3 / §4.4)------")
    benchCache()
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Guardado (Binario vs JSON) (§4.10)------")
    benchGuardado()
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Efectos (cancelar) (§4.1)------")
    benchEfectos()
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Motor (Agenda, Rastro, Bitácora) (§4.1, §4.7, §4.8)------")
    try:
        from bench.BenchMotor import correr as correrMotor
        def imprimir(subsistema, descripcion, segundos):
            print("%-9s %-48s %9.2f ms" % (subsistema, descripcion, segundos * 1000))
        correrMotor(imprimir)
    except Exception as e:
        print(f"Nota BenchMotor: {e}")
    print("\n" + "=" * 50 + "\n")
    print("------Bench de Retroceso e Inventario (§4.5, §4.6)------")
    try:
        import sys, threading
        sys.setrecursionlimit(200000)
        from bench.BenchRetroceso import _todo as correrRetroceso
        hilo = threading.Thread(target=correrRetroceso)
        hilo.start()
        hilo.join()
    except Exception as e:
        print(f"Nota BenchRetroceso: {e}")


def crearCliente(args):
    if args.offline:
        from adapters.clienteOffline import ClienteOffline
        return ClienteOffline(args.offline)
    from adapters.clienteHttp import ClienteHTTP
    return ClienteHTTP(BASE_URL)


def elegirCripta(cliente):
    criptas = cliente.obtenerListaCriptas().get("criptas", [])
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


def construirModelo(cliente, idCripta, semilla, cacheSize):
    from adapters.ProveedorRed import ProveedorRed
    from model.Juego import Modelo
    from model.Inventario import Inventario
    from model.Diario import Diario
    from model.efectos import EfectosJuego

    proveedor = ProveedorRed(cliente, idCripta, cacheSize)
    efectos = EfectosJuego()
    modelo = Modelo(proveedor, semilla, Inventario(proveedor), Diario(), efectos)
    efectos.registrarEn(modelo)
    return proveedor, modelo


def jugar(args, cliente):
    from adapters.bitacoraReplay import GestorBitacoraReplay
    from adapters.tablaPuntajes import GestorTablaPuntajes
    from controller.ControladorJuego import Controlador
    from view.Consola import VistaConsola

    idCripta = args.cripta if args.cripta else elegirCripta(cliente)
    semilla = args.semilla if args.semilla is not None else int.from_bytes(os.urandom(4), "big")
    nombre = args.nombre if args.nombre else (input("Nombre del jugador: ").strip() or "Jugador")

    proveedor, modelo = construirModelo(cliente, idCripta, semilla, args.cache_size)
    versionCripta = proveedor.datos["version"]

    registro = GestorBitacoraReplay(args.log)
    registro.iniciarNuevaBitacora(idCripta, versionCripta, proveedor.cache.versionCatalogo, semilla)

    controlador = Controlador(modelo, VistaConsola(), registro, GestorTablaPuntajes())
    controlador.nombre = nombre
    controlador.idCripta = idCripta
    controlador.versionCripta = versionCripta

    modelo.iniciarPartida()
    print("Semilla: %d  |  bitácora: %s" % (semilla, args.log))
    controlador.bucleInteractivo()
    print(proveedor.reporte())


def reproducir(args, cliente):
    from adapters.bitacoraReplay import GestorBitacoraReplay
    from controller.ControladorJuego import Controlador

    registro = GestorBitacoraReplay(args.replay)
    meta, acciones = registro.cargarYValidarReplay(cliente)
    idCripta = meta.get("idCripta", meta.get("id_cripta"))
    semilla = meta.get("semilla")
    proveedor, modelo = construirModelo(cliente, idCripta, semilla, args.cache_size)
    modelo.iniciarPartida()
    controlador = Controlador(modelo)          # sin vista: --replay no la usa (§6)
    ok, motivo = controlador.reproducir(acciones)
    resultado = modelo.resultadoPartida()
    print("Replay %s. Estado=%d reloj=%d acciones=%d derrotados=%d"
          % ("completo" if ok else "INTERRUMPIDO: " + motivo, resultado.estado,
             resultado.tiempoFinal, resultado.acciones, resultado.derrotados))
    print(proveedor.reporte())


def mostrarTablaPuntajes():
    from adapters.tablaPuntajes import GestorTablaPuntajes
    gestor = GestorTablaPuntajes()
    print(gestor.formatearTabla())


def main():
    parser = argparse.ArgumentParser(description="Cripta Dungeon")
    parser.add_argument("--bench", action="store_true", help="ejecuta los benchmarks (§5.3)")
    parser.add_argument("--offline", metavar="DIR", help="lee las respuestas desde una carpeta (§Modo sin conexión)")
    parser.add_argument("--replay", metavar="LOG", help="reproduce una partida desde su bitácora (§4.11)")
    parser.add_argument("--puntajes", action="store_true", help="muestra la tabla de puntajes locales (§2.12)")
    parser.add_argument("--cache-size", type=int, default=25, help="fichas en memoria (def. 25) (§4.4)")
    parser.add_argument("--cripta", help="id de la cripta (si no, se elige de una lista)")
    parser.add_argument("--semilla", type=int, help="semilla del azar (si no, aleatoria)")
    parser.add_argument("--nombre", help="nombre del jugador")
    parser.add_argument("--log", default="partida.log", help="archivo de bitácora de la partida")
    args = parser.parse_args()

    if args.bench:
        ejecutarBenchmarks()
        return

    if args.puntajes:
        mostrarTablaPuntajes()
        return

    try:
        cliente = crearCliente(args)
        if args.replay:
            reproducir(args, cliente)
        else:
            jugar(args, cliente)
    except RuntimeError as error:
        print("ERROR: %s" % error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
