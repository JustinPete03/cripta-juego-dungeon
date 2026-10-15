import time
import uuid
from adapters.cliente_cripta import ClienteCripta
import requests


class ClienteHTTP(ClienteCripta):

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # El UUID (Identificador único) se genera una sola vez por ejecución y se reutiliza
        self.client_id = str(uuid.uuid4())
        self.headers = {"X-Cripta-Client-Id": self.client_id}
        # Toda solicitud HTTP cuenta para el presupuesto (incluyendo reintentos 429)
        self.solicitudes_realizadas = 0
    
    # Implementación de la interfaz ClienteCripta con manejo de errores y reintentos
    def _hacer_peticion_segura(self, ruta: str) -> dict:
        url = f"{self.base_url}{ruta}"

        while True:
            try:
                # Cada solicitud cuenta para el presupuesto de solicitudes
                self.solicitudes_realizadas += 1
                respuesta = requests.get(
                    url, headers=self.headers, timeout=self.timeout
                )
        
                if respuesta.status_code == 200: 
                    return respuesta.json()

                elif respuesta.status_code == 429: # Manejo de límite de frecuencia (Too Many Requests)
                    #Esperar el tiempo indicado sin caer ni avanzar reloj virtual
                    datos_error = respuesta.json()
                    tiempo_espera = datos_error.get("reintentar_en", 1) # Si el servidor no indica tiempo, esperar 1 segundo por defecto
                    print(f"[Red] HTTP 429 (Límite de frecuencia). Esperando {tiempo_espera}s...")
                    time.sleep(tiempo_espera)
                    continue

                else:
                    # Manejo de otros errores HTTP
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
# Implementación de la interfaz ClienteCripta
    def obtener_lista_criptas(self) -> dict:
        return self._hacer_peticion_segura("/criptas")

    def obtener_datos_generales(self, id_cripta: str) -> dict:
        return self._hacer_peticion_segura(f"/criptas/{id_cripta}")

    def obtener_version_cripta(self, id_cripta: str) -> dict:
        return self._hacer_peticion_segura(f"/criptas/{id_cripta}/version")

    def obtener_version_catalogo(self) -> dict:
        return self._hacer_peticion_segura("/catalogo/version")

    def obtener_esqueleto(self, id_cripta: str, pagina: int = 1) -> dict:
        return self._hacer_peticion_segura(f"/criptas/{id_cripta}/salas?pagina={pagina}")

    def obtener_contenido_lote(self, id_cripta: str, salas: list) -> dict:
        if not salas:
            return {"contenido": []}
        if len(salas) > 10:
            raise ValueError("El lote de contenido no puede superar las 10 salas por solicitud.")
        salas_str = ",".join(map(str, salas))
        return self._hacer_peticion_segura(f"/criptas/{id_cripta}/contenido?salas={salas_str}")

    def obtener_catalogo_lote(self, ids_catalogo: list) -> dict:
        if not ids_catalogo:
            return {"entidades": []}
        if len(ids_catalogo) > 10:
            raise ValueError("El lote de catálogo no puede superar los 10 IDs por solicitud.")
        ids_str = ",".join(ids_catalogo)
        return self._hacer_peticion_segura(f"/catalogo?ids={ids_str}")

    def obtener_solicitudes_realizadas(self) -> int:
        return self.solicitudes_realizadas