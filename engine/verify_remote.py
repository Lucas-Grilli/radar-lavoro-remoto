"""Verifica remoto reale — il filtro is_remote di LinkedIn non è affidabile.

Test 19/08: su 72 annunci "in linea" con is_remote=True impostato in ricerca,
solo 13 confermavano il remoto nella descrizione reale; 24 nominavano
on-site/hybrid (un annuncio diceva letteralmente "Fully on-site — Barcelona
or Valencia" pur passando il filtro). Il campo `is_remote` restituito da
JobSpy è un'euristica testuale su titolo+descrizione+location — senza aver
scaricato la descrizione, resta quasi sempre a False e non dice niente.

Costa una richiesta HTTP per annuncio: si applica solo al tier "in linea"
(quello che l'utente vede per primo), non a tutto il dataset.
"""

import random
import re
import time

import pandas as pd
from jobspy.linkedin import LinkedIn
from jobspy.model import DescriptionFormat, ScraperInput, Site

ONSITE_RE = re.compile(r"\bon-?site\b|\bin office\b|\bin-office\b|\bhybrid\b", re.I)
REMOTE_RE = re.compile(r"\bremote\b|\bwork from home\b|\bwfh\b", re.I)


def _strip_markdown(text: str) -> str:
    """La versione pip di JobSpy non ha DescriptionFormat.PLAIN (solo
    MARKDOWN/HTML) — puliamo qui invece di dipendere da una feature assente
    nel pacchetto pubblicato."""
    if not text:
        return ""
    text = re.sub(r"\*\*|\*|__|_", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    return text


def _snippet(text: str, n: int = 220) -> str | None:
    if not text:
        return None
    t = re.sub(r"\s+", " ", _strip_markdown(text)).strip()
    return (t[:n].rsplit(" ", 1)[0] + "…") if len(t) > n else t


def verify_linkedin_jobs(df: pd.DataFrame, domain_match=None, delay_range=(1.0, 1.8)) -> pd.DataFrame:
    """Scarica la descrizione reale per ogni riga LinkedIn: classifica il
    remoto e, se `domain_match` è dato (competenze dell'utente), controlla
    se compaiono nella descrizione — stesso fetch, nessuna richiesta in più.
    Ritorna df con 'remote_status', 'desc_snippet' e 'competenze_confermate'
    aggiunti."""
    if df.empty:
        df["remote_status"] = []
        df["desc_snippet"] = []
        df["competenze_confermate"] = []
        return df

    scraper = LinkedIn()
    scraper.scraper_input = ScraperInput(
        site_type=[Site.LINKEDIN], search_term="x", description_format=DescriptionFormat.MARKDOWN
    )

    statuses, snippets, domain_hits = [], [], []
    for row in df.itertuples():
        job_id = str(row.job_url).rstrip("/").split("/")[-1]
        try:
            details = scraper._get_job_details(job_id)
            desc = _strip_markdown(details.get("description") or "")
        except Exception:
            desc = ""

        statuses.append(_classify_text(desc))
        snippets.append(_snippet(desc))
        domain_hits.append(bool(domain_match(desc)) if domain_match else None)
        time.sleep(random.uniform(*delay_range))

    df = df.copy()
    df["remote_status"] = statuses
    df["desc_snippet"] = snippets
    df["competenze_confermate"] = domain_hits
    return df


def _classify_text(desc: str) -> str:
    has_onsite = bool(ONSITE_RE.search(desc or ""))
    has_remote = bool(REMOTE_RE.search(desc or ""))
    if not desc:
        return "non verificato"
    if has_onsite and not has_remote:
        return "SOSPETTO on-site/hybrid"
    if has_remote:
        return "remote confermato"
    return "ambiguo"


def verify_remote_status(df: pd.DataFrame, domain_match=None) -> pd.DataFrame:
    """Dispatcher per fonte: Indeed porta già la descrizione completa nella
    ricerca (nessuna richiesta extra); LinkedIn no, richiede il fetch della
    pagina — vedi verify_linkedin_jobs. Da chiamare solo sulle righe che
    l'utente vedrà per prime (tier 'In linea'), non su tutto il dataset.

    `domain_match`: matcher delle competenze (da build_query.make_matcher),
    se dato calcola anche 'competenze_confermate' sulla descrizione reale."""
    if df.empty:
        return df

    li_mask = df["site"] == "linkedin"
    parts = []
    if (~li_mask).any():
        indeed_part = df[~li_mask].copy()
        clean_desc = indeed_part["description"].apply(lambda d: _strip_markdown(d or ""))
        indeed_part["remote_status"] = clean_desc.apply(_classify_text)
        indeed_part["desc_snippet"] = clean_desc.apply(_snippet)
        indeed_part["competenze_confermate"] = (
            clean_desc.apply(lambda d: bool(domain_match(d))) if domain_match else None
        )
        parts.append(indeed_part)
    if li_mask.any():
        parts.append(verify_linkedin_jobs(df[li_mask], domain_match=domain_match))

    return pd.concat(parts, ignore_index=True) if parts else df
