
import os
from pathlib import Path

class gestorArchivos:
    def __init__(self, ruta_base):
        self.ruta_base = Path(ruta_base)
    
    # Método para obtener el último archivo CSV de una carpeta específica
    def obtenerUltimoArchivoCSV(self,carpeta):

        ruta = self.ruta_base + carpeta

        try:
            # Listamos todos los archivos CSV en la carpeta dada
            archivos_csv = list(ruta.glob('*.csv'))
            
            if not archivos_csv:
                return None

            # Buscamos el archivo CSV con la fecha de modificación (mtime) más reciente
            reciente_csv = max(archivos_csv, key=lambda f: os.path.getmtime(f))
            
            return reciente_csv
            
        except Exception as e:
            return f"Error al explorar: {e}"