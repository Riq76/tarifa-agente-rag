# -*- coding: utf-8 -*-
"""Carga y trocea (chunking) el documento fuente (PDF/CSV) en pasajes de texto
listos para indexar. Este es el paso de "leer y procesar el documento" que pide
el challenge."""

import csv
from pathlib import Path
from pypdf import PdfReader


def _chunk_text(text, source, chunk_size=800, overlap=150):
    """Divide un texto largo en fragmentos solapados de tamaño fijo."""
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        piece = text[start:end].strip()
        if piece:
            chunks.append({"source": source, "text": piece})
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def load_pdf_chunks(pdf_path, chunk_size=800, overlap=150):
    """Extrae texto del PDF página por página y lo trocea."""
    reader = PdfReader(str(pdf_path))
    chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        chunks.extend(_chunk_text(text, f"PDF página {i + 1}", chunk_size, overlap))
    return chunks


def load_csv_chunks(csv_path):
    """Convierte cada fila pregunta/respuesta del CSV de FAQ en un fragmento propio."""
    chunks = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            categoria = row.get("categoria", "").strip()
            pregunta = row.get("pregunta", "").strip()
            respuesta = row.get("respuesta", "").strip()
            text = f"Pregunta: {pregunta}\nRespuesta: {respuesta}"
            chunks.append({"source": f"FAQ #{i} ({categoria})", "text": text})
    return chunks


def load_all_chunks(data_dir):
    """Carga y combina los fragmentos del PDF y del CSV de un directorio de datos."""
    data_dir = Path(data_dir)
    chunks = []
    pdf_path = data_dir / "Base_Conocimiento_Optium_Energia.pdf"
    csv_path = data_dir / "FAQ_Optium_Energia.csv"
    if pdf_path.exists():
        chunks.extend(load_pdf_chunks(pdf_path))
    if csv_path.exists():
        chunks.extend(load_csv_chunks(csv_path))
    return chunks
