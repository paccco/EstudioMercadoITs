#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from jobspy import scrape_jobs # <--- Scrappeo de ofertas de empleo
import time
import random
import os # <--- Para manejo de archivos y rutas
import logging # <--- Para manejo de logs
import gc  # <--- Para liberar RAM
from datetime import datetime

# --- CONFIGURACIÓN DE RUTAS Y LOGS ---
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"scraping_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# --- CONFIGURACIÓN DE GUARDADO INICIAL ---
fecha_hoy = datetime.now().strftime("%d-%m-%Y")
timestamp_archivo = datetime.now().strftime("%H-%M")
ruta_carpeta = os.path.join('scraps', fecha_hoy)
if not os.path.exists(ruta_carpeta):
    os.makedirs(ruta_carpeta)

ruta_final = os.path.join(ruta_carpeta, f"ofertas_it_{timestamp_archivo}.csv")

# --- CONFIGURACIÓN DE BÚSQUEDA ---
sites = ["linkedin", "indeed", "glassdoor"]
locations = ["Málaga", "Granada", "Sevilla", "Madrid", "Barcelona"]
search_terms = ["Data Engineer", "Data Analyst", "Python Developer", "Backend Engineer" ,"Software Developer", "IA Engineer"]
random_pet = [7, 12] # Rango de espera aleatoria entre búsquedas (en segundos) para evitar bloqueos

def save_to_csv(df, path):
    # Guardamos el dataframe en modo append y libera memoria
    if not df.empty:
        # Escribir cabecera solo si el archivo no existe
        file_exists = os.path.isfile(path)
        df.to_csv(path, mode='a', index=False, header=not file_exists, encoding='utf-8')
        return True
    return False

# 1. Búsqueda Presencial
for loc in locations:
    for term in search_terms:
        try:
            jobs = scrape_jobs(
                site_name=sites,
                search_term=term,
                location=loc,
                results_wanted=40,
                hours_old=24,
                is_remote=False,             
                linkedin_fetch_description=True 
            )
            
            df_res = pd.DataFrame(jobs)
            if not df_res.empty:
                df_res['search_location'] = loc
                df_res['search_query'] = term
                
                if save_to_csv(df_res, ruta_final):
                    logging.info(f"Éxito y Guardado: {len(df_res)} empleos en {loc} para {term}.")
                
                # Liberación agresiva de RAM
                del df_res
            else:
                logging.warning(f"No se encontraron resultados para {term} en {loc}.")

            del jobs
            gc.collect()  # <--- Forzamos limpieza de basura en RAM

        except Exception as e:
            logging.error(f"Error buscando {term} en {loc}: {str(e)}")

        time.sleep(random.uniform(random_pet[0], random_pet[1]))

# 2. Búsqueda Remota
logging.info("------  Iniciando empleos remotos ------")

for term in search_terms:
    try:
        jobs_remote = scrape_jobs(
            site_name=sites,
            search_term=term,
            location="Spain",           
            results_wanted=40,
            hours_old=24,           
            is_remote=True,              
            linkedin_fetch_description=True 
        )
        
        df_temp = pd.DataFrame(jobs_remote)
        if not df_temp.empty:
            df_temp['search_location'] = 'Remote (Spain)'
            df_temp['search_query'] = term
            
            save_to_csv(df_temp, ruta_final)
            logging.info(f"Éxito y Guardado: {len(df_temp)} empleos remotos para {term}.")
            
            del df_temp
        
        del jobs_remote
        gc.collect()

    except Exception as e:
        logging.error(f"Error en búsqueda remota de {term}: {str(e)}")

    time.sleep(random.uniform(random_pet[0], random_pet[1]))

# --- LIMPIEZA FINAL DE DUPLICADOS (Sobre el archivo ya guardado) ---
if os.path.exists(ruta_final):
    logging.info("Iniciando limpieza de duplicados en el archivo final...")
    df_final = pd.read_csv(ruta_final)
    antes = len(df_final)
    
    df_final.drop_duplicates(subset=['job_url'], inplace=True)
    df_final.drop_duplicates(subset=['title', 'company', 'location'], keep='first', inplace=True)
    
    df_final.to_csv(ruta_final, index=False, encoding='utf-8')
    logging.info(f"Limpieza completa: de {antes} a {len(df_final)} registros únicos.")
    
    del df_final
    gc.collect()

logging.info(f"Proceso finalizado. Archivo disponible en: {ruta_final}")