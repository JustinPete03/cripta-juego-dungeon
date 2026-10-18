from adapters.estrategiaRed import GestorRedPrecarga
from adapters.persistenciaCache import AlmacenamientoPersistenteCache
from model.Interfaces import ProveedorDatos
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
        self.enUso = None

    def datosGenerales(self):
        return self.datos

    def esqueleto(self):
        return self.salas

    def contenidoSala(self, salaId):
        self._protegerEnUso()
        c = self.gestor.asegurarContenidoSala(salaId, self.salas)
        if c is None:
            raise KeyError(f"No se pudo obtener el contenido para la sala {salaId}.")
        return {
            "sala": c["sala"],
            "enemigos": list(c.get("enemigos", [])),
            "objetos": list(c.get("objetos", [])),
            "trampas": list(c.get("trampas", [])),
        }

    def ficha(self, tipoId):
        ficha = self.cache.obtener(tipoId)
        if ficha is None:  # Ni en RAM ni en disco: única razón de pedir por red (sección 4.4)
            self._protegerEnUso()
            respuesta = self.gestor.cliente.obtenerCatalogoLote([tipoId])
            for f in respuesta.get("entidades", []):
                self.cache.insertar(f["id"], f)
            ficha = self.cache.obtener(tipoId)
            if ficha is None:
                raise KeyError("Ficha de catálogo inexistente: %s" % tipoId)
        return ficha.crudo

    def anticipar(self, salaId):
        self._protegerEnUso()
        self.gestor.precargarVecindad(salaId, self.salas)

    def fijarPredicadoEnUso(self, predicado):
        self.enUso = predicado

    def _protegerEnUso(self):
        """Traduce el predicado del modelo (sección 4.4) a las referencias que respeta la caché."""
        if self.enUso is None:
            return
        for cubeta in self.cache.cubetas:
            for entrada in cubeta:
                entrada.referencias_activas = 1 if self.enUso(entrada.id_entidad) else 0

    def reporte(self):
        return self.gestor.generarReporteRendimientoRed()