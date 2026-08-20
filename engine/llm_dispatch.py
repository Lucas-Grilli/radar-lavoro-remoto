"""Smistamento del campo libero "altro da sapere".

È l'unico punto del motore che costa token, e costa **una chiamata per
ricerca** — non una per annuncio. Se il campo è vuoto (il caso normale) non
parte nessuna chiamata e il motore resta a costo zero.

Serve una chiave API Anthropic:
    - in locale:  set ANTHROPIC_API_KEY=sk-ant-...
    - su GitHub:  secret del repository

Senza chiave il motore non si ferma: stampa un avviso ben visibile, ignora
il campo e prosegue con gli altri filtri.
"""

import json
import os

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """Una persona sta cercando lavoro da remoto e ha scritto un \
testo libero nel campo "altro da sapere" di un form di ricerca.

Il tuo unico compito è smistare quel testo sui campi strutturati del form. \
Non aggiungere nulla che la persona non abbia detto o chiaramente implicato: \
se scrive "odio le multinazionali" NON inventare competenze, metti "multinazionale" \
tra le esclusioni. Se una parte del testo non è mappabile su nessun campo \
(una domanda, uno sfogo, un commento non azionabile), riportala in \
"nota_ignorata" invece di forzarla dentro un campo.

I termini che produci finiscono in una ricerca su bacheche di lavoro \
internazionali: scrivili in **inglese**, come apparirebbero nel titolo di un \
annuncio."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "ruoli_extra": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ruoli/titoli da aggiungere alla ricerca, in inglese. Vuoto se il testo non ne nomina.",
        },
        "competenze_extra": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Competenze/strumenti da aggiungere, in inglese. Vuoto se il testo non ne nomina.",
        },
        "esclusioni_extra": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Termini da escludere, in inglese. Vuoto se il testo non esclude nulla.",
        },
        "livello": {
            "type": "string",
            "enum": ["junior", "mid", "senior", "qualsiasi"],
            "description": "Solo se il testo lo rende esplicito, altrimenti 'qualsiasi'.",
        },
        "nota_ignorata": {
            "type": "string",
            "description": "Parti del testo non mappabili su nessun campo. Stringa vuota se tutto è stato mappato.",
        },
    },
    "required": ["ruoli_extra", "competenze_extra", "esclusioni_extra", "livello", "nota_ignorata"],
    "additionalProperties": False,
}


def dispatch_altro(testo: str) -> dict:
    """Testo libero -> dict con i campi da fondere nel profilo.
    Ritorna {} se il campo è vuoto. Solleva RuntimeError se manca la chiave
    o il pacchetto `anthropic` (il chiamante decide se è fatale)."""
    if not testo or not testo.strip():
        return {}

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY non impostata — il campo 'altro da sapere' "
            "richiede una chiave API Anthropic. In locale: "
            "set ANTHROPIC_API_KEY=sk-ant-... (Windows) / export su Linux-Mac. "
            "Su GitHub Actions: secret del repository."
        )

    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "pacchetto 'anthropic' non installato — serve solo per il campo "
            "'altro da sapere'. Installalo con: pip install anthropic"
        )

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": testo}],
        output_config={"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def merge_altro(profile, altro_result: dict):
    """Applica il risultato di dispatch_altro al profilo, in-place."""
    if not altro_result:
        return profile

    profile.ruoli.extend(altro_result.get("ruoli_extra", []))
    profile.competenze.extend(altro_result.get("competenze_extra", []))
    profile.esclusioni.extend(altro_result.get("esclusioni_extra", []))

    livello = altro_result.get("livello")
    if livello and livello != "qualsiasi" and profile.livello == "qualsiasi":
        profile.livello = livello

    return profile
