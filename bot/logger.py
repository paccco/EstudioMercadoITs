import logging
import os
import datetime

class MiLogger:
    def __init__(self, carpeta_logs, nombre_script):
        # 1. Definir la ruta:
        self.carpeta_raiz = carpeta_logs
        self.subcarpeta = os.path.join(self.carpeta_raiz, nombre_script)
        
        # 2. Crear las carpetas si no existen (makedirs crea toda la ruta)
        if not os.path.exists(self.subcarpeta):
            os.makedirs(self.subcarpeta)

        # 3. Crear un logger único para este script
        self.logger = logging.getLogger(nombre_script)
        self.logger.setLevel(logging.INFO)

        # 4. Evitar duplicar handlers (importante en POO)
        if not self.logger.handlers:
            fecha_hoy = datetime.date.today().strftime('%Y-%m-%d')
            # El archivo se guardará en: logs/script1/2026-03-15.log
            ruta_archivo = os.path.join(self.subcarpeta, f"{fecha_hoy}.log")

            # Formato profesional
            formato = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s', 
                datefmt='%H:%M:%S'
            )

            # Handler para el archivo
            file_handler = logging.FileHandler(ruta_archivo, encoding='utf-8')
            file_handler.setFormatter(formato)
            self.logger.addHandler(file_handler)

            # Handler opcional para ver en la terminal de la Raspberry
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formato)
            self.logger.addHandler(console_handler)

    def info(self, mensaje):
        self.logger.info(mensaje)

    def warning(self, mensaje):
        self.logger.warning(mensaje)

    def error(self, mensaje):
        self.logger.error(mensaje)