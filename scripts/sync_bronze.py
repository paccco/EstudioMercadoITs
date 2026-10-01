import os
import sys
import duckdb

def debug_columns():
    # 1. Recuperar variables de entorno
    env = os.environ.get("ENV", "prod").strip().lower()
    motherduck_db = os.environ.get("MOTHERDUCK_DB", f"db_{env}")
    token = os.environ.get("MOTHERDUCK_TOKEN")
    bucket = os.environ.get("S3_BUCKET")
    aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = os.environ.get("AWS_REGION", "eu-north-1")

    if not token:
        print("[ERROR] Falta MOTHERDUCK_TOKEN.")
        sys.exit(1)

    table_name = "t_scrap_offers_b"
    full_table_path = f"{motherduck_db}.bronze.{table_name}"

    print(f"[*] Conectando a MotherDuck: {motherduck_db}")
    con = duckdb.connect(f"md:{motherduck_db}?motherduck_token={token}")

    # Configurar acceso a S3 si hay credenciales disponibles
    if aws_key and aws_secret:
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute(f"""
            CREATE OR REPLACE SECRET s3_creds (
                TYPE S3,
                KEY_ID '{aws_key}',
                SECRET '{aws_secret}',
                REGION '{aws_region}'
            );
        """)

    # 2. Obtener columnas de la tabla existente en MotherDuck
    try:
        table_desc = con.execute(f"DESCRIBE {full_table_path};").fetchall()
        table_cols = {row[0]: row[1] for row in table_desc}
        print(f"[✓] Columnas detectadas en la tabla ({len(table_cols)}): {full_table_path}")
    except Exception as e:
        print(f"[ERROR] No se pudo leer la tabla destino: {e}")
        con.close()
        sys.exit(1)

    # 3. Determinar origen del archivo de prueba (S3 o local)
    # Puedes pasar la ruta como argumento: python scripts/debug_schema_diff.py s3://bucket/path/file.csv
    # O por defecto comprobará el último patrón en S3
    if len(sys.argv) > 1:
        target_csv = sys.argv[1]
    else:
        target_csv = f"s3://{bucket}/raw/year=2026/**/*.csv"

    print(f"[*] Analizando esquema proyectado del CSV: {target_csv}")

    # Misma proyección de metadatos que usa sync_bronze.py
    query_csv_schema = f"""
        DESCRIBE 
        SELECT 
            *,
            CURRENT_DATE AS extraction_date,
            filename AS source_file,
            CURRENT_TIMESTAMP AS ingested_at
        FROM read_csv('{target_csv}', filename = true, auto_detect = true, union_by_name = true)
        LIMIT 1;
    """

    try:
        csv_desc = con.execute(query_csv_schema).fetchall()
        csv_cols = {row[0]: row[1] for row in csv_desc}
        print(f"[✓] Columnas proyectadas por el CSV + metadatos ({len(csv_cols)})")
    except Exception as e:
        print(f"[ERROR] No se pudo leer el CSV: {e}")
        con.close()
        sys.exit(1)

    # 4. Comparativa de conjuntos
    set_table = set(table_cols.keys())
    set_csv = set(csv_cols.keys())

    extra_in_csv = set_csv - set_table
    missing_in_csv = set_table - set_csv

    print("\n" + "=" * 60)
    print("RESULTADO DE LA COMPARACIÓN DE ESQUEMA")
    print("=" * 60)
    print(f"Total columnas en BD  : {len(table_cols)}")
    print(f"Total columnas en CSV : {len(csv_cols)}")
    print("-" * 60)

    if not extra_in_csv and not missing_in_csv:
        print("[✓] Ambos esquemas coinciden exactamente en nombres de columnas.")
    else:
        if extra_in_csv:
            print(f"[!] COLUMNAS SOBRANTES EN EL CSV (No existen en la tabla de BD):")
            for col in sorted(extra_in_csv):
                print(f"    -> '{col}' (Tipo detectado: {csv_cols[col]})")

        if missing_in_csv:
            print(f"\n[!] COLUMNAS FALTANTES EN EL CSV (Existen en la BD pero no en el CSV):")
            for col in sorted(missing_in_csv):
                print(f"    -> '{col}' (Tipo esperado: {table_cols[col]})")

    print("=" * 60)
    con.close()

if __name__ == "__main__":
    debug_columns()