from abc import ABC, abstractmethod
#Clase abstracta que define la interfaz para interactuar con el servidor de criptas.

class ClienteCripta(ABC):

    @abstractmethod
    def obtener_lista_criptas(self) -> dict:
        pass

    @abstractmethod
    def obtener_datos_generales(self, id_cripta: str) -> dict:
        pass

    @abstractmethod
    def obtener_version_cripta(self, id_cripta: str) -> dict:
        pass

    @abstractmethod
    def obtener_version_catalogo(self) -> dict:
        pass

    @abstractmethod
    def obtener_esqueleto(self, id_cripta: str, pagina: int = 1) -> dict:
        pass

    @abstractmethod
    def obtener_contenido_lote(self, id_cripta: str, salas: list) -> dict:
        pass

    @abstractmethod
    def obtener_catalogo_lote(self, ids_catalogo: list) -> dict:
        pass

    @abstractmethod
    def obtener_solicitudes_realizadas(self) -> int:
        pass