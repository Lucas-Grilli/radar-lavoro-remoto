"""Filtro di pertinenza sul ruolo + esclusioni + seniority.

Lezione emersa testando su un profilo del settore AI: un filtro a condizione singola
("ruolo" O "dominio") produce falsi positivi enormi — es. "Advanced Clinical
Biomechanics Specialist" passava perché "specialist" da solo è troppo
generico.

Lezione del consolidamento (stesso giorno, seconda passata): richiedere le
competenze specifiche (es. "Copilot", "n8n") nel TITOLO le fa quasi sparire
— quei nomi compaiono nella descrizione molto più spesso che nel titolo. Le
competenze non decidono più il tier: diventano un badge "confermate" o meno,
calcolato su verify_remote.py durante il fetch della descrizione che si fa
già per il tier "In linea" — stesso costo, nessuna richiesta in più.

Tre fasce:
  - "In linea": il ruolo matcha nel titolo
  - "Fuori target": SOLO esclusione esplicita o disallineamento di livello —
    mai per "il ruolo non matcha", quello è "Generico"
  - "Generico": tutto il resto
"""

import re

import pandas as pd

from .profile import SENIORITY_PATTERNS


def _seniority_mismatch(title: str, livello: str) -> bool:
    """Esclude solo se il titolo dichiara ESPLICITAMENTE un livello diverso
    da quello richiesto — un titolo senza indicazione di livello non è mai
    escluso per questo motivo."""
    if livello == "qualsiasi" or not isinstance(title, str):
        return False
    wanted_pattern = SENIORITY_PATTERNS[livello]
    if re.search(wanted_pattern, title, re.I):
        return False
    for lvl, pattern in SENIORITY_PATTERNS.items():
        if lvl != livello and re.search(pattern, title, re.I):
            return True
    return False


def tier_row(title: str, role_match, exclude_match, livello: str) -> str:
    if not isinstance(title, str) or not title:
        return "Fuori target"
    if exclude_match and exclude_match(title):
        return "Fuori target"
    if _seniority_mismatch(title, livello):
        return "Fuori target"
    if role_match and role_match(title):
        return "In linea"
    return "Generico"


def apply_filters(df: pd.DataFrame, profile, filters: dict) -> pd.DataFrame:
    if df.empty:
        return df
    role_match, exclude_match = filters["role_match"], filters["exclude_match"]
    df = df.copy()
    df["tier"] = df["title"].apply(
        lambda t: tier_row(t, role_match, exclude_match, profile.livello)
    )
    return df
