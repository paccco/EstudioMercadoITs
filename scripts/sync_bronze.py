import os
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
    full_table_path = f"bronze.{table_name}"

    # 2. Conexión y configuración de MotherDuck / S3
    con = duckdb.connect(f"md:{database}?motherduck_token={token}")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"""
        SET s3_region = '{aws_region}';
        SET s3_access_key_id = '{aws_key}';
        SET s3_secret_access_key = '{aws_secret}';
    """)

    # Garantizar esquema bronze
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

    # 3. Determinar la última fecha procesada de forma segura
    check_table = con.execute(f"""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'bronze' AND table_name = '{table_name}';
    """).fetchone()[0]

    if check_table == 0:
        last_date = date(2026, 1, 1)
    else:
        raw_last = con.execute(f"SELECT MAX(extraction_date) FROM {full_table_path};").fetchone()[0]
        if raw_last is None:
            last_date = date(2026, 1, 1)
        elif isinstance(raw_last, str):
            last_date = datetime.strptime(raw_last, "%Y-%m-%d").date()
        else:
            last_date = raw_last

    start_date = last_date + timedelta(days=1)
    end_date = date.today()

    print(f"Buscando particiones pendientes para {full_table_path} entre {start_date} y {end_date}...")

    # 4. Comprobar archivos existentes en S3 con HEAD Object
    s3_client = boto3.client(
        "s3",
        region_name=aws_region,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret
    )

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
    if not files_to_load:
        print("No se encontraron particiones pendientes de carga.")
        con.close()
        return

    print(f"Cargando {len(files_to_load)} lote(s) en {full_table_path}...")

    # Operación DDL/DML parametrizada pasando la lista en $1
    if check_table == 0:
        con.execute(f"""
            CREATE TABLE {full_table_path} AS
            SELECT 
                *,
                strptime(regexp_extract(filename, '(\\d{{8}})', 1), '%Y%m%d')::DATE AS extraction_date,
                filename AS source_file,
                CURRENT_TIMESTAMP AS ingested_at
            FROM read_csv($1, filename = true, auto_detect = true);
        """, [files_to_load])
    else:
        con.execute(f"""
            INSERT INTO {full_table_path}
            SELECT 
                *,
                strptime(regexp_extract(filename, '(\\d{{8}})', 1), '%Y%m%d')::DATE AS extraction_date,
                filename AS source_file,
                CURRENT_TIMESTAMP AS ingested_at
            FROM read_csv($1, filename = true, auto_detect = true);
        """, [files_to_load])

    # 6. Comprobación final
    total_filas = con.execute(f"SELECT COUNT(*) FROM {full_table_path};").fetchone()[0]
    print(f"Carga finalizada con éxito. Filas acumuladas en {full_table_path}: {total_filas}")
    con.close()

if __name__ == "__main__":
    run_sync()