import os 
import json
from utils.logger import MiLogger
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Asumimos que MiLogger ya existe en tu estructura
# from bot.logger import MiLogger 

class GestorCache:
    _instancia = None
    _logger = None
    _ruta_cache_dir = os.path.join(os.getcwd(), 'cache')
    _geo_cache_file = os.path.join(_ruta_cache_dir, 'geo_cache.json')

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(GestorCache, cls).__new__(cls)
            ruta = os.path.dirname(__file__)
            nombre = os.path.basename(__file__)
            cls._logger = MiLogger(ruta, nombre)
        return cls._instancia

    def __init__(self):
        # Usamos el logger de la clase
        self.log = self.__class__._logger

    def getGeoCache(self):
        """Carga el cache actual. Si no existe, devuelve dict vacío."""
        if not os.path.exists(self._geo_cache_file):
            return {}
        try:
            with open(self._geo_cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _guardar_fisicamente(self, cache_completa):
        """Método privado para persistir el diccionario completo."""
        with open(self._geo_cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_completa, f, ensure_ascii=False, indent=4)

    def _extraer_pais_ciudad(self, location):
        """
        Extrae País y Ciudad de forma estructurada usando los metadatos de la API.
        Evita el parseo manual de comas que falla según la precisión del resultado.
        """
        if not location:
            return ["Desconocido", "Desconocido"]

        # 1. Acceso a los atributos estructurados (ArcGIS)
        # ArcGIS devuelve un dict 'attributes' dentro de 'raw' con campos normalizados
        attrs = getattr(location, 'raw', {}).get('attributes', {})
        
        # 2. Extracción de País con Fallbacks
        # Prioridad: Atributo 'Country' -> 'CountryCode' -> Último segmento del address
        pais = attrs.get('Country', attrs.get('CntryName'))
        if not pais:
            pais = location.address.split(',')[-1].strip()

        # 3. Extracción de Ciudad/Provincia con Fallbacks
        # Prioridad: 'City' (Ciudad) -> 'Region' (Provincia/Estado) -> Primera parte del address
        ciudad = attrs.get('City', attrs.get('Region', attrs.get('District')))
        if not ciudad:
            ciudad = location.address.split(',')[0].strip()

        return [pais, ciudad]

    def actualizar_misses(self, lista_misses):
        cache_actual = self.getGeoCache()
        
        if not lista_misses:
            return cache_actual

        self._logger.info(f"Procesando {len(lista_misses)} nuevas ubicaciones...")

        geolocator = Nominatim(user_agent="geo_structured_cleaner", timeout=10)
        geocode = RateLimiter(geolocator.geocode, 
            min_delay_seconds=1.5, 
            max_retries=3, 
            error_wait_seconds=2.0
            )
        
        cambios = False
        for i, texto in enumerate(lista_misses):
            try:
                location = geocode(texto)
                # GUARDAMOS LISTA: [País, Provincia]
                cache_actual[texto] = self._extraer_pais_ciudad(location)
                cambios = True
            except Exception as e:
                self._logger.error(f"Error en {texto}: {e}")
                cache_actual[texto] = ["Error", "Error"]
            
            if i % 25 == 0 and cambios:
                self._guardar_fisicamente(cache_actual)
        
        if cambios:
            self._guardar_fisicamente(cache_actual)
            
        return cache_actual
    
gestorCache = GestorCache()