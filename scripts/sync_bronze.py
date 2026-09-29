import os
import re
import sys
from datetime import date, datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import duckdb

def list_s3_keys_under_prefix(s3_client, bucket, prefix):
    """Recupera todas las claves bajo un prefijo en S3 manejando paginación."""
    keys = []
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            keys.append(obj['Key'])
    return keys

def run_sync():
    # 1. Detección de entorno (dev por defecto para evitar sobreescrituras accidentales en prod)
    env = os.environ.get("ENV", "dev").strip().lower()
    
    # 1. Variables inyectadas directamente por GitHub Actions
    env = os.environ.get("ENV", "dev").strip().lower()
    bucket = os.environ.get("S3_BUCKET")
    token = os.environ.get("MOTHERDUCK_TOKEN")
    aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
    database = os.environ.get("MOTHERDUCK_DB")
    aws_region = os.environ.get("AWS_REGION")
    aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY_DEV")

    database = os.environ.get("MOTHERDUCK_DB")
    aws_region = os.environ.get("AWS_REGION")

    print(f"[*] Ejecutando en entorno: {env.upper()} | Bucket objetivo: {bucket}")

    if not all([token, aws_key, aws_secret, database]):
        print(f"[ERROR] Faltan secretos obligatorios para el entorno '{env}'.")
        sys.exit(1)

    table_name = "t_scrap_offers_b"
    full_table_path = f"bronze.{table_name}"

    # 2. Conexión y configuración de MotherDuck / S3
    con = duckdb.connect(f"md:{database}?motherduck_token={token}")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"""
        SET s3_region = '{aws_region}';
        SET s3_access_key_id = '{aws_key}';
        SET s3_secret_access_key = '{aws_secret}';
    """)
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

    # 3. Determinar la última fecha procesada
    check_table = con.execute(f"""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'bronze' AND table_name = '{table_name}';
    """).fetchone()[0]

    if check_table == 0:
        last_date = date(2026, 1, 1)
        already_loaded_files = set()
    else:
        raw_last = con.execute(f"SELECT MAX(extraction_date) FROM {full_table_path};").fetchone()[0]
        last_date = raw_last if isinstance(raw_last, date) else (
            datetime.strptime(raw_last, "%Y-%m-%d").date() if raw_last else date(2026, 1, 1)
        )
        # Control estricto de idempotencia por ruta completa para evitar duplicados
        loaded_res = con.execute(f"SELECT DISTINCT source_file FROM {full_table_path};").fetchall()
        already_loaded_files = {row[0] for row in loaded_res if row[0]}

    start_date = last_date + timedelta(days=1)
    end_date = date.today()

    print(f"Buscando particiones pendientes para {full_table_path} desde {start_date} hasta {end_date}...")

    # 4. Exploración dinámica en S3
    s3_client = boto3.client(
        "s3",
        region_name=aws_region,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret
    )

    # Identificar años a revisar
    target_years = range(start_date.year, end_date.year + 1)
    files_to_load = []

    for yr in target_years:
        prefix = f"raw/year={yr}/"
        s3_keys = list_s3_keys_under_prefix(s3_client, bucket, prefix)

        for key in s3_keys:
            full_s3_uri = f"s3://{bucket}/{key}"
            if full_s3_uri in already_loaded_files:
                continue

            # Caso 1: Archivo consolidado de mes cerrado (raw/year=YYYY/month_X.csv)
            match_month = re.search(r"raw/year=(\d{4})/month_(\d+)\.csv$", key)
            if match_month:
                f_year, f_month = int(match_month.group(1)), int(match_month.group(2))
                # Fecha representativa: primer día del mes siguiente menos 1 día
                if f_month == 12:
                    month_end_date = date(f_year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end_date = date(f_year, f_month + 1, 1) - timedelta(days=1)

                if month_end_date >= start_date:
                    files_to_load.append(full_s3_uri)
                    print(f"  [+] Mes cerrado localizado: {key}")
                continue

            # Caso 2: Archivo diario dentro de carpeta de mes abierto (raw/year=YYYY/month=MM/ofertas_it_YYYY-MM-DD_at_*.csv)
            match_daily = re.search(r"ofertas_it_(\d{4}-\d{2}-\d{2})_at_.*\.csv$", key)
            if match_daily:
                f_date = datetime.strptime(match_daily.group(1), "%Y-%m-%d").date()
                if start_date <= f_date <= end_date:
                    files_to_load.append(full_s3_uri)
                    print(f"  [+] Archivo diario localizado: {key}")

    # 5. Ingesta directa en MotherDuck
    if not files_to_load:
        print("No se encontraron particiones pendientes de carga.")
        con.close()
        return

    print(f"Cargando {len(files_to_load)} archivo(s) en {full_table_path}...")

    # Expresión condicional SQL para derivar extraction_date según el tipo de archivo
    date_parsing_sql = """
        CASE 
            WHEN regexp_matches(filename, 'ofertas_it_\\d{4}-\\d{2}-\\d{2}_at_') 
                THEN strptime(regexp_extract(filename, '(\\d{4}-\\d{2}-\\d{2})', 1), '%Y-%m-%d')::DATE
            WHEN regexp_matches(filename, 'month_\\d+\\.csv') 
                THEN strptime(
                    regexp_extract(filename, 'year=(\\d{4})', 1) || '-' || 
                    lpad(regexp_extract(filename, 'month_(\\d+)\\.csv', 1), 2, '0') || '-01',
                    '%Y-%m-%d'
                )::DATE
            ELSE CURRENT_DATE
        END AS extraction_date,
        filename AS source_file,
        CURRENT_TIMESTAMP AS ingested_at
    """

    if check_table == 0:
        con.execute(f"""
            CREATE TABLE {full_table_path} AS
            SELECT 
                *,
                {date_parsing_sql}
            FROM read_csv($1, filename = true, auto_detect = true, union_by_name = true);
        """, [files_to_load])
    else:
        con.execute(f"""
            INSERT INTO {full_table_path}
            SELECT 
                *,
                {date_parsing_sql}
            FROM read_csv($1, filename = true, auto_detect = true, union_by_name = true);
        """, [files_to_load])

    # 6. Verificación final
    total_filas = con.execute(f"SELECT COUNT(*) FROM {full_table_path};").fetchone()[0]
    print(f"Carga finalizada con éxito. Filas acumuladas en {full_table_path}: {total_filas}")
    con.close()

if __name__ == "__main__":
    run_sync()