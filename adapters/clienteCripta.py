from abc import ABC, abstractmethod

# Clase abstracta que define la interfaz para interactuar con el servidor de criptas.
class ClienteCripta(ABC):

    @abstractmethod
    def obtenerListaCriptas(self) -> dict:
        pass

    @abstractmethod
    def obtenerDatosGenerales(self, idCripta: str) -> dict:
        pass

    @abstractmethod
    def obtenerVersionCripta(self, idCripta: str) -> dict:
        pass

    @abstractmethod
    def obtenerVersionCatalogo(self) -> dict:
        pass

    @abstractmethod
    def obtenerEsqueleto(self, idCripta: str, pagina: int = 1) -> dict:
        pass

    @abstractmethod
    def obtenerContenidoLote(self, idCripta: str, salas: list) -> dict:
        pass

    @abstractmethod
    def obtenerCatalogoLote(self, idsCatalogo: list) -> dict:
        pass

    @abstractmethod
    def obtenerSolicitudesRealizadas(self) -> int:
        pass

    # Una respuesta leída del almacenamiento local no consume presupuesto (sección 3.4), así que
    # el modo offline redefine esto a False para que la estrategia de red no se autocensure.
    def cuentaComoRed(self) -> bool:
        return True

    # Alias en snake_case para compatibilidad retroactiva si algún módulo externo aún los invoca
    obtener_lista_criptas = obtenerListaCriptas
    obtener_datos_generales = obtenerDatosGenerales
    obtener_version_cripta = obtenerVersionCripta
    obtener_version_catalogo = obtenerVersionCatalogo
    obtener_esqueleto = obtenerEsqueleto
    obtener_contenido_lote = obtenerContenidoLote
    obtener_catalogo_lote = obtenerCatalogoLote
    obtener_solicitudes_realizadas = obtenerSolicitudesRealizadas