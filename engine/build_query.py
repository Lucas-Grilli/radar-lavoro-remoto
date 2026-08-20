"""Profilo -> parametri di ricerca JobSpy + matcher di filtro.

Lezione del test 19/08: né LinkedIn né Indeed rispettano bene query booleane
complesse nel search_term (LinkedIn in particolare fa matching semantico,
non letterale) — il search_term serve solo a lanciare una rete larga.
La precisione vera viene dopo, in filter.py.

Lezione del consolidamento (stesso giorno): il matching a FRASE ESATTA è
troppo fragile — un titolo come "AI **and** Automation Lead" non contiene
la frase letterale "AI Automation" e sfuggiva al filtro. Si matcha invece
per PAROLE: un tag come "AI Automation" è soddisfatto se il titolo contiene
sia "AI" sia "Automation" da qualche parte, non necessariamente vicine.
"""

import re


def _words(tag: str) -> list[str]:
    return [w for w in re.split(r"\s+", tag.strip()) if w]


def make_matcher(tags: list[str]):
    """Ritorna una funzione title -> bool, vera se il titolo contiene TUTTE
    le parole di ALMENO UNO dei tag. None se la lista di tag è vuota."""
    groups = [_words(t) for t in tags if t.strip()]
    groups = [g for g in groups if g]
    if not groups:
        return None

    patterns = [[re.compile(r"\b" + re.escape(w) + r"\b", re.I) for w in g] for g in groups]

    def matcher(title) -> bool:
        if not isinstance(title, str) or not title:
            return False
        return any(all(p.search(title) for p in group) for group in patterns)

    return matcher


def search_term(profile) -> str:
    """Rete larga per il search_term della chiamata JobSpy — precisione dopo."""
    terms = list(profile.ruoli) + list(profile.competenze)
    return " OR ".join(terms)


def build_filters(profile) -> dict:
    """
    Ritorna i matcher usati da filter.py:
      - role_match: obbligatorio, dai ruoli cercati
      - domain_match: solo se l'utente ha dato competenze — se assente, il
        tier "in linea" si decide sul solo ruolo (vedi filter.py)
      - exclude_match: dalle esclusioni dell'utente, se presenti
    """
    return {
        "role_match": make_matcher(profile.ruoli),
        "domain_match": make_matcher(profile.competenze),
        "exclude_match": make_matcher(profile.esclusioni),
    }
