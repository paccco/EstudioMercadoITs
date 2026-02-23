#!/usr/bin/env python3
"""
Script para hacer append de archivos CSV al dataset_maestro.csv

Uso:
    python AppendToMaestro.py archivo1.csv archivo2.csv ...
    python AppendToMaestro.py --folder /ruta/a/carpeta/
"""

import pandas as pd
import argparse
import os
import sys
from pathlib import Path


def append_to_maestro(input_files, maestro_path='data/dataset_maestro.csv', output_path=None, remove_duplicates=True):
    """
   Hace append de uno o varios archivos CSV al dataset_maestro.
    
    Args:
        input_files: Lista de rutas a archivos CSV para añadir
        maestro_path: Ruta al archivo dataset_maestro.csv
        output_path: Ruta de salida (si es None, sobrescribe el maestro)
        remove_duplicates: Si True, elimina duplicados basados en 'id' y 'job_url'
    """
    
    # Cargar el dataset maestro
    print(f"Cargando dataset maestro: {maestro_path}")
    try:
        df_maestro = pd.read_csv(maestro_path)
        print(f"  - Filas actuales: {len(df_maestro)}")
    except FileNotFoundError:
        print(f"  - No encontrado, creando nuevo dataset maestro...")
        df_maestro = pd.DataFrame()
    
    # Procesar cada archivo de entrada
    total_new_rows = 0
    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"  ⚠️ Archivo no encontrado: {input_file}")
            continue
            
        print(f"Procesando: {input_file}")
        try:
            df_new = pd.read_csv(input_file)
            rows = len(df_new)
            print(f"  - Filas a añadir: {rows}")
            
            # Eliminar duplicados dentro del archivo nuevo
            if remove_duplicates:
                if 'id' in df_new.columns and 'job_url' in df_new.columns:
                    before_dedup = len(df_new)
                    df_new = df_new.drop_duplicates(subset=['id', 'job_url'], keep='first')
                    after_dedup = len(df_new)
                    if before_dedup != after_dedup:
                        print(f"  - Duplicados eliminados en archivo nuevo: {before_dedup - after_dedup}")
                elif 'id' in df_new.columns:
                    before_dedup = len(df_new)
                    df_new = df_new.drop_duplicates(subset=['id'], keep='first')
                    after_dedup = len(df_new)
                    if before_dedup != after_dedup:
                        print(f"  - Duplicados eliminados en archivo nuevo: {before_dedup - after_dedup}")
            
            rows_to_add = len(df_new)
            total_new_rows += rows_to_add
            
            # Concatenar con el maestro
            df_maestro = pd.concat([df_maestro, df_new], ignore_index=True)
        except Exception as e:
            print(f"  ⚠️ Error al leer {input_file}: {e}")
    
    # Eliminar duplicados del dataset final
    if remove_duplicates and len(df_maestro) > 0:
        print("\nEliminando duplicados finales...")
        if 'id' in df_maestro.columns and 'job_url' in df_maestro.columns:
            before_total = len(df_maestro)
            df_maestro = df_maestro.drop_duplicates(subset=['id', 'job_url'], keep='first')
            after_total = len(df_maestro)
            duplicates_removed = before_total - after_total
            if duplicates_removed > 0:
                print(f"  - Duplicados eliminados (id + job_url): {duplicates_removed}")
        elif 'id' in df_maestro.columns:
            before_total = len(df_maestro)
            df_maestro = df_maestro.drop_duplicates(subset=['id'], keep='first')
            after_total = len(df_maestro)
            duplicates_removed = before_total - after_total
            if duplicates_removed > 0:
                print(f"  - Duplicados eliminados (id): {duplicates_removed}")
    
    # Guardar el resultado
    if output_path is None:
        output_path = maestro_path
    
    print(f"\nGuardando resultado: {output_path}")
    df_maestro.to_csv(output_path, index=False)
    print(f"  - Total filas: {len(df_maestro)}")
    print(f"  - Nuevas filas añadidas: {total_new_rows}")
    
    return df_maestro


def main():
    parser = argparse.ArgumentParser(
        description='Hace append de archivos CSV al dataset_maestro.csv',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos de uso:
  python AppendToMaestro.py nuevos_datos.csv
  python AppendToMaestro.py datos1.csv datos2.csv datos3.csv
  python AppendToMaestro.py --folder ./data/nuevos/
  python AppendToMaestro.py nuevos_datos.csv --output dataset_maestro_actualizado.csv
        '''
    )
    
    parser.add_argument(
        'files', 
        nargs='*', 
        help='Archivos CSV para añadir al maestro'
    )
    
    parser.add_argument(
        '--folder', '-f',
        type=str,
        help='Carpeta contendo archivos CSV (añade todos los .csv de la carpeta)'
    )
    
    parser.add_argument(
        '--maestro', '-m',
        type=str,
        default='data/dataset_maestro.csv',
        help='Ruta al archivo dataset_maestro (default: data/dataset_maestro.csv)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Ruta de salida (default: sobrescribe el maestro)'
    )
    
    args = parser.parse_args()
    
    # Recopilar archivos de entrada
    input_files = []
    
    if args.folder:
        # Añadir todos los CSV de la carpeta
        folder_path = Path(args.folder)
        if folder_path.is_dir():
            csv_files = list(folder_path.glob('*.csv'))
            input_files = [str(f) for f in csv_files]
            print(f"Encontrados {len(input_files)} archivos CSV en {args.folder}")
        else:
            print(f"Error: La carpeta no existe: {args.folder}")
            sys.exit(1)
    elif args.files:
        input_files = args.files
    else:
        parser.print_help()
        sys.exit(1)
    
    if not input_files:
        print("Error: No se encontraron archivos para procesar")
        sys.exit(1)
    
    # Ejecutar el append
    append_to_maestro(
        input_files=input_files,
        maestro_path=args.maestro,
        output_path=args.output
    )
    
    print("\n✓ Proceso completado!")


if __name__ == '__main__':
    main()
