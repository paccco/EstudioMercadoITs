import os
from pathlib import Path
from typing import Optional, Union
from utils.logger import MiLogger

class GestorArchivos:
    """Gestor de archivos implementado con patrón Singleton y Pathlib."""
    _instancia = None

    def __new__(cls, *args, **kwargs):
        if not cls._instancia:
            cls._instancia = super(GestorArchivos, cls).__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self, ruta_base: Union[str, Path] = "."):
        if not self._inicializado:
            self._logger = MiLogger(str(Path(__file__).parent), Path(__file__).name)
            self._logger.info("Inicializando GestorArchivos...")
            self.ruta_base = Path(ruta_base).resolve()
            self._inicializado = True

    def obtenerUltimoArchivo(self, carpeta: str = "", tipo_archivo: Optional[str] = None) -> Optional[Path]:
        """
        Navega recursivamente y obtiene el último archivo modificado.
        """
        ruta_absoluta = (self.ruta_base / carpeta).resolve()

        if not ruta_absoluta.is_dir():
            self._logger.warning(f"La carpeta '{ruta_absoluta}' no existe.")
            return None

        patron = "**/*" if tipo_archivo is None else f"**/*.{tipo_archivo}"
        archivos = [f for f in ruta_absoluta.rglob(patron) if f.is_file()]

        if not archivos:
            return None

        return max(archivos, key=lambda f: f.stat().st_mtime)
    
    def leerArchivo(self, ruta_archivo: Union[str, Path, None], n_tail: Optional[int] = None) -> str:
        if ruta_archivo is None:
            return "No se ha proporcionado una ruta válida."
            
        ruta = (self.ruta_base / ruta_archivo).resolve()
        
        if not ruta.is_file():
            return "No se encontró el archivo."
        
        try:
            with ruta.open('r', encoding='utf-8') as f:
                if n_tail is None:
                    return f.read()
                
                lineas = f.readlines()
                return "".join(lineas[-n_tail:])
        except Exception as e:
            self._logger.error(f"Error leyendo archivo {ruta}: {e}")
            return f"Error leyendo el archivo: {e}"

# Creamos una instancia global del gestor de archivos
gestor = GestorArchivos(".")
