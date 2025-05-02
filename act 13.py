import os
import sys
import time
import mmap
from datetime import datetime
from collections import defaultdict

class RobustSearchEngine:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.log_file = os.path.join(base_dir, "a13_2889834.txt")
        self.init_log()
        self.setup_files()
    
    def init_log(self):
        with open(self.log_file, 'w', encoding='utf-8', errors='replace') as log:
            log.write(f"Log de búsquedas - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write("="*50 + "\n")
    
    def setup_files(self):
        try:
            self.documents = self.load_documents()
            self.dict_index = self.build_dictionary_index()
            self.posting_mmap = self.setup_posting_file()
            
            with open(self.log_file, 'a', encoding='utf-8', errors='replace') as log:
                log.write("\n[INICIO] Motor de búsqueda configurado correctamente\n")
                log.write(f"Documentos indexados: {len(self.documents)}\n")
                log.write(f"Términos únicos: {len(self.dict_index)}\n")
        
        except Exception as e:
            self.log_error(f"Error en setup_files: {str(e)}")
            sys.exit(1)
    
    def load_documents(self):
        documents = {}
        try:
            with open(os.path.join(self.base_dir, 'documents_filtered.txt'), 
                     'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    parts = line.strip().split(';')
                    if len(parts) >= 2:
                        try:
                            doc_id = int(parts[0])
                            documents[doc_id] = parts[1]
                        except:
                            continue
            return documents
        except Exception as e:
            self.log_error(f"Error cargando documentos: {str(e)}")
            sys.exit(1)
    
    def build_dictionary_index(self):
        index = {}
        try:
            with open(os.path.join(self.base_dir, 'token_dictionary_filtered.txt'), 
                     'r', encoding='utf-8', errors='replace') as f:
                position = 0
                for line in f:
                    if ';' not in line:
                        continue
                    term = line.split(';')[0].lower().strip()
                    if term:
                        index[term] = position
                        position += len(line.encode('utf-8'))
            return index
        except Exception as e:
            self.log_error(f"Error construyendo índice: {str(e)}")
            sys.exit(1)
    
    def setup_posting_file(self):
        try:
            posting_path = os.path.join(self.base_dir, 'token_posting_filtered.txt')
            f = open(posting_path, 'rb')
            return mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        except Exception as e:
            self.log_error(f"Error cargando posting file: {str(e)}")
            sys.exit(1)
    
    def log_search(self, query, results, search_time):
        with open(self.log_file, 'a', encoding='utf-8', errors='replace') as log:
            log.write(f"\n[Busqueda] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write(f"Término: {query}\n")
            log.write(f"Tiempo: {search_time:.6f}s\n")
            log.write(f"Resultados: {len(results)}\n")
            for i, (doc, score) in enumerate(results[:10], 1):
                log.write(f"{i}. {doc} ({score:.4f})\n")
    
    def log_error(self, message):
        with open(self.log_file, 'a', encoding='utf-8', errors='replace') as log:
            log.write(f"\n[ERROR] {message}\n")
    
    def safe_readline(self):
        line = self.posting_mmap.readline()
        try:
            return line.decode('utf-8', errors='replace').strip()
        except:
            return ""
    
    def search_terms(self, terms):
        results = defaultdict(float)
        for term in terms:
            term = term.lower().strip()
            if term not in self.dict_index:
                continue
            
            self.posting_mmap.seek(self.dict_index[term])
            for _ in range(100):  # Limitar resultados por término
                line = self.safe_readline()
                if not line:
                    break
                
                if ';' not in line:
                    continue
                
                try:
                    parts = line.split(';')
                    doc_id = int(parts[1])
                    score = float(parts[2])
                    results[doc_id] += score * (1 + 0.2 * len(terms))
                except:
                    continue
        
        # Ordenar y obtener top 10
        sorted_results = sorted(
            [(doc_id, score) for doc_id, score in results.items()],
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return [(self.documents.get(doc_id, f"Documento {doc_id}"), score) 
                for doc_id, score in sorted_results]

def main():
    if len(sys.argv) < 2:
        print("Uso: python Act_13.py <término1> [término2 ...]")
        sys.exit(1)
    
    # BASE_DIR = r"C:\Users\Jair\Downloads\Fase3\Fase3"
    BASE_DIR = r"C:\Users\hernandf\OneDrive - Hewlett Packard Enterprise\Documents\Semestre Empresarial\proyectos de tecnologias\Fase 4\Fase3\Fase3"
    try:
        engine = RobustSearchEngine(BASE_DIR)
        terms = sys.argv[1:]
        start_time = time.time()
        results = engine.search_terms(terms)
        search_time = time.time() - start_time
        
        print(f"\nResultados para: {' '.join(terms)}")
        print(f"Tiempo de búsqueda: {search_time:.4f}s")
        print("-" * 50)
        for i, (doc, score) in enumerate(results[:10], 1):
            print(f"{i:>2}. {doc} (score: {score:.4f})")
        
        engine.log_search(' '.join(terms), results, search_time)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if "--test" in sys.argv:
        test_terms = [
            "Gauch", "elephants", "CSCE", "Arkansas", "gift",
            "abcdef", "20", "20.07", "123-456-7890", 
            "lawyer consumers", "garden computer",
            "United States laws", "Medición de tiempos"
        ]
        
        engine = RobustSearchEngine(r"C:\Users\hernandf\OneDrive - Hewlett Packard Enterprise\Documents\Semestre Empresarial\proyectos de tecnologias\Fase 4\Fase3\Fase3")
        for term in test_terms:
            print(f"\nTesting: {term}")
            results = engine.search_terms([term])
            print(f"Resultados: {len(results)}")
            for i, (doc, score) in enumerate(results[:5], 1):
                print(f"  {i}. {doc} ({score:.2f})")
        engine.log_search("Prueba completa", [], 0)
    else:
        main()