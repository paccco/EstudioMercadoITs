import os 
from pathlib import Path
from logger import MiLogger

class GestorArchivos: # Sugerencia: Usar CamelCase para clases
    _instancia = None
    _logger = None

    def __new__(cls, *args, **kwargs):
        if not cls._logger:
            cls._logger = MiLogger(os.path.dirname(__file__), os.path.basename(__file__))
            cls._logger.info("Inicializando GestorArchivos...")
        if not cls._instancia:
            cls._instancia = super(GestorArchivos, cls).__new__(cls)
        return cls._instancia

    def __init__(self, ruta_base):
        # Cuidado: en un Singleton el __init__ se ejecuta cada vez que "creas" el objeto
        # Solo inicializamos si no se ha hecho antes
        if not hasattr(self, 'inicializado'):
            self.ruta_base = Path(ruta_base)
            self.inicializado = True
    
    def getFatherDir(self, archivo):
        # Obtiene el directorio padre del directorio del archivo dado
        return os.path.dirname(os.path.dirname(os.path.abspath(archivo)))

    def obtenerUltimoArchivo(self, carpeta="", tipo_archivo=None):
        """
        Navega recursivamente como un árbol de directorios y obtiene 
        el último archivo modificado del tipo especificado.
        
        Args:
            carpeta: Directorio base desde donde buscar (relativo a ruta_base)
            tipo_archivo: Extensión del archivo a buscar (sin el punto)
        
        Returns:
            Path: El archivo más reciente encontrado, o None si no hay archivos
        """
        # Unimos las rutas de forma correcta con /
        ruta = self.ruta_base / carpeta if carpeta else self.ruta_base

        if not ruta.is_dir():
            return None

        # Buscamos archivos recursivamente usando rglob (navega como árbol)
        patron = "**/*" if tipo_archivo is None else f"**/*.{tipo_archivo}"
        archivos = list(ruta.glob(patron))
        
        # Filtramos solo archivos (no directorios)
        archivos = [f for f in archivos if f.is_file()]
        
        if not archivos:
            return None
        
        # Usamos la propiedad .stat().st_mtime de pathlib
        return max(archivos, key=lambda f: f.stat().st_mtime)
    
    def leerArchivo(self, ruta_archivo, n_tail=None):
        ruta = self.ruta_base / ruta_archivo
        if not os.path.isfile(ruta):
            return "No se encontró el archivo."
        with open(ruta, 'r') as f:
            contenido = f.read()
            if n_tail is not None:
                contenido = '\n'.join(contenido.split('\n')[-n_tail:])
            return contenido
    

# Creamos una instancia global del gestor de archivos
gestor = GestorArchivos("../")
