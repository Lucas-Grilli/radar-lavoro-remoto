"""Esegue la ricerca JobSpy su regioni esplicite (mai 'Worldwide' da solo).

Richiede `python-jobspy` installato (vedi requirements.txt). Non punta al
una copia locale del sorgente di JobSpy — quella serve solo come riferimento
usata per leggere il sorgente durante il test del 19/08.

Bug di JobSpy trovato testando il profilo demo backend/JS (19/08): la
whitelist paesi di `Country.from_string` non copre tutti i paesi reali che
LinkedIn restituisce (es. "North Macedonia" manca) — e un solo annuncio con
un paese non in whitelist fa fallire l'INTERA chiamata `scrape_jobs`,
buttando via anche gli annunci già raccolti in quella chiamata. Patchato
sotto: un paese sconosciuto degrada a WORLDWIDE invece di far crashare tutto.
"""

import pandas as pd
from jobspy import scrape_jobs
from jobspy.model import Country

from .build_query import search_term
from .profile import REGION_MAP

_original_from_string = Country.from_string.__func__


def _lenient_from_string(cls, country_str):
    try:
        return _original_from_string(cls, country_str)
    except ValueError:
        return Country.WORLDWIDE


Country.from_string = classmethod(_lenient_from_string)


def run_search(profile, hours_old: int = 720, results_per_call: int = 50) -> pd.DataFrame:
    term = search_term(profile)
    regions = profile.regions_resolved()

    frames = []
    for region in regions:
        for call in REGION_MAP[region]:
            kwargs = dict(
                site_name=[call["site"]],
                search_term=term,
                location=call["location"],
                is_remote=True,
                results_wanted=results_per_call,
                hours_old=hours_old,
                verbose=0,
            )
            if "country_indeed" in call:
                kwargs["country_indeed"] = call["country_indeed"]

            try:
                df = scrape_jobs(**kwargs)
            except Exception as e:
                print(f"[avviso] {call['site']}/{region} fallita, salto: {e}")
                continue
            if df is None or df.empty:
                continue
            df["region"] = region
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates(subset=["title", "company"]).reset_index(drop=True)
    return merged
