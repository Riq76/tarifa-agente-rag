# -*- coding: utf-8 -*-
"""Paso de generación: arma el prompt con el contexto recuperado y llama a la
API de Claude (Anthropic) para redactar la respuesta final."""

import os

from anthropic import Anthropic

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = (
    "Eres el asistente virtual de atención a clientes de Optium Energía SpA, "
    "empresa chilena de servicios de gestión energética. "
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


def answer(question, chunks, model=None, api_key=None, max_tokens=500):
    client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
    prompt = build_prompt(question, chunks)
    response = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
