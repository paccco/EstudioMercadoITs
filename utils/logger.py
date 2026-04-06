import logging
from pathlib import Path
from datetime import date
from typing import Union, Any

class MiLogger:
    """Clase para la gestión centralizada de logs del proyecto."""
    
    def __init__(self, ruta_absoluta_carpeta: Union[str, Path], nombre_script: str) -> None:
        """
        Inicializa un manejador de logs para un script en particular.
        
        Args:
            ruta_absoluta_carpeta: Directorio raíz donde reside el script.
            nombre_script: Nombre del archivo del script, usado para catalogar los logs.
        """
        self.carpeta_raiz = Path(ruta_absoluta_carpeta)
        # Extraemos el nombre del archivo sin extensión
        n_script = Path(nombre_script).stem
        self.subcarpeta = self.carpeta_raiz / "logs" / n_script
        
        # Crear los directorios padres y correspondientes
        self.subcarpeta.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(n_script)
        self.logger.setLevel(logging.INFO)

        # Evitamos registrar handlers repetidos si el logger ya fue inicializado
        if not self.logger.hasHandlers():
            fecha_hoy = date.today().strftime('%Y-%m-%d')
            ruta_archivo = self.subcarpeta / f"{fecha_hoy}.log"

            formato = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s', 
                datefmt='%H:%M:%S'
            )

            file_handler = logging.FileHandler(ruta_archivo, encoding='utf-8')
            file_handler.setFormatter(formato)
            self.logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formato)
            self.logger.addHandler(console_handler)

    def info(self, mensaje: Any) -> None:
        self.logger.info(mensaje)

    def warning(self, mensaje: Any) -> None:
        self.logger.warning(mensaje)

    def error(self, mensaje: Any) -> None:
        self.logger.error(mensaje)