#!/usr/bin/env python
# coding: utf-8

import os
import time
import random
import gc
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
from jobspy import scrape_jobs
from utils.logger import MiLogger


def configurar_rutas(log: MiLogger) -> Path:
    """Configura las carpetas y rutas de guardado."""
    fecha_hoy = datetime.now().strftime("%d-%m-%Y")
    timestamp_archivo = datetime.now().strftime("%H-%M")
    
    ruta_carpeta = Path(__file__).parent / "scraps" / fecha_hoy
    ruta_carpeta.mkdir(parents=True, exist_ok=True)
    
    ruta_final = ruta_carpeta / f"ofertas_it_{timestamp_archivo}.csv"
    return ruta_final


def guardar_a_csv(df: pd.DataFrame, path: Path) -> bool:
    """Guarda un dataframe en formato CSV de manera incremental (append)."""
    if not df.empty:
        df.to_csv(path, mode='a', index=False, header=not path.exists(), encoding='utf-8')
        return True
    return False


def realizar_busqueda(
    term: str, 
    loc: str, 
    sites: List[str], 
    is_remote: bool, 
    ruta_final: Path, 
    log: MiLogger
) -> None:
    """Realiza la búsqueda de empleos y la guarda en disco liberando memoria inmediatamente."""
    try:
        jobs = scrape_jobs(
            site_name=sites,
            search_term=term,
            location=loc,
            results_wanted=40,
            hours_old=24,
            is_remote=is_remote,
            linkedin_fetch_description=True 
        )
        
        df_res = pd.DataFrame(jobs)
        if not df_res.empty:
            df_res['search_location'] = 'Remote (Spain)' if is_remote else loc
            df_res['search_query'] = term
            
            if guardar_a_csv(df_res, ruta_final):
                tipo = "remotos" if is_remote else f"en {loc}"
                log.info(f"Éxito y Guardado: {len(df_res)} empleos {tipo} para {term}.")
        else:
            log.warning(f"No se encontraron resultados para {term} en {loc}.")

    except Exception as e:
        log.error(f"Error en búsqueda de {term} en {loc}: {e}")


def limpiar_duplicados(ruta_final: Path, log: MiLogger) -> None:
    """Lee el CSV final, limpia duplicados y reescribe."""
    if not ruta_final.exists():
        return
        
    log.info("Iniciando limpieza de duplicados en el archivo final...")
    df_final = pd.read_csv(ruta_final)
    antes = len(df_final)
    
    df_final.drop_duplicates(subset=['job_url'], inplace=True)
    df_final.drop_duplicates(subset=['title', 'company', 'location'], keep='first', inplace=True)
    
    df_final.to_csv(ruta_final, index=False, encoding='utf-8')
    log.info(f"Limpieza completa: de {antes} a {len(df_final)} registros únicos.")


def main() -> None:
    """Función principal que ejecuta el scraping de ofertas de empleo."""
    # Configuración de logs
    log = MiLogger(str(Path(__file__).parent.parent), Path(__file__).name)
    ruta_final = configurar_rutas(log)

    # Configuración de búsqueda
    sites = ["linkedin", "indeed", "glassdoor"]
    search_terms = ["Data Engineer", "Data Analyst", "Python Developer", "Backend Engineer", "Software Developer", "IA Engineer"]
    locations = ["Málaga", "Granada", "Sevilla", "Madrid", "Barcelona"]
    random_pet = (7, 12)

    # 1. Búsqueda Presencial
    for loc in locations:
        for term in search_terms:
            realizar_busqueda(term, loc, sites, False, ruta_final, log)
            gc.collect()
            time.sleep(random.uniform(*random_pet))

    # 2. Búsqueda Remota
    log.info("------ Iniciando empleos remotos ------")
    for term in search_terms:
        realizar_busqueda(term, "Spain", sites, True, ruta_final, log)
        gc.collect()
        time.sleep(random.uniform(*random_pet))

    # Limpieza final
    limpiar_duplicados(ruta_final, log)
    log.info(f"Proceso finalizado. Archivo disponible en: {ruta_final}")


if __name__ == "__main__":
    main()
