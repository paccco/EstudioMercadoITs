#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import glob
import os
import gc
import shutil  # Para borrar las carpetas diarias
import argparse  # Para argumentos de línea de comandos
from datetime import datetime, timedelta
from bot.logger import MiLogger


# --- 0. PARSER DE ARGUMENTOS ---
parser = argparse.ArgumentParser(description='Script de consolidación mensual de datos de LinkedIn')
parser.add_argument('--auto', action='store_true', 
                    help='Ejecuta el script en modo automático (borra las carpetas diarias)')
args = parser.parse_args()

# --- 1. CONFIGURACIÓN DE LOGS ---

log = MiLogger("logs", os.path.basename(__file__))

# --- 2. DETERMINAR EL MES A PROCESAR ---
hoy = datetime.now()
if args.auto:
    # En modo automático procesamos el mes anterior
    mes_a_procesar = (hoy.replace(day=1) - timedelta(days=1)).strftime("%m-%Y")
else:
    # En modo manual (por defecto) procesamos el mes actual
    mes_a_procesar = hoy.strftime("%m-%Y")
    log.info("MODO MANUAL: Procesando el MES ACTUAL")

# --- 3. PROCESAMIENTO INCREMENTAL ---
# Buscamos las carpetas diarias: scraps/DD-MM-YYYY/
carpetas_diarias = glob.glob(os.path.join('scraps', f'*-{mes_a_procesar}'))
archivos = glob.glob(os.path.join('scraps', f'*-{mes_a_procesar}', '*.csv'))

# Estructura de destino
data_dir = 'data_mensual'
if not os.path.exists(data_dir): os.makedirs(data_dir)

carpeta_mes = os.path.join(data_dir, f"resultado_{mes_a_procesar}")
ruta_temporal = os.path.join(data_dir, f"temp_{mes_a_procesar}.csv")

# Determinar el sufijo del archivo: "_F" si es día 1 y es ejecución automática
sufijo = ""
if args.auto:
    sufijo = "_F"
    log.info("DÍA 1 DEL MES: Se añadirá sufijo '_F' al archivo final")

ruta_final = os.path.join(carpeta_mes, f"dataset_{mes_a_procesar}{sufijo}.csv")

log.info(f"Iniciando consolidación de {len(archivos)} archivos de {len(carpetas_diarias)} días...")

# Paso 1: Unir archivos en un temporal
for i, archivo in enumerate(archivos):
    try:
        temp_df = pd.read_csv(archivo, engine='c', low_memory=True)
        temp_df.to_csv(ruta_temporal, mode='a', index=False, header=not os.path.exists(ruta_temporal))
        del temp_df
        if i % 5 == 0: gc.collect()
    except Exception as e:
        log.error(f"Error procesando {archivo}: {e}")

# Paso 2: Limpieza y creación de la carpeta final
exito_guardado = False
if os.path.exists(ruta_temporal):
    log.info("Limpiando duplicados y generando archivo maestro...")
    
    df_maestro = pd.read_csv(ruta_temporal, engine='c')
    os.remove(ruta_temporal) 
    
    df_maestro.drop_duplicates(subset=['job_url'], keep='first', inplace=True)
    df_maestro.drop_duplicates(subset=['title', 'company', 'location'], keep='first', inplace=True)
    
    if not os.path.exists(carpeta_mes):
        os.makedirs(carpeta_mes)

    try:
        df_maestro.to_csv(ruta_final, index=False, encoding='utf-8')
        log.info(f"¡ÉXITO! Archivo guardado en: {ruta_final}")
        exito_guardado = True # Marcamos que el archivo está a salvo
    except Exception as e:
        log.critical(f"Error fatal al guardar: {e}")
    
    del df_maestro
    gc.collect()
else:
    log.warning(f"No había datos para {mes_a_procesar}.")

# --- 4. BORRADO DE CARPETAS DIARIAS (LIMPIEZA DE SCRAPS) ---
if exito_guardado:
    if not args.auto:
        log.info("MODO MANUAL: No se borrarán las carpetas diarias. Los informes se mantienen en scraps/")
    else:
        log.info(f"Iniciando borrado de carpetas diarias de {mes_a_procesar}...")
        for carpeta in carpetas_diarias:
            try:
                shutil.rmtree(carpeta) # Borra la carpeta y todo su contenido
                log.info(f"Eliminada: {carpeta}")
            except Exception as e:
                log.error(f"No se pudo borrar {carpeta}: {e}")
        log.info("Limpieza de scraps completada.")
else:
    log.warning("No se borraron las carpetas diarias porque el archivo maestro no se generó.")

# Finalización
del carpetas_diarias, archivos, mes_a_procesar, carpeta_mes, ruta_temporal, ruta_final
log.info("Proceso mensual finalizado.")