# -*- coding: utf-8 -*-
"""Paso de generación: arma el prompt con el contexto recuperado y llama a la
API de Google Gemini para redactar la respuesta final."""

import os

from google import genai

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

SYSTEM_PROMPT = (
    "Eres el asistente virtual de atención a clientes de Voltia Energía SpA, "
    "empresa chilena de asesoría en gestión energética. "
    "Responde SIEMPRE en español, de forma breve y directa. "
    "Usa exclusivamente la información del CONTEXTO entregado; si la respuesta "
    "no está en el contexto, dilo explícitamente y no inventes datos ni montos. "
    "Al final de la respuesta, indica entre paréntesis la(s) fuente(s) del "
    "contexto que usaste (por ejemplo: (Fuente: FAQ #6) o (Fuente: PDF página 4))."
)


def build_context(chunks):
    return "\n\n".join(f"[{c['source']}] {c['text']}" for c in chunks)


def build_prompt(question, chunks):
    return f"CONTEXTO:\n{build_context(chunks)}\n\nPREGUNTA DEL CLIENTE:\n{question}"


def answer(question, chunks, model=None, api_key=None, max_tokens=1024):
    client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
    prompt = build_prompt(question, chunks)
    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "max_output_tokens": max_tokens,
            # Sin "thinking" extendido: es una respuesta de FAQ corta, no un
            # problema de razonamiento complejo, y el thinking consume del
            # mismo presupuesto de max_output_tokens.
            "thinking_config": {"thinking_budget": 0},
        },
    )
    return response.text
