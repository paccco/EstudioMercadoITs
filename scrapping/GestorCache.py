import os 
import json
from bot.logger import MiLogger
from geopy.geocoders import ArcGIS
from geopy.extra.rate_limiter import RateLimiter

# Asumimos que MiLogger ya existe en tu estructura
# from bot.logger import MiLogger 

class GestorCache:
    _instancia = None
    _logger = None
    _ruta_cache_dir = os.path.join(os.getcwd(), 'cache')
    _geo_cache_file = os.path.join(_ruta_cache_dir, 'geo_cache.json')

    def __new__(cls):
        if not cls._instancia:
            cls._instancia = super(GestorCache, cls).__new__(cls)
            cls._logger = MiLogger(os.path.dirname(__file__), os.path.basename(__file__))
        return cls._instancia

    def __init__(self):
        # Asegurar que la carpeta cache existe al instanciar
        if not os.path.exists(self._ruta_cache_dir):
            os.makedirs(self._ruta_cache_dir)

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

    def _extraer_pais_provincia(self, location):
        """
        Lógica de parsing para ArcGIS: 
        Retorna [País, Provincia/Estado]
        """
        if not location:
            return ["No encontrado", "No encontrado"]
        
        # Ejemplo: "Sevilla, Andalucía, ESP" -> ["Sevilla", "Andalucía", "ESP"]
        partes = [p.strip() for p in location.address.split(',')]
        
        # ArcGIS suele poner el País al final y la Provincia/Comunidad justo antes
        pais = partes[-1] if len(partes) >= 1 else "Desconocido"
        provincia = partes[-2] if len(partes) >= 2 else pais # Si solo hay uno, repetimos
        
        return [pais, provincia]

    def actualizar_misses(self, lista_misses):
        cache_actual = self.getGeoCache()
        
        if not lista_misses:
            return cache_actual

        self._logger.info(f"Procesando {len(lista_misses)} nuevas ubicaciones...")
        
        geolocator = ArcGIS(user_agent="geo_structured_cleaner")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.5)
        
        cambios = False
        for i, texto in enumerate(lista_misses):
            try:
                location = geocode(texto)
                # GUARDAMOS LISTA: [País, Provincia]
                cache_actual[texto] = self._extraer_pais_provincia(location)
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