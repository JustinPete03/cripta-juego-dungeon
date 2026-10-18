# Pruebas de la caché viva (sección 4.4): la tabla hash de model/cache_estructuras y su
# resolución por lotes desde adapters/estrategiaRed. El camino vivo no tiene cliente HTTP en las
# pruebas, así que ClienteFalso responde con los datos de FuentePrueba y cuenta cada viaje.
from adapters.ProveedorRed import CacheConDisco, ProveedorRed
from adapters.estrategiaRed import GestorRedPrecarga
from adapters.persistenciaCache import AlmacenamientoPersistenteCache
from model.cache_estructuras import CacheCatalogo
from tests.FuentePrueba import FICHAS, FuentePrueba


def _ficha(idEntidad):
    return {"id": idEntidad, "clase": "objeto", "nombre": idEntidad}


class ClienteFalso:
    """Imita las respuestas del servicio y cuenta solicitudes: permite afirmar cuántos viajes cuesta."""

    def __init__(self, fuente):
        self.fuente = fuente
        self.viajes = 0
        self.lotesCatalogo = []

    def obtenerVersionCatalogo(self):
        return {"version": "v1"}

    def obtenerDatosGenerales(self, idCripta):
        datos = self.fuente.datosGenerales()
        return {"id": datos["id"], "sala_inicial": datos["sala_inicial"],
                "sala_salida": datos["sala_salida"], "presupuesto_solicitudes": 999,
                "total_paginas": 1, "paginas": 1}

    def obtenerEsqueleto(self, idCripta, pagina=1):
        self.viajes += 1
        return {"salas": self.fuente.salas, "pagina": pagina, "total_paginas": 1}

    def obtenerContenidoLote(self, idCripta, salas):
        self.viajes += 1
        salida = []
        for idSala in salas:
            c = self.fuente.contenidos[idSala - 1]
            salida.append({"sala": c["sala"], "enemigos": list(c["enemigos"]),
                           "objetos": list(c["objetos"]), "trampas": list(c["trampas"])})
        return {"contenido": salida}

    def obtenerCatalogoLote(self, idsCatalogo):
        self.viajes += 1
        self.lotesCatalogo.append(list(idsCatalogo))
        return {"entidades": [dict(f) for f in FICHAS if f["id"] in idsCatalogo]}

    def obtenerSolicitudesRealizadas(self):
        return self.viajes

    def cuentaComoRed(self):
        return True


def testLasCubetasCrecenConElTamanoDeLaCache():
    cache = CacheCatalogo(400)
    for i in range(400):
        cache.insertar("ent_%03d" % i, _ficha("ent_%03d" % i))

    assert cache.cantidad_actual == 400
    assert cache.num_cubetas > 53          # las cubetas fijas del diseño anterior se quedaban cortas
    assert max(len(c) for c in cache.cubetas) <= 8
    for i in range(400):
        assert cache.contiene("ent_%03d" % i, False)


def testDesalojaLaMenosUsada():
    cache = CacheCatalogo(2)
    cache.insertar("a", _ficha("a"))
    cache.insertar("b", _ficha("b"))
    cache.obtener("a")                     # "b" pasa a ser la menos usada
    cache.insertar("c", _ficha("c"))

    assert cache.desalojos == 1
    assert cache.contiene("a", False) and cache.contiene("c", False)
    assert not cache.contiene("b", False)


def testLaFichaEnUsoNoSeDesaloja():
    cache = CacheCatalogo(2)
    cache.insertar("a", _ficha("a"))
    cache.insertar("b", _ficha("b"))
    cache.marcar_en_uso("b", 1)            # "a" es la menos usada, pero "b" la referencia el modelo
    cache.insertar("c", _ficha("c"))

    assert cache.contiene("b", False) and cache.contiene("c", False)
    assert not cache.contiene("a", False)


def testCacheConDiscoReleeLaFichaGuardada(tmp_path):
    almacen = AlmacenamientoPersistenteCache(str(tmp_path))
    primera = CacheConDisco(2, almacen, "v1")
    primera.insertar("ent_rata", dict(FICHAS[0]))

    segunda = CacheConDisco(2, almacen, "v1")
    ficha = segunda.obtener("ent_rata")
    assert ficha is not None
    assert ficha.crudo["nombre"] == "Rata gigante"


def testUnHitDeDiscoNoDesalojaUnaFichaEnUso(tmp_path):
    fuente = FuentePrueba(ancho=3, alto=2, semillaCripta=5)
    proveedor = ProveedorRed(ClienteFalso(fuente), "cripta-prueba",
                             capacidadCache=3, directorioCache=str(tmp_path))
    proveedor.fijarFichasEnUso(lambda: ["ent_rata"])
    proveedor.ficha("ent_rata")

    for i in range(5):                     # cinco fichas que solo están en disco
        idEntidad = "itm_suelta_%d" % i
        proveedor.cache.almacen.guardarFichaDisco("v1", idEntidad, _ficha(idEntidad))
        proveedor.ficha(idEntidad)

    assert proveedor.cache.contiene("ent_rata", False)


def testAsegurarCatalogoDeduplicaYOrdenaEnUnViaje():
    cliente = ClienteFalso(FuentePrueba())
    gestor = GestorRedPrecarga(cliente, CacheCatalogo(50))
    ids = ["ent_rata", "itm_daga", "ent_rata", "trp_dardos", "itm_daga", "itm_pocion"]

    gestor.asegurarCatalogo(ids)

    assert len(cliente.lotesCatalogo) == 1
    assert sorted(cliente.lotesCatalogo[0]) == ["ent_rata", "itm_daga", "itm_pocion", "trp_dardos"]
    viajes = cliente.viajes
    gestor.asegurarCatalogo(ids)           # ya están todas en caché: no se vuelve al servicio
    assert cliente.viajes == viajes


def testAsegurarCatalogoCortaLosLotesEnDiez():
    cliente = ClienteFalso(FuentePrueba())
    gestor = GestorRedPrecarga(cliente, CacheCatalogo(50))

    gestor.asegurarCatalogo(["id_%02d" % i for i in range(12)])

    assert [len(lote) for lote in cliente.lotesCatalogo] == [10, 2]


def testDespuesDelLotePedirFichasNoCuestaRed(tmp_path):
    fuente = FuentePrueba(ancho=4, alto=3, semillaCripta=9, enemigosPorSala=2)
    cliente = ClienteFalso(fuente)
    proveedor = ProveedorRed(cliente, "cripta-prueba", capacidadCache=25,
                             directorioCache=str(tmp_path))
    ids = ["ent_rata", "ent_guardian", "ent_errante", "itm_pocion", "trp_dardos"]

    proveedor.asegurarFichas(ids)
    despuesDelLote = cliente.viajes
    for idEntidad in ids:
        proveedor.ficha(idEntidad)

    assert cliente.viajes == despuesDelLote
