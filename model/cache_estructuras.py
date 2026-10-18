class FichaCatalogo:
 # Representa la ficha de un enemigo, objeto o trampa en el catálogo del juego.
    def __init__(self, json_dict: dict):
        self.id = json_dict.get("id", "")
        self.clase = json_dict.get("clase", "")
        self.nombre = json_dict.get("nombre", "")
        # Estadísticas de enemigos 
        self.vida_max = json_dict.get("vida_max", 0)
        self.ataque = json_dict.get("ataque", 0)
        self.defensa = json_dict.get("defensa", 0)
        self.velocidad = json_dict.get("velocidad", 100)
        self.comportamiento = json_dict.get("comportamiento", "")
        self.suelta = list(json_dict.get("suelta", []))
        self.regeneracion = json_dict.get("regeneracion", 0)
        # Atributos de objetos y trampas 
        self.peso = json_dict.get("peso", 0)
        self.valor = json_dict.get("valor", 0)
        self.ataque_bonus = json_dict.get("ataque_bonus", 0)
        self.defensa_bonus = json_dict.get("defensa_bonus", 0)
        self.cura = json_dict.get("cura", 0)
        self.modificador_velocidad = json_dict.get("modificador_velocidad", 0)
        self.duracion = json_dict.get("duracion", 0)
        self.abre = json_dict.get("abre", "")
        self.dano = json_dict.get("daño", json_dict.get("dano", 0))
        self.rearme = json_dict.get("rearme", 300)

# Entrada de la caché que contiene la ficha de catálogo y metadatos para LRU y referencias activas.
class EntradaCache:
    def __init__(
        self, id_entidad: str, datos_ficha: FichaCatalogo, ultimo_acceso: int
    ):
        self.id_entidad = id_entidad
        self.datos_ficha = datos_ficha
        self.ultimo_acceso = ultimo_acceso
        # Si es > 0, la ficha está "en uso" y no puede desalojarse (sección 4.4)
        self.referencias_activas = 0

# cache de fichas de catálogo con política LRU y contadores de aciertos o fallos segun coresponda. Se usa para evitar descargas repetidas de fichas de enemigos, objetos y trampas.
class CacheCatalogo:
    def __init__(self, capacidad_maxima: int = 25, num_cubetas: int = 53):
        self.capacidad_maxima = capacidad_maxima
        self.num_cubetas = num_cubetas
        self.cubetas = [[] for _ in range(self.num_cubetas)] # Lista de listas para manejar colisiones con encadenamiento
        self.cantidad_actual = 0
        self.contador_operaciones = 0
        self.aciertos = 0
        self.fallos = 0

    def _hash(self, clave: str) -> int: #Función hash simple para distribuir fichas en cubetas, usando el algoritmo djb2.
        valor = 5381
        for caracter in clave: valor = ((valor << 5) + valor) + ord(caracter)
        return valor % self.num_cubetas

    def contiene(self, id_entidad: str, registrar_metrica: bool = True) -> bool:
        # Verifica si la ficha está en la caché y actualiza el contador de aciertos o fallos según corresponda.
        self.contador_operaciones += 1
        indice = self._hash(id_entidad)
        for entrada in self.cubetas[indice]:
            if entrada.id_entidad == id_entidad:
                entrada.ultimo_acceso = self.contador_operaciones
                if registrar_metrica: self.aciertos += 1
                return True
        if registrar_metrica: self.fallos += 1
        return False
# Obtiene la ficha de catálogo de la caché si existe, actualizando el contador de aciertos o fallos y el último acceso para LRU.
    def obtener(self, id_entidad: str) -> FichaCatalogo | None:
        self.contador_operaciones += 1
        indice = self._hash(id_entidad)
        for entrada in self.cubetas[indice]:
            if entrada.id_entidad == id_entidad:
                entrada.ultimo_acceso = self.contador_operaciones
                self.aciertos += 1
                return entrada.datos_ficha
        self.fallos += 1
        return None
# Inserta una ficha de catálogo en la caché, desalojando la menos usada si se alcanza la capacidad máxima. Convierte dict a FichaCatalogo si es necesario.
    def insertar(self, id_entidad: str, datos_ficha: FichaCatalogo | dict):
        if isinstance(datos_ficha, dict): datos_ficha = FichaCatalogo(datos_ficha)
        self.contador_operaciones += 1
        indice = self._hash(id_entidad)
        # Si ya existe, actualizamos
        for entrada in self.cubetas[indice]:
            if entrada.id_entidad == id_entidad:
                entrada.datos_ficha = datos_ficha
                entrada.ultimo_acceso = self.contador_operaciones
                return

        # Si alcanzamos el tope (--cache-size), desalojamos una ficha que NO esté en uso 
        if self.cantidad_actual >= self.capacidad_maxima: self._desalojar_menos_usada()
        nueva = EntradaCache(id_entidad, datos_ficha, self.contador_operaciones)
        self.cubetas[indice].append(nueva)
        self.cantidad_actual += 1
# Marca una ficha como "en uso" o libera su referencia activa, para evitar desalojarla mientras esté en uso. Se puede usar delta positivo o negativo para incrementar o decrementar el contador de referencias activas.
    def marcar_en_uso(self, id_entidad: str, delta: int):
        indice = self._hash(id_entidad)
        for entrada in self.cubetas[indice]:
            if entrada.id_entidad == id_entidad:
                entrada.referencias_activas = max(0, entrada.referencias_activas + delta)
                return
# Desaloja la ficha con menor 'ultimo_acceso' y referencias_activas == 0, siguiendo la política LRU. Devuelve el ID desalojado o None si no hay candidata.
    def _desalojar_menos_usada(self) -> str | None:
        candidata_cubeta = -1
        candidata_pos = -1
        menor_acceso = None
        for i in range(self.num_cubetas):
            cubeta = self.cubetas[i]
            for j in range(len(cubeta)):
                entrada = cubeta[j]
                if entrada.referencias_activas == 0:
                    if (
                        menor_acceso is None
                        or entrada.ultimo_acceso < menor_acceso
                    ):
                        menor_acceso = entrada.ultimo_acceso
                        candidata_cubeta = i
                        candidata_pos = j
        if candidata_cubeta != -1:
            eliminada = self.cubetas[candidata_cubeta].pop(candidata_pos)
            self.cantidad_actual -= 1
            return eliminada.id_entidad
        return None

# El registro de salas descargadas mantiene un hash de salas con encadenamiento para evitar descargas repetidas y mejorar el rendimiento de la red.
class RegistroSalas:
    def __init__(self, num_cubetas: int = 31):
        self.num_cubetas = num_cubetas
        self.cubetas = [[] for _ in range(self.num_cubetas)]

    def _hash(self, id_sala: int) -> int: return id_sala % self.num_cubetas

    def contiene(self, id_sala: int) -> bool:
        for par in self.cubetas[self._hash(id_sala)]:
            if par[0] == id_sala: return True
        return False

    def guardar(self, id_sala: int, contenido: dict):
        cubeta = self.cubetas[self._hash(id_sala)]
        for par in cubeta:
            if par[0] == id_sala:
                par[1] = contenido
                return
        cubeta.append([id_sala, contenido])

    def obtener(self, id_sala: int) -> dict | None:
        for par in self.cubetas[self._hash(id_sala)]:
            if par[0] == id_sala:return par[1]
        return None