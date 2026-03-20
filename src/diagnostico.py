import pdfplumber
from pathlib import Path

# Buscamos el primer PDF que encuentres en la carpeta
folder = Path.cwd() / "data" / "raw"
files = list(folder.glob("*.pdf"))

if files:
    target_file = files[0] # Tomamos el primero
    print(f"--- ANALIZANDO: {target_file.name} ---")
    
    with pdfplumber.open(target_file) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        
        print("\n--- INICIO DEL TEXTO CRUDO ---")
        print(text)
        print("--- FIN DEL TEXTO CRUDO ---\n")
        
        # También ayuda ver si hay tablas ocultas
        tables = first_page.extract_tables()
        if tables:
            print(f"Se encontraron {len(tables)} tablas/estructuras.")
            print("Muestra de la primera fila:", tables[0][0])
else:
    print("No encontré PDFs en data/raw para analizar.")