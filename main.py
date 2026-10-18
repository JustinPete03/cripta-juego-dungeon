import argparse
import importlib
import os
import sys
import threading

from model.Interfaces import SinDatos

BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


def _modulo(ruta):
    return importlib.import_module(ruta)


def _bench(titulo, ejecutar):
    print("------%s------" % titulo)
    try:
        ejecutar()
    except Exception as error:
        print("Nota: %s no esta disponible (%s)." % (titulo, error))
    print("\n" + "=" * 50 + "\n")


def _imprimirBench(subsistema, descripcion, segundos):
    print("%-9s %-48s %9.2f ms" % (subsistema, descripcion, segundos * 1000))


def _benchRetroceso():
    sys.setrecursionlimit(200000)
    hilo = threading.Thread(target=_modulo("bench.BenchRetroceso")._todo)
    hilo.start()
    hilo.join()


def ejecutarBenchmarks():
    # Cada benchmark corre aislado: en la defensa se pasan los otros cinco aunque uno falte.
    _bench("Bench de Ordenamientos (sección 4.9)", lambda: _modulo("bench.Ordenamientos").main())
    _bench("Bench de Cache (sección 4.3 / sección 4.4)", lambda: _modulo("bench.Cache").main())
    _bench("Bench de Guardado (Binario vs JSON) (sección 4.10)",
           lambda: _modulo("bench.benchGuardado").main())
    _bench("Bench de Efectos (cancelar) (sección 4.1)",
           lambda: _modulo("bench.benchEfectos").main())
    _bench("Bench de Motor (Agenda, Rastro, Bitácora) (sección 4.1, sección 4.7, sección 4.8)",
           lambda: _modulo("bench.BenchMotor").correr(_imprimirBench))
    _bench("Bench de Retroceso e Inventario (sección 4.5, sección 4.6)", _benchRetroceso)


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


def armarModelo(proveedor, semilla):
    from model.Juego import Modelo
    from model.Inventario import Inventario
    from model.Diario import Diario
    from model.efectosTrampa import efectosTrampa

    efectos = efectosTrampa()
    modelo = Modelo(proveedor, semilla, Inventario(proveedor), Diario(), efectos)
    efectos.registrarEn(modelo)
    return modelo


def armarGuardado(idCripta, versionCripta, versionCatalogo):
    from adapters.guardadoPartida import guardadoPartida

    return guardadoPartida(idCripta, versionCripta, versionCatalogo)


def construirModelo(cliente, idCripta, semilla, cacheSize):
    from adapters.ProveedorRed import ProveedorRed

    proveedor = ProveedorRed(cliente, idCripta, cacheSize)
    return proveedor, armarModelo(proveedor, semilla)


def jugar(args, cliente):
    from adapters.bitacoraReplay import GestorBitacoraReplay
    from adapters.tablaPuntajes import GestorTablaPuntajes
    from controller.ControladorJuego import Controlador
    from view.Consola import VistaConsola

    idCripta = args.cripta if args.cripta else elegirCripta(cliente)
    semilla = args.semilla if args.semilla is not None else int.from_bytes(os.urandom(4), "big")
    nombre = args.nombre if args.nombre else (input("Nombre del jugador: ").strip() or "Jugador")

    proveedor, modelo = construirModelo(cliente, idCripta, semilla, args.cacheSize)
    versionCripta = proveedor.datos["version"]

    registro = GestorBitacoraReplay(args.log)
    registro.iniciarNuevaBitacora(idCripta, versionCripta, proveedor.cache.versionCatalogo, semilla)

    controlador = Controlador(modelo, VistaConsola(), registro, GestorTablaPuntajes(),
                              armarGuardado(idCripta, versionCripta, proveedor.cache.versionCatalogo),
                              proveedor.reporte)
    controlador.nombre = nombre
    controlador.idCripta = idCripta
    controlador.versionCripta = versionCripta

    modelo.iniciarPartida()
    print("Semilla: %d  |  bitácora: %s" % (semilla, args.log))
    controlador.bucleInteractivo()
    if not controlador.termino:
        # El reporte ya lo muestra el controlador al terminar la partida; esto cubre salir antes.
        print(proveedor.reporte())


def reproducir(args, cliente):
    from adapters.bitacoraReplay import GestorBitacoraReplay
    from controller.ControladorJuego import Controlador

    registro = GestorBitacoraReplay(args.replay)
    meta, acciones = registro.cargarYValidarReplay(cliente)
    idCripta = meta.get("idCripta", meta.get("id_cripta"))
    semilla = meta.get("semilla")
    proveedor, modelo = construirModelo(cliente, idCripta, semilla, args.cacheSize)
    modelo.iniciarPartida()
    controlador = Controlador(modelo)          # sin vista: --replay no la usa (sección 6)
    ok, motivo = controlador.reproducir(acciones)
    resultado = modelo.resultadoPartida()
    print("Replay %s. Estado=%d reloj=%d acciones=%d derrotados=%d"
          % ("completo" if ok else "INTERRUMPIDO: " + motivo, resultado.estado,
             resultado.tiempoFinal, resultado.acciones, resultado.derrotados))
    print(proveedor.reporte())


def lanzarInterfaz(args):
    """Vista gráfica estilo Pokémon sobre los mismos adaptadores que la consola (sección 6).

    Sin --offline ni --cripta usa la cripta de demostración local: la interfaz no depende de la red.
    """
    from adapters.bitacoraReplay import GestorBitacoraReplay
    from adapters.tablaPuntajes import GestorTablaPuntajes
    from controller.ControladorJuego import Controlador
    from view.Grafica import VistaGrafica

    if args.offline or args.cripta:
        cliente = crearCliente(args)
        disponibles = cliente.obtenerListaCriptas().get("criptas", [])
        if args.cripta:
            disponibles = [c for c in disponibles if c["id"] == args.cripta]
        if len(disponibles) == 0:
            raise RuntimeError("No hay criptas disponibles para %s." % args.cripta)
        criptas = tuple((c["nombre"], {"id": c["id"], "salas": c["salas"],
                                       "dificultad": c["dificultad"]}) for c in disponibles)
    else:
        from adapters.proveedor_demo import CRIPTAS_DEMO
        cliente = None
        criptas = CRIPTAS_DEMO

    registro = GestorBitacoraReplay(args.log)
    puntajes = GestorTablaPuntajes()

    def fabrica(indice, semilla):
        nombre, parametros = criptas[indice]
        reporte = None
        if cliente is None:
            from adapters.proveedor_demo import ProveedorDemo
            proveedor = ProveedorDemo(**parametros)
            datos = proveedor.datosGenerales()
            idCripta = datos["id"]
            versionCatalogo = "demo"
        else:
            from adapters.ProveedorRed import ProveedorRed
            proveedor = ProveedorRed(cliente, parametros["id"], args.cacheSize)
            datos = proveedor.datos
            idCripta = parametros["id"]
            versionCatalogo = proveedor.cache.versionCatalogo
            reporte = proveedor.reporte       # la demo no hace solicitudes: no tiene nada que reportar
        modelo = armarModelo(proveedor, semilla)
        registro.iniciarNuevaBitacora(idCripta, datos["version"], versionCatalogo, semilla)
        modelo.iniciarPartida()
        controlador = Controlador(modelo, vista, registro, puntajes,
                                  armarGuardado(idCripta, datos["version"], versionCatalogo), reporte)
        controlador.nombre = args.nombre if args.nombre else "Explorador"
        controlador.idCripta = idCripta
        controlador.versionCripta = datos["version"]
        return controlador

    vista = VistaGrafica(fabrica, criptas)
    if args.semilla is not None:
        vista.semilla = max(1, args.semilla)
    vista.ejecutar()


def mostrarTablaPuntajes():
    from adapters.tablaPuntajes import GestorTablaPuntajes
    gestor = GestorTablaPuntajes()
    print(gestor.formatearTabla())


def main():
    parser = argparse.ArgumentParser(description="Cripta Dungeon")
    parser.add_argument("--bench", action="store_true", help="ejecuta los benchmarks (sección 5.3)")
    parser.add_argument("--offline", metavar="DIR", help="lee las respuestas desde una carpeta (sección Modo sin conexión)")
    parser.add_argument("--replay", metavar="LOG", help="reproduce una partida desde su bitácora (sección 4.11)")
    parser.add_argument("--puntajes", action="store_true", help="muestra la tabla de puntajes locales (sección 2.12)")
    parser.add_argument("--cache-size", dest="cacheSize", type=int, default=25, help="fichas en memoria (def. 25) (sección 4.4)")
    parser.add_argument("--cripta", help="id de la cripta (si no, se elige de una lista)")
    parser.add_argument("--semilla", type=int, help="semilla del azar (si no, aleatoria)")
    parser.add_argument("--nombre", help="nombre del jugador")
    parser.add_argument("--log", default="partida.log", help="archivo de bitácora de la partida")
    parser.add_argument("--gui", action="store_true",
                        help="abre la interfaz grafica estilo Pokemon (es la opcion por defecto)")
    parser.add_argument("--consola", action="store_true",
                        help="juega en la terminal en lugar de abrir la interfaz grafica")
    args = parser.parse_args()

    if args.bench:
        ejecutarBenchmarks()
        return

    if args.puntajes:
        mostrarTablaPuntajes()
        return

    try:
        if args.replay:
            # La bitacora se reproduce sin crear la vista interactiva (seccion 7).
            reproducir(args, crearCliente(args))
            return
        if args.consola:
            if args.gui:
                raise RuntimeError("--consola y --gui piden vistas distintas; elige una.")
            jugar(args, crearCliente(args))
            return
        lanzarInterfaz(args)
    except (RuntimeError, SinDatos) as error:
        # PresupuestoAgotado al arrancar (no alcanza ni para el esqueleto) también sale por aquí.
        print("ERROR: %s" % error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
