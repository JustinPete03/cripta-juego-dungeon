from adapters.estrategiaRed import GestorRedPrecarga
from adapters.persistenciaCache import AlmacenamientoPersistenteCache
from model.Interfaces import ProveedorDatos, SinDatos
from model.Tabla import Conjunto
from model.cache_estructuras import CacheCatalogo, FichaCatalogo


class FichaConCrudo(FichaCatalogo):
    """FichaCatalogo que conserva el dict original: el modelo trabaja con dicts."""
    def __init__(self, crudo):
        FichaCatalogo.__init__(self, crudo)
        self.crudo = crudo


class CacheConDisco(CacheCatalogo):
    """Caché con disco: al insertar guarda; un fallo en RAM intenta disco antes de pedir por red (sección 4.4)."""
    def __init__(self, capacidad, almacen, versionCatalogo):
        CacheCatalogo.__init__(self, capacidad)
        self.almacen = almacen
        self.versionCatalogo = versionCatalogo

    def insertar(self, idEntidad, datos):
        if isinstance(datos, dict):
            self.almacen.guardarFichaDisco(self.versionCatalogo, idEntidad, datos)
            datos = FichaConCrudo(datos)
        CacheCatalogo.insertar(self, idEntidad, datos)

    def contiene(self, idEntidad, registrar_metrica=True):
        if CacheCatalogo.contiene(self, idEntidad, registrar_metrica):
            return True
        crudo = self.almacen.leerFichaDisco(self.versionCatalogo, idEntidad)
        if crudo is None:
            return False
        CacheCatalogo.insertar(self, idEntidad, FichaConCrudo(crudo))
        return True

    def obtener(self, idEntidad):
        ficha = CacheCatalogo.obtener(self, idEntidad)
        if ficha is None:
            crudo = self.almacen.leerFichaDisco(self.versionCatalogo, idEntidad)
            if crudo is not None:
                ficha = FichaConCrudo(crudo)
                CacheCatalogo.insertar(self, idEntidad, ficha)
        return ficha


class ProveedorRed(ProveedorDatos):
    """Une el cliente de Diego (HTTP u offline) con la caché para el modelo (sección 6 Adaptadores)."""
    def __init__(self, cliente, idCripta, capacidadCache=25, directorioCache=".cache_cripta"):
        version = cliente.obtenerVersionCatalogo()["version"]
        self.cache = CacheConDisco(capacidadCache, AlmacenamientoPersistenteCache(directorioCache), version)
        self.gestor = GestorRedPrecarga(cliente, self.cache)
        self.datos, self.salas = self.gestor.inicializarCripta(idCripta)
        self.productorEnUso = None

    def datosGenerales(self):
        return self.datos

    def esqueleto(self):
        return self.salas

    def contenidoSala(self, salaId):
        self._protegerEnUso()
        c = self.gestor.asegurarContenidoSala(salaId, self.salas)
        if c is None:
            raise SinDatos(f"No se pudo obtener el contenido para la sala {salaId}.")
        return {
            "sala": c["sala"],
            "enemigos": list(c.get("enemigos", [])),
            "objetos": list(c.get("objetos", [])),
            "trampas": list(c.get("trampas", [])),
        }

    def ficha(self, tipoId):
        self._protegerEnUso()   # un hit de disco reinserta y podría desalojar una ficha en uso
        ficha = self.cache.obtener(tipoId)
        if ficha is None:  # Ni en RAM ni en disco: única razón de pedir por red (sección 4.4)
            self.gestor.asegurarCatalogo([tipoId])
            ficha = self.cache.obtener(tipoId)
            if ficha is None:
                raise KeyError("Ficha de catálogo inexistente: %s" % tipoId)
        return ficha.crudo

    def asegurarFichas(self, tipoIds):
        self._protegerEnUso()
        self.gestor.asegurarCatalogo(tipoIds)

    def anticipar(self, salaId):
        self._protegerEnUso()
        self.gestor.precargarVecindad(salaId, self.salas)

    def fijarFichasEnUso(self, productor):
        self.productorEnUso = productor

    def _protegerEnUso(self):
        """Marca la caché en una pasada con el conjunto de ids en uso (sección 4.4)."""
        if self.productorEnUso is None:
            return
        enUso = Conjunto()
        for tipoId in self.productorEnUso():
            enUso.agregar(tipoId)
        for cubeta in self.cache.cubetas:
            for entrada in cubeta:
                entrada.referencias_activas = 1 if enUso.contiene(entrada.id_entidad) else 0

    def reporte(self):
        return self.gestor.generarReporteRendimientoRed()