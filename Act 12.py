import os
import time
import re
import math
import pdfplumber
from collections import defaultdict

def load_stoplist(pdf_file):
    stop_words = set()
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            words = text.split()
            for word in words:
                stop_words.add(word.lower())
    return stop_words

def process_files(input_dir, stoplist=None, suffix="", min_frequency=1):
    """Procesa archivos con o sin stoplist"""
    start_time = time.time()
    
    files = sorted([f for f in os.listdir(input_dir) if f.endswith(".txt")])
    doc_ids = {file: idx + 1 for idx, file in enumerate(files)}
    
    # Nombres de archivos de salida
    output_dict = f"token_dictionary{suffix}.txt"
    output_posting = f"token_posting{suffix}.txt"
    output_docs = f"documents{suffix}.txt"
    output_log = f"log{suffix}.txt"
    
    # Escribir archivo de documentos
    with open(output_docs, "w", encoding="utf-8") as docs_out:
        for file, doc_id in doc_ids.items():
            file_path = os.path.join(input_dir, file)
            docs_out.write(f"{doc_id};{file};{file_path}\n")
    
    doc_data = {}
    df_counts = defaultdict(int)
    
    for file in files:
        doc_id = doc_ids[file]
        file_path = os.path.join(input_dir, file)
        term_freq = {}
        total_tokens = 0
        
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                # Extraer tokens manteniendo números, guiones, puntos, etc.
                tokens = re.findall(r'\b[\w.-]+\b', line.lower())
                filtered = []
                for token in tokens:
                    # Aplicar filtros solo si hay stoplist
                    if stoplist is not None:
                        if len(token) == 1 or token in stoplist:
                            continue
                    filtered.append(token)
                
                total_tokens += len(filtered)
                for token in filtered:
                    term_freq[token] = term_freq.get(token, 0) + 1
        
        filtered_terms = {k: v for k, v in term_freq.items() if v >= min_frequency}
        for term in filtered_terms:
            df_counts[term] += 1
        
        doc_data[doc_id] = {
            "terms": filtered_terms,
            "total_tokens": total_tokens
        }
    
    total_docs = len(files)
    idf = {term: math.log(total_docs / df) if df != 0 else 0 for term, df in df_counts.items()}
    
    # Escribir diccionario
    with open(output_dict, "w", encoding="utf-8") as dict_out:
        for term in df_counts:
            dict_out.write(f"{term};{df_counts[term]};{idf[term]:.6f}\n")
    
    # Escribir posting file
    with open(output_posting, "w", encoding="utf-8") as post_out:
        for doc_id, data in doc_data.items():
            total_t = data["total_tokens"]
            for term, count in data["terms"].items():
                tf = count / total_t if total_t > 0 else 0
                tf_idf = tf * idf.get(term, 0)
                post_out.write(f"{term};{doc_id};{tf_idf:.6f}\n")
    
    # Archivo log
    with open(output_log, "w", encoding="utf-8") as log:
        log.write(f"Documentos procesados: {total_docs}\n")
        log.write(f"Términos únicos: {len(df_counts)}\n")
        log.write(f"Tiempo de ejecución: {time.time() - start_time:.2f} segundos\n")

if __name__ == "__main__":
    input_dir = r"C:\Users\Jair\Downloads\Fase3\Fase3\CS13309_Archivos_HTML\Output"
    stoplist_pdf = r"C:\Users\Jair\Downloads\Fase3\Fase3\Actividad9_stoplist.pdf"
    
    # Procesar CON stoplist
    print("Procesando CON stoplist...")
    stoplist = load_stoplist(stoplist_pdf)
    process_files(input_dir, stoplist=stoplist, suffix="_filtered", min_frequency=2)
    
    # Procesar SIN stoplist
    print("\nProcesando SIN stoplist...")
    process_files(input_dir, stoplist=None, suffix="_full", min_frequency=1)
    
    print("\nProceso completado. Se generaron dos conjuntos de archivos:")
    print("- *_filtered.txt (con stoplist y frecuencia mínima 2)")
    print("- *_full.txt (sin stoplist y todos los tokens)")