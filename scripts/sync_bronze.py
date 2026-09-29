import os
<<<<<<< HEAD
import sys
from datetime import date, datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import duckdb

def run_sync():
    # 1. Variables de entorno inyectadas por el entorno de ejecución
    token = os.environ.get("MOTHERDUCK_TOKEN")
    database = os.environ.get("MOTHERDUCK_DB", "mi_db_prod")
    bucket = os.environ.get("S3_BUCKET", "mi-bucket-raw")
    aws_region = os.environ.get("AWS_REGION", "eu-west-1")
    aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")

    if not all([token, aws_key, aws_secret]):
        print("[ERROR] Faltan variables de entorno obligatorias.")
        sys.exit(1)

    table_name = "t_scrap_offers_b"
=======
import re
import sys
from datetime import date, datetime, timedelta
import boto3
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
    # 1. Configuración de variables de entorno
    table_name = "t_scraps_offers_b"
>>>>>>> dev
    full_table_path = f"bronze.{table_name}"

    # 2. Conexión y configuración de MotherDuck / S3
    con = duckdb.connect(f"md:{database}?motherduck_token={token}")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"""
        SET s3_region = '{aws_region}';
        SET s3_access_key_id = '{aws_key}';
        SET s3_secret_access_key = '{aws_secret}';
    """)
<<<<<<< HEAD

    # Garantizar esquema bronze
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

    # 3. Determinar la última fecha procesada de forma segura
=======
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

    # 3. Determinar la última fecha procesada
>>>>>>> dev
    check_table = con.execute(f"""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'bronze' AND table_name = '{table_name}';
    """).fetchone()[0]

    if check_table == 0:
        last_date = date(2026, 1, 1)
<<<<<<< HEAD
    else:
        raw_last = con.execute(f"SELECT MAX(extraction_date) FROM {full_table_path};").fetchone()[0]
        if raw_last is None:
            last_date = date(2026, 1, 1)
        elif isinstance(raw_last, str):
            last_date = datetime.strptime(raw_last, "%Y-%m-%d").date()
        else:
            last_date = raw_last
=======
        already_loaded_files = set()
    else:
        raw_last = con.execute(f"SELECT MAX(extraction_date) FROM {full_table_path};").fetchone()[0]
        last_date = raw_last if isinstance(raw_last, date) else (
            datetime.strptime(raw_last, "%Y-%m-%d").date() if raw_last else date(2026, 1, 1)
        )
        # Control estricto de idempotencia por ruta completa para evitar duplicados
        loaded_res = con.execute(f"SELECT DISTINCT source_file FROM {full_table_path};").fetchall()
        already_loaded_files = {row[0] for row in loaded_res if row[0]}
>>>>>>> dev

    start_date = last_date + timedelta(days=1)
    end_date = date.today()

<<<<<<< HEAD
    print(f"Buscando particiones pendientes para {full_table_path} entre {start_date} y {end_date}...")

    # 4. Comprobar archivos existentes en S3 con HEAD Object
=======
    print(f"Buscando particiones pendientes para {full_table_path} desde {start_date} hasta {end_date}...")

    # 4. Exploración dinámica en S3
>>>>>>> dev
    s3_client = boto3.client(
        "s3",
        region_name=aws_region,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret
    )

<<<<<<< HEAD
    files_to_load = []
    curr = start_date
    while curr <= end_date:
        filename = f"datos_{curr.strftime('%Y%m%d')}.csv"
        key = f"raw/{filename}"
        
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            files_to_load.append(f"s3://{bucket}/{key}")
            print(f"  [+] Archivo localizado: {key}")
        except ClientError:
            pass  # Día sin scraping o archivo no generado
            
        curr += timedelta(days=1)

    # 5. Ingesta por lote directo en MotherDuck
=======
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
>>>>>>> dev
    if not files_to_load:
        print("No se encontraron particiones pendientes de carga.")
        con.close()
        return

<<<<<<< HEAD
    print(f"Cargando {len(files_to_load)} lote(s) en {full_table_path}...")

    # Operación DDL/DML parametrizada pasando la lista en $1
=======
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

>>>>>>> dev
    if check_table == 0:
        con.execute(f"""
            CREATE TABLE {full_table_path} AS
            SELECT 
                *,
<<<<<<< HEAD
                strptime(regexp_extract(filename, '(\\d{{8}})', 1), '%Y%m%d')::DATE AS extraction_date,
                filename AS source_file,
                CURRENT_TIMESTAMP AS ingested_at
            FROM read_csv($1, filename = true, auto_detect = true);
=======
                {date_parsing_sql}
            FROM read_csv($1, filename = true, auto_detect = true, union_by_name = true);
>>>>>>> dev
        """, [files_to_load])
    else:
        con.execute(f"""
            INSERT INTO {full_table_path}
            SELECT 
                *,
<<<<<<< HEAD
                strptime(regexp_extract(filename, '(\\d{{8}})', 1), '%Y%m%d')::DATE AS extraction_date,
                filename AS source_file,
                CURRENT_TIMESTAMP AS ingested_at
            FROM read_csv($1, filename = true, auto_detect = true);
        """, [files_to_load])

    # 6. Comprobación final
=======
                {date_parsing_sql}
            FROM read_csv($1, filename = true, auto_detect = true, union_by_name = true);
        """, [files_to_load])

    # 6. Verificación final
>>>>>>> dev
    total_filas = con.execute(f"SELECT COUNT(*) FROM {full_table_path};").fetchone()[0]
    print(f"Carga finalizada con éxito. Filas acumuladas en {full_table_path}: {total_filas}")
    con.close()

if __name__ == "__main__":
    run_sync()