#!/usr/bin/env python
# coding: utf-8

import gc
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from jobspy import scrape_jobs
from scrapping.subidaS3 import subir_a_s3
from utils.logger import MiLogger


def configurar_rutas(log: MiLogger) -> Tuple[Path, str]:
    """Configura las carpetas locales y genera las rutas de guardado."""
    ahora = datetime.now()
    fecha_hoy = ahora.strftime("%d-%m-%Y")
    timestamp_archivo = ahora.strftime("%H-%M")
    
    ruta_carpeta = Path(__file__).resolve().parent / "scraps" / fecha_hoy
    ruta_carpeta.mkdir(parents=True, exist_ok=True)

    nombre_archivo = f"ofertas_it_{timestamp_archivo}.csv"
    ruta_final = ruta_carpeta / nombre_archivo
    return ruta_final, nombre_archivo


def guardar_a_csv(df: pd.DataFrame, path: Path) -> bool:
    """Guarda un DataFrame de manera incremental en CSV."""
    if df.empty:
        return False
    df.to_csv(path, mode="a", index=False, header=not path.exists(), encoding="utf-8")
    return True


def realizar_busqueda(
    term: str, 
    loc: str, 
    sites: List[str], 
    is_remote: bool, 
    results_wanted: int,
    ruta_final: Path, 
    log: MiLogger
) -> None:
    """Ejecuta el scraping para un término/ubicación y persiste en disco inmediatamente."""
    etiqueta = "remotos" if is_remote else f"en {loc}"
    try:
        jobs = scrape_jobs(
            site_name=sites,
            search_term=term,
            location=loc,
            results_wanted=results_wanted,
            hours_old=24,
            is_remote=is_remote,
            linkedin_fetch_description=True
        )
        
        df_res = pd.DataFrame(jobs)
        if not df_res.empty:
            df_res["search_location"] = "Remote (Spain)" if is_remote else loc
            df_res["search_query"] = term
            
            if guardar_a_csv(df_res, ruta_final):
                log.info(f"Éxito: {len(df_res)} empleos guardados ({etiqueta}) para '{term}'.")
        else:
            log.warning(f"Sin resultados para '{term}' ({etiqueta}).")

    except Exception as e:
        log.error(f"Error procesando '{term}' ({etiqueta}): {e}")


def limpiar_duplicados(ruta_final: Path, log: MiLogger) -> None:
    """Elimina registros duplicados en el CSV generado."""
    if not ruta_final.exists():
        log.warning(f"No se generó ningún archivo en {ruta_final} para limpiar.")
        return
        
    log.info("Iniciando deduplicación en el archivo consolidado...")
    try:
        df_final = pd.read_csv(ruta_final)
        total_inicial = len(df_final)
        
        # Deduplicación por URL y por firma de oferta
        df_final.drop_duplicates(subset=["job_url"], inplace=True)
        df_final.drop_duplicates(subset=["title", "company", "location"], keep="first", inplace=True)
        
        df_final.to_csv(ruta_final, index=False, encoding="utf-8")
        log.info(f"Deduplicación lista: de {total_inicial} a {len(df_final)} ofertas únicas.")
    except Exception as e:
        log.error(f"Error limpiando duplicados: {e}")


def main() -> None:
    """Orquestador principal del scraping e ingesta a S3."""
    log = MiLogger(str(Path(__file__).resolve().parent.parent), Path(__file__).name)
    ruta_final, nombre_archivo = configurar_rutas(log)

    is_test = os.getenv("TEST_MODE", "0") == "1"

    if is_test:
        log.info("=== MODO TEST / CI DETECTADO ===")
        sites = ["indeed"]
        search_terms = ["Python Developer"]
        search_tasks = [(False, "Madrid")]
        results_wanted = 2
        delay_range = (1, 2)
    else:
        sites = ["linkedin", "indeed", "glassdoor"]
        search_terms = [
            "Data Engineer", "Data Analyst", "Python Developer", 
            "Backend Engineer", "Software Developer", "IA Engineer"
        ]
        # Lista de tuplas: (is_remote, location)
        search_tasks = [
            (False, "Málaga"),
            (False, "Granada"),
            (False, "Sevilla"),
            (False, "Madrid"),
            (False, "Barcelona"),
            (True, "Spain")
        ]
        results_wanted = 40
        delay_range = (7, 12)

    # Ejecución iterativa unificada
    for is_remote, loc in search_tasks:
        log.info(f"--- Procesando {'remoto' if is_remote else loc} ---")
        for term in search_terms:
            realizar_busqueda(term, loc, sites, is_remote, results_wanted, ruta_final, log)
            gc.collect()
            time.sleep(random.uniform(*delay_range))

    # Limpieza final de registros
    limpiar_duplicados(ruta_final, log)

    # Subida a almacenamiento en la nube
    if is_test:
        log.info("Smoke test completado exitosamente. Se omite la subida a S3.")
        return

    nombre_bucket = os.getenv("BUCKET_NAME")
    if not nombre_bucket:
        log.error("Variable de entorno BUCKET_NAME no configurada. Omitiendo subida a S3.")
        return

    if not ruta_final.exists():
        log.warning("No hay archivo generado para subir a S3.")
        return

    ahora = datetime.now()
    clave_s3 = f"raw/year={ahora.strftime('%Y')}/month={ahora.strftime('%m')}/{nombre_archivo}"
    
    if subir_a_s3(ruta_final, nombre_bucket, clave_s3, log):
        log.info(f"Pipeline completado. Archivo disponible en S3: {clave_s3}")
    else:
        log.error("Fallo durante la persistencia en S3.")


if __name__ == "__main__":
    main()