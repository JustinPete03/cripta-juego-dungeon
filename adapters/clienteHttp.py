import json
import logging
import time
import uuid
import requests
from adapters.clienteCripta import ClienteCripta

logger = logging.getLogger("Cripta.Red")


class ErrorRedCripta(RuntimeError):
    """Excepción base para fallos de red en el cliente de la Cripta."""
    pass


class ErrorConexionServidor(ErrorRedCripta):
    """Fallo de conectividad física, resolución DNS o conexión rechazada por el servidor."""
    pass


class ErrorTiempoEspera(ErrorRedCripta):
    """Tiempo de espera (timeout) agotado al intentar comunicar con el servidor."""
    pass


class ErrorLimiteFrecuenciaExcedido(ErrorRedCripta):
    """Se superó el número máximo de reintentos tras recibir HTTP 429 (Too Many Requests)."""
    pass


class ErrorRespuestaInvalida(ErrorRedCripta):
    """El servidor devolvió una respuesta con código 200 pero contenido no decodificable como JSON."""
    pass


class ErrorHttp(ErrorRedCripta):
    """Error HTTP con código de estado devuelto por el servidor (4xx o 5xx)."""

    def __init__(self, codigo: int, ruta: str, detalle: str):
        self.codigo = codigo
        self.ruta = ruta
        self.detalle = detalle
        super().__init__(f"Error HTTP {codigo} en GET '{ruta}': {detalle}")


class ClienteHTTP(ClienteCripta):

    def __init__(self, baseUrl: str, timeout: int = 10):
        self.baseUrl = baseUrl.rstrip("/")
        self.timeout = timeout
        # El UUID (Identificador único) se genera una sola vez por ejecución y se reutiliza (sección Encabezado obligatorio)
        self.clientId = str(uuid.uuid4())
        self.headers = {
            "X-Cripta-Client-Id": self.clientId,
            "Accept": "application/json",
            "User-Agent": "CriptaClient/2.0-Python",
        }
        # Toda solicitud HTTP cuenta para el presupuesto (incluyendo reintentos 429)
        self.solicitudesRealizadas = 0
        self._versionCatalogo = None
        logger.info(f"ClienteHTTP inicializado hacia {self.baseUrl} con Client-Id: {self.clientId} (timeout={self.timeout}s)")

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

    # Implementación de peticiones seguras con manejo robusto de errores, reintentos 429 y logging
    def _hacerPeticionSegura(self, ruta: str) -> dict:
        url = f"{self.baseUrl}{ruta}"
        maxReintentos429 = 5
        reintentosActuales = 0

        while True:
            t0 = time.perf_counter()
            self.solicitudesRealizadas += 1
            numSolicitud = self.solicitudesRealizadas

            logger.debug(f"[Req #{numSolicitud}] Enviando GET {url} | Headers: {self.headers}")

            try:
                respuesta = requests.get(
                    url, headers=self.headers, timeout=self.timeout
                )
                duracionMs = (time.perf_counter() - t0) * 1000.0

                if respuesta.status_code == 200:
                    try:
                        datos = respuesta.json()
                        tamanoBytes = len(respuesta.content)
                        logger.info(
                            f"[Req #{numSolicitud}] 200 OK en GET '{ruta}' "
                            f"({duracionMs:.1f}ms, {tamanoBytes} bytes)"
                        )
                        return datos
                    except (json.JSONDecodeError, ValueError) as errJson:
                        logger.error(
                            f"[Req #{numSolicitud}] Fallo al decodificar JSON de '{url}': {errJson}. "
                            f"Cuerpo recibido: {respuesta.text[:200]!r}"
                        )
                        raise ErrorRespuestaInvalida(
                            f"Respuesta no válida del servidor en GET '{ruta}': no se pudo parsear como JSON. "
                            f"Detalle: {errJson}"
                        ) from errJson

                elif respuesta.status_code == 429:  # Límite de frecuencia (Too Many Requests)
                    reintentosActuales += 1
                    tiempoEspera = 1
                    try:
                        datosError = respuesta.json()
                        tiempoEspera = int(datosError.get("reintentar_en", 1))
                    except Exception:
                        if "Retry-After" in respuesta.headers:
                            try:
                                tiempoEspera = int(respuesta.headers["Retry-After"])
                            except ValueError:
                                tiempoEspera = 1

                    tiempoEspera = max(1, tiempoEspera)

                    if reintentosActuales > maxReintentos429:
                        msg = (
                            f"[Red] Se excedió el número máximo de reintentos ({maxReintentos429}) "
                            f"por HTTP 429 en '{ruta}'."
                        )
                        logger.error(f"[Req #{numSolicitud}] {msg}")
                        raise ErrorLimiteFrecuenciaExcedido(msg)

                    logger.warning(
                        f"[Req #{numSolicitud}] HTTP 429 (Límite de frecuencia) en '{ruta}'. "
                        f"Reintento {reintentosActuales}/{maxReintentos429}. "
                        f"Esperando {tiempoEspera}s antes de reintentar..."
                    )
                    time.sleep(tiempoEspera)
                    continue

                elif respuesta.status_code == 404:
                    logger.error(
                        f"[Req #{numSolicitud}] HTTP 404 No Encontrado en '{ruta}'. "
                        f"Verifique la existencia de la cripta o recurso solicitado."
                    )
                    raise ErrorHttp(
                        404, ruta,
                        f"Recurso no encontrado: {respuesta.text.strip() or '404 Not Found'}"
                    )

                elif 400 <= respuesta.status_code < 500:
                    logger.error(
                        f"[Req #{numSolicitud}] Error de cliente HTTP {respuesta.status_code} en '{ruta}': "
                        f"{respuesta.text[:250]}"
                    )
                    raise ErrorHttp(
                        respuesta.status_code, ruta,
                        f"Petición rechazada ({respuesta.status_code}): {respuesta.text.strip()}"
                    )

                elif respuesta.status_code >= 500:
                    logger.error(
                        f"[Req #{numSolicitud}] Error interno del servidor HTTP {respuesta.status_code} en '{ruta}': "
                        f"{respuesta.text[:250]}"
                    )
                    raise ErrorHttp(
                        respuesta.status_code, ruta,
                        f"Fallo del servidor ({respuesta.status_code}): {respuesta.text.strip()}"
                    )

                else:
                    logger.error(
                        f"[Req #{numSolicitud}] Código HTTP inesperado {respuesta.status_code} en '{ruta}'."
                    )
                    raise ErrorHttp(
                        respuesta.status_code, ruta,
                        f"Código de respuesta HTTP inesperado: {respuesta.status_code}"
                    )

            except requests.exceptions.Timeout as eTimeout:
                duracionMs = (time.perf_counter() - t0) * 1000.0
                logger.error(
                    f"[Req #{numSolicitud}] Timeout ({self.timeout}s) al consultar '{url}' "
                    f"después de {duracionMs:.1f}ms: {eTimeout}"
                )
                raise ErrorTiempoEspera(
                    f"Tiempo de espera agotado ({self.timeout}s) al conectar con '{url}'. "
                    f"El servidor tardó demasiado en responder."
                ) from eTimeout

            except requests.exceptions.ConnectionError as eConn:
                duracionMs = (time.perf_counter() - t0) * 1000.0
                logger.error(
                    f"[Req #{numSolicitud}] Fallo de conexión hacia '{url}' tras {duracionMs:.1f}ms: {eConn}"
                )
                raise ErrorConexionServidor(
                    f"No se pudo establecer conexión con el servidor en '{url}'. "
                    f"Compruebe que el servicio esté en línea y su conexión de red. Detalle: {eConn}"
                ) from eConn

            except requests.exceptions.RequestException as eReq:
                duracionMs = (time.perf_counter() - t0) * 1000.0
                logger.error(
                    f"[Req #{numSolicitud}] Excepción de red genérica en '{url}' tras {duracionMs:.1f}ms: {eReq}"
                )
                raise ErrorRedCripta(
                    f"Fallo de conexión de red al consultar '{url}'. "
                    f"Verifique su conexión. Detalle técnico: {eReq}"
                ) from eReq

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

    def obtenerLlaves(self, idCripta: str) -> dict:
        return self._hacerPeticionSegura(f"/criptas/{idCripta}/llaves")

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
    obtener_llaves = obtenerLlaves
    obtener_solicitudes_realizadas = obtenerSolicitudesRealizadas
