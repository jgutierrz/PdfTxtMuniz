import re
from dataclasses import dataclass, fields
from typing import Optional

# --- PATRONES REGEX ---
PATRON_MONEDA = r"([A-Z]{3}|S/|S/\.|S/\s|\$)"
PATRON_MONTO = r"([\d,\.\s]+)"

DOC_TYPES = {
    "BOLETA DE VENTA": "BOLETA DE VENTA",
    "FACTURA ELECTRÓNICA": "FACTURA ELECTRONICA",
    "NOTA DE CRÉDITO": "NOTA DE CREDITO",
    "NOTA DE DÉBITO": "NOTA DE DEBITO"
}

RE_SERIE_NRO = re.compile(r"Nro\.?\s+([A-Z0-9]+)-(\d+)")
RE_FECHA_EMISION = re.compile(r"Fecha\s*:\s*(\d{2}-[A-Z]{3}-\d{4})")
RE_FECHA_VENC = re.compile(r"Fecha de Vencimiento\s*:\s*(\d{2}-[A-Z]{3}-\d{4})")
RE_CLIENTE_BLOQUE = re.compile(r"Señor\(es\)\s*:\s*(.*?)(?:Dirección|VAT|RUC|DNI)", re.DOTALL)
RE_RUC = re.compile(r"RUC\s*[:\.]\s*(\d{11})")
RE_VAT = re.compile(r"VAT\s*[:\.]\s*([A-Z0-9]+)")
RE_DNI = re.compile(r"DNI\s*[:\.]\s*(\d+)")
RE_OT = re.compile(r"OT\s*[:\.]\s*([\w\-\/]+)")
RE_REF = re.compile(r"(?:Documento que modifica|Referencia)\s*[:\.]?\s*([A-Z0-9]+-\d+)", re.IGNORECASE)
RE_DETRACCION = re.compile(rf"Monto Detracción\s*:\s*([A-Z/\.]+)\s*{PATRON_MONTO}")

RE_GRAVADAS = re.compile(rf"OPERACIONES GRAVADAS\s+{PATRON_MONEDA}\s+{PATRON_MONTO}")
RE_EXONERADAS = re.compile(rf"OPERACIONES EXONERADAS\s+{PATRON_MONEDA}\s+{PATRON_MONTO}")
RE_INAFECTAS = re.compile(rf"OPERACIONES INAFECTAS\s+{PATRON_MONEDA}\s+{PATRON_MONTO}")
RE_IGV = re.compile(rf"IGV.*?{PATRON_MONEDA}\s+{PATRON_MONTO}")
RE_TOTAL = re.compile(rf"(?:TOTAL VENTA|PRECIO TOTAL)\s+{PATRON_MONEDA}\s+{PATRON_MONTO}")

@dataclass
class InvoiceData:
    archivo_origen: str
    fecha_emision: str = ""
    fecha_vencimiento: str = ""
    tipo_documento: str = ""
    serie_documento: str = ""
    numero_documento: str = ""
    ruc_cliente: str = ""
    cliente_nombre: str = ""
    moneda: str = ""
    op_gravadas: float = 0.0
    op_exoneradas: float = 0.0
    op_inafectas: float = 0.0
    igv: float = 0.0
    total: float = 0.0
    monto_detraccion: str = ""
    cod_ot: str = ""
    doc_referencia: str = ""
    error: str = ""

# --- FUNCIONES DE APOYO ---
def clean_text(text: Optional[str]) -> str:
    return " ".join(text.split()) if text else ""

def parse_amount(text_amount: Optional[str]) -> float:
    if not text_amount: return 0.0
    try:
        return float(text_amount.replace(",", "").replace(" ", ""))
    except ValueError: return 0.0

def normalize_date(date_text: Optional[str]) -> str:
    if not date_text: return ""
    meses = {"ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04", "MAY": "05", "JUN": "06",
             "JUL": "07", "AGO": "08", "SET": "09", "OCT": "10", "NOV": "11", "DIC": "12"}
    try:
        parts = date_text.split("-")
        if len(parts) == 3:
            return f"{parts[0]}/{meses.get(parts[1].upper())}/{parts[2]}"
    except: pass
    return date_text

def normalize_currency(currency_text: Optional[str]) -> str:
    if not currency_text: return ""
    text = currency_text.upper().replace(".", "").strip()
    return "PEN" if "S/" in text or "PEN" in text else "USD" if "USD" in text or "$" in text else text

# --- EXTRACCIÓN ---
def process_file_content(text: str, filename: str) -> InvoiceData:
    data = InvoiceData(archivo_origen=filename)
    
    # Tipo, Serie, Número y Fechas
    for doc_name, std_name in DOC_TYPES.items():
        if re.search(doc_name, text, re.IGNORECASE):
            data.tipo_documento = std_name
            break
    if m := RE_SERIE_NRO.search(text):
        data.serie_documento, data.numero_documento = m.groups()
    if m := RE_FECHA_EMISION.search(text): data.fecha_emision = normalize_date(m.group(1))
    if m := RE_FECHA_VENC.search(text): data.fecha_vencimiento = normalize_date(m.group(1))
    if m := RE_OT.search(text): data.cod_ot = m.group(1)
    if m := RE_REF.search(text): data.doc_referencia = m.group(1)

    # Cliente
    if m_c := RE_CLIENTE_BLOQUE.search(text):
        data.cliente_nombre = m_c.group(1).strip()
        ctx = text[m_c.end():]
        if mid := (RE_RUC.search(ctx) or RE_VAT.search(ctx) or RE_DNI.search(ctx)):
            data.ruc_cliente = mid.group(1)

    # Montos
    def _get_val(reg, attr):
        if m := reg.search(text):
            setattr(data, attr, parse_amount(m.group(2)))
            if not data.moneda: data.moneda = normalize_currency(m.group(1))

    _get_val(RE_GRAVADAS, "op_gravadas")
    _get_val(RE_EXONERADAS, "op_exoneradas")
    _get_val(RE_INAFECTAS, "op_inafectas")
    _get_val(RE_IGV, "igv")
    _get_val(RE_TOTAL, "total")
    if m := RE_DETRACCION.search(text): data.monto_detraccion = f"{m.group(1)} {m.group(2)}"

    return data