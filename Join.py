#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import glob
import os
import logging
import gc
import shutil  # Para borrar las carpetas diarias
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE LOGS ---
log_dir = 'logs'
if not os.path.exists(log_dir): os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"consolidacion_mensual_{datetime.now().strftime('%Y-%m')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()]
)

# --- 2. DETERMINAR EL MES ANTERIOR ---
hoy = datetime.now()
mes_a_procesar = (hoy.replace(day=1) - timedelta(days=1)).strftime("%m-%Y")

# --- 3. PROCESAMIENTO INCREMENTAL ---
# Buscamos las carpetas diarias: scraps/DD-MM-YYYY/
carpetas_diarias = glob.glob(os.path.join('scraps', f'*-{mes_a_procesar}'))
archivos = glob.glob(os.path.join('scraps', f'*-{mes_a_procesar}', '*.csv'))

# Estructura de destino
data_dir = 'data_mensual'
if not os.path.exists(data_dir): os.makedirs(data_dir)

carpeta_mes = os.path.join(data_dir, f"resultado_{mes_a_procesar}")
ruta_temporal = os.path.join(data_dir, f"temp_{mes_a_procesar}.csv")
ruta_final = os.path.join(carpeta_mes, f"dataset_{mes_a_procesar}.csv")

logging.info(f"Iniciando consolidación de {len(archivos)} archivos de {len(carpetas_diarias)} días...")

# Paso A: Unir archivos en un temporal
for i, archivo in enumerate(archivos):
    try:
        temp_df = pd.read_csv(archivo, engine='c', low_memory=True)
        temp_df.to_csv(ruta_temporal, mode='a', index=False, header=not os.path.exists(ruta_temporal))
        del temp_df
        if i % 5 == 0: gc.collect()
    except Exception as e:
        logging.error(f"Error procesando {archivo}: {e}")

# Paso B: Limpieza y creación de la carpeta final
exito_guardado = False
if os.path.exists(ruta_temporal):
    logging.info("Limpiando duplicados y generando archivo maestro...")
    
    df_maestro = pd.read_csv(ruta_temporal, engine='c')
    os.remove(ruta_temporal) 
    
    df_maestro.drop_duplicates(subset=['job_url'], keep='first', inplace=True)
    df_maestro.drop_duplicates(subset=['title', 'company', 'location'], keep='first', inplace=True)
    
    if not os.path.exists(carpeta_mes):
        os.makedirs(carpeta_mes)

    try:
        df_maestro.to_csv(ruta_final, index=False, encoding='utf-8')
        logging.info(f"¡ÉXITO! Archivo guardado en: {ruta_final}")
        exito_guardado = True # Marcamos que el archivo está a salvo
    except Exception as e:
        logging.critical(f"Error fatal al guardar: {e}")
    
    del df_maestro
    gc.collect()
else:
    logging.warning(f"No había datos para {mes_a_procesar}.")

# --- 4. BORRADO DE CARPETAS DIARIAS (LIMPIEZA DE SCRAPS) ---
if exito_guardado:
    logging.info(f"Iniciando borrado de carpetas diarias de {mes_a_procesar}...")
    for carpeta in carpetas_diarias:
        try:
            shutil.rmtree(carpeta) # Borra la carpeta y todo su contenido
            logging.info(f"Eliminada: {carpeta}")
        except Exception as e:
            logging.error(f"No se pudo borrar {carpeta}: {e}")
    logging.info("Limpieza de scraps completada.")
else:
    logging.warning("No se borraron las carpetas diarias porque el archivo maestro no se generó.")

# Finalización
del carpetas_diarias, archivos, mes_a_procesar, carpeta_mes, ruta_temporal, ruta_final
logging.info("Proceso mensual finalizado.")