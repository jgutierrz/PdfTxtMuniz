import os
import sys
from pathlib import Path
import pandas as pd
import pdfplumber

# Agregamos la carpeta src para encontrar la lógica de extracción
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from procesar_ventas import process_file_content, clean_text, InvoiceData, fields

def ejecutar():
    # Usamos la carpeta 'data' por defecto o pedimos una
    ruta_carpeta = input("Carpeta de PDFs (Presiona Enter para usar 'data'): ").strip()
    if not ruta_carpeta:
        ruta_carpeta = "data"
    
    path_entrada = Path(ruta_carpeta)
    archivos = list(path_entrada.glob("*.pdf"))
    
    if not archivos:
        print(f"No se encontraron PDFs en: {path_entrada.absolute()}")
        return

    print(f"Procesando {len(archivos)} archivos...")
    resultados = []

    for archivo in archivos:
        try:
            with pdfplumber.open(archivo) as pdf:
                texto = clean_text(pdf.pages[0].extract_text())
                # Usamos la función de procesar_ventas.py
                datos = process_file_content(texto, archivo.name)
                resultados.append(datos.__dict__)
                print(f"✅ {archivo.name} procesado.")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            datos_error = InvoiceData(archivo_origen=archivo.name, error=error_msg)
            resultados.append(datos_error.__dict__)
            print(f"❌ {archivo.name}: {error_msg}")

    if resultados:
        df = pd.DataFrame(resultados)
        # Ordenamos las columnas según InvoiceData
        cols = [f.name for f in fields(InvoiceData)]
        df = df.reindex(columns=cols).fillna("")
        
        output = path_entrada / "Reporte_Ventas.xlsx"
        df.to_excel(output, index=False)
        print(f"\nTerminado. Archivo creado en: {output}")

if __name__ == "__main__":
    ejecutar()