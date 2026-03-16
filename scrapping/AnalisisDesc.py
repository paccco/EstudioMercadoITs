#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import spacy
import requests
import os
import numpy as np
from spacy.lang.es.stop_words import STOP_WORDS as STOP_ES
from spacy.lang.en.stop_words import STOP_WORDS as STOP_EN

STOP_WORDS = STOP_ES.union(STOP_EN)

# --- Cargar el Diccionario Tech ---   
def get_tech_dictionary(limit = 200):
    tags = []
    # La API entrega 100 por página
    for page in range(1, (limit // 100) + 1):
        url = f"https://api.stackexchange.com/2.3/tags?page={page}&pagesize=100&order=desc&sort=popular&site=stackoverflow"
        try:
            response = requests.get(url)
            data = response.json()
            for item in data['items']:
                tags.append(item['name'])
        except Exception as e:
            print(f"Error en página {page}: {e}")
            break
    return tags

def main():
    # --- Configurar spaCy ---
    print("Cargando modelo y configurando NER...")
    nlp = spacy.load("es_core_news_lg")

    # 1. Definir excepciones (tecnologías que son stop words pero queremos conservar)
    # Minúsculas para la comparación
    excepciones_tech = {"go", "r"}

    palabras_populares = {
        "performance", "testing", "security", "string", "array", "list", 
        "function", "object", "api", "rest", "json", "documentation",
        "deployment", "automation", "clean", "move", "code", "work",
        "linux", "windows", "ios", "android", "version-control", 'facebook',
        'join','variables', 'validation'
    }

    # 2. Cargar diccionario de GitHub
    tech_dictionary = get_tech_dictionary()

    diccionario_final = set(tech_dictionary).union(excepciones_tech).difference(palabras_populares)

    ruler = nlp.add_pipe("entity_ruler")
    LABEL_NAME = "TECH"

    # 3. Construir patrones filtrando Stop Words (evita que entre "al", "del", etc.)
    patterns = []
    for t in diccionario_final:
        t_lower = t.lower()
        
        # Si la palabra es una Stop Word y NO está en nuestras excepciones, la ignoramos
        if t_lower in STOP_WORDS and t_lower not in excepciones_tech:
            continue
        
        # Si es una excepción muy corta (como 'C', 'R', 'AL'), usamos TEXT para evitar minúsculas basura
        if len(t) <= 2:
            patterns.append({"label": LABEL_NAME, "pattern": [{"TEXT": t}]})
        else:
            # Para el resto, detección normal insensible a mayúsculas
            patterns.append({"label": LABEL_NAME, "pattern": [{"LOWER": t_lower}]})

    ruler.add_patterns(patterns)
    print(f"Diccionario configurado con {len(patterns)} patrones activos.")

    # --- PASO 3: Limpieza extrema de RAM ---
    if "ner" in nlp.pipe_names: nlp.remove_pipe("ner")
    if "parser" in nlp.pipe_names: nlp.remove_pipe("parser")
    if "lemmatizer" in nlp.pipe_names: nlp.remove_pipe("lemmatizer")
    if "attribute_ruler" in nlp.pipe_names: nlp.remove_pipe("attribute_ruler")

    # Vaciamos los vectores (ahorro de ~500MB por cada proceso de n_process)
    nlp.vocab.vectors.clear()

    # --- PASO 3: Cargar tu DataFrame Local ---
    file_path = os.path.join(os.path.dirname(__file__), 'data', 'dataset_master.csv')

    df = pd.DataFrame()  # Inicializamos un DataFrame vacío por si el archivo no se encuentra
    if not os.path.exists(file_path):
        print(f"❌ No se encuentra el archivo {file_path}. Asegúrate de que esté en la misma carpeta.")
    else:
        df = pd.read_csv(file_path)

    def process_safely(df_column, chunk_size=128):
        results = []
        # Aseguramos que los datos sean strings y manejamos nulos
        data = df_column.astype(str).tolist()
        total = len(data)

        print(f"🚀 Iniciando procesamiento de {total} registros...")

        for i, doc in enumerate(nlp.pipe(data, batch_size=chunk_size, n_process=4)):
            
            # Usamos set() para evitar duplicados en el mismo texto (ej: "Python y Python")
            tech_encontradas = list(set([ent.text.lower() for ent in doc.ents if ent.label_ == LABEL_NAME]))
            
            # Si la lista está vacía, guardamos NaN para limpieza posterior
            results.append(tech_encontradas if tech_encontradas else np.nan)
            
            # Imprimir progreso cada vez que terminamos un chunk
            if (i + 1) % chunk_size == 0 or (i + 1) == total:
                print(f"✅ Procesados: {i + 1}/{total}")
                
        return results

    # --- EJECUCIÓN ---
    # Nota: Pasamos solo la columna de texto, no el ID
    df['description'] = process_safely(df['description'])

    # --- PASO 5: Guardar resultado ---
    output_name = "data/dataset_PostNLP.csv"
    df.to_csv(output_name, index=False)
    print(f"✅ ¡Hecho! Archivo guardado como: {output_name}")


if __name__ == "__main__":
    main()