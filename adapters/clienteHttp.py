import time
import uuid
import requests
from adapters.clienteCripta import ClienteCripta


class ClienteHTTP(ClienteCripta):

    def __init__(self, baseUrl: str, timeout: int = 10):
        self.baseUrl = baseUrl.rstrip("/")
        self.timeout = timeout
        # El UUID (Identificador único) se genera una sola vez por ejecución y se reutiliza (sección Encabezado obligatorio)
        self.clientId = str(uuid.uuid4())
        self.headers = {"X-Cripta-Client-Id": self.clientId}
        # Toda solicitud HTTP cuenta para el presupuesto (incluyendo reintentos 429)
        self.solicitudesRealizadas = 0
        self._versionCatalogo = None

    # Compatibilidad con atributos previos
    @property
    def base_url(self):
        return self.baseUrl

    @property
    def client_id(self):
        return self.clientId

    @property
    def solicitudes_realizadas(self):
        return self.solicitudesRealizadas

    # Implementación de peticiones seguras con manejo de errores y reintentos 429
    def _hacerPeticionSegura(self, ruta: str) -> dict:
        url = f"{self.baseUrl}{ruta}"
        maxReintentos429 = 5
        reintentosActuales = 0

        while True:
            try:
                # Cada solicitud cuenta para el presupuesto de solicitudes (sección 5.1)
                self.solicitudesRealizadas += 1
                respuesta = requests.get(
                    url, headers=self.headers, timeout=self.timeout
                )

                if respuesta.status_code == 200:
                    return respuesta.json()

                elif respuesta.status_code == 429:  # Límite de frecuencia (Too Many Requests)
                    reintentosActuales += 1
                    if reintentosActuales > maxReintentos429:
                        raise RuntimeError(
                            f"[Red] Se excedió el número máximo de reintentos ({maxReintentos429}) por HTTP 429 en '{ruta}'."
                        )

                    tiempoEspera = 1
                    try:
                        datosError = respuesta.json()
                        tiempoEspera = datosError.get("reintentar_en", 1)
                    except Exception:
                        if "Retry-After" in respuesta.headers:
                            try:
                                tiempoEspera = int(respuesta.headers["Retry-After"])
                            except ValueError:
                                tiempoEspera = 1

                    print(f"[Red] HTTP 429 (Límite de frecuencia). Esperando {tiempoEspera}s...")
                    time.sleep(tiempoEspera)
                    continue

                else:
                    # Manejo de otros errores HTTP con contexto (sección 3.1)
                    raise RuntimeError(
                        f"Error HTTP {respuesta.status_code} en la operación GET '{ruta}'. "
                        f"Detalle: {respuesta.text}"
                    )
            # Manejo de errores de conexión y tiempo de espera
            except requests.exceptions.RequestException as e:
                raise RuntimeError(
                    f"Fallo de conexión de red al consultar '{url}'. "
                    f"Verifique su conexión. Detalle técnico: {e}"
                )

    _hacer_peticion_segura = _hacerPeticionSegura

    # Implementación de la interfaz ClienteCripta en camelCase
    def obtenerListaCriptas(self) -> dict:
        return self._hacerPeticionSegura("/criptas")

    def obtenerDatosGenerales(self, idCripta: str) -> dict:
        return self._hacerPeticionSegura(f"/criptas/{idCripta}")

    def obtenerVersionCripta(self, idCripta: str) -> dict:
        return self._hacerPeticionSegura(f"/criptas/{idCripta}/version")

    def obtenerVersionCatalogo(self) -> dict:
        if self._versionCatalogo is None:
            self._versionCatalogo = self._hacerPeticionSegura("/catalogo/version")
        return self._versionCatalogo

    def obtenerEsqueleto(self, idCripta: str, pagina: int = 1) -> dict:
        return self._hacerPeticionSegura(f"/criptas/{idCripta}/salas?pagina={pagina}")

    def obtenerContenidoLote(self, idCripta: str, salas: list) -> dict:
        if not salas:
            return {"contenido": []}
        if len(salas) > 10:
            raise ValueError("El lote de contenido no puede superar las 10 salas por solicitud.")
        salasStr = ",".join(map(str, salas))
        return self._hacerPeticionSegura(f"/criptas/{idCripta}/contenido?salas={salasStr}")

    def obtenerCatalogoLote(self, idsCatalogo: list) -> dict:
        if not idsCatalogo:
            return {"entidades": []}
        if len(idsCatalogo) > 10:
            raise ValueError("El lote de catálogo no puede superar los 10 IDs por solicitud.")
        idsStr = ",".join(idsCatalogo)
        return self._hacerPeticionSegura(f"/catalogo?ids={idsStr}")

    def obtenerSolicitudesRealizadas(self) -> int:
        return self.solicitudesRealizadas

    # Alias en snake_case
    obtener_lista_criptas = obtenerListaCriptas
    obtener_datos_generales = obtenerDatosGenerales
    obtener_version_cripta = obtenerVersionCripta
    obtener_version_catalogo = obtenerVersionCatalogo
    obtener_esqueleto = obtenerEsqueleto
    obtener_contenido_lote = obtenerContenidoLote
    obtener_catalogo_lote = obtenerCatalogoLote
    obtener_solicitudes_realizadas = obtenerSolicitudesRealizadas