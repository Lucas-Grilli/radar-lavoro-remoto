"""Schema del profilo utente — i 6 campi del form, confermati 19/08.

Modalita (sempre remoto) e lingua di ricerca (sempre inglese) sono fisse nel
prodotto e non fanno parte del profilo: non si chiedono all'utente.
"""

from dataclasses import dataclass, field

LEVELS = ("junior", "mid", "senior", "qualsiasi")

# Bucket di regione -> query esplicite per sito. Mai "Worldwide" da solo
# (su LinkedIn "Worldwide" pesca un pool quasi separato
# dalle query esplicite per regione, 2 sovrapposizioni su 190 annunci).
# Indeed è aggiunto solo dove è già stato validato dare segnale (USA, UK) —
# altrove ha reso 0 match utili nei test, non vale il costo della richiesta.
# Glassdoor e ZipRecruiter provati il 19/08: entrambi rispondono 403 su ogni
# chiamata senza proxy — rimossi, non vale la pena tenerli attivi a vuoto.
# Da riconsiderare solo se/quando si decide di pagare un proxy (rifiutato
# per ora).
REGION_MAP = {
    "USA": [
        {"site": "linkedin", "location": "United States"},
        {"site": "indeed", "location": "United States", "country_indeed": "USA"},
    ],
    "Canada": [
        {"site": "linkedin", "location": "Canada"},
    ],
    "UK & Irlanda": [
        {"site": "linkedin", "location": "United Kingdom"},
        {"site": "indeed", "location": "United Kingdom", "country_indeed": "UK"},
    ],
    "Europa": [
        {"site": "linkedin", "location": "Europe"},
    ],
    "Asia-Pacifico": [
        {"site": "linkedin", "location": "Australia"},
    ],
}

ALL_REGIONS = tuple(REGION_MAP.keys())

# Segnali di seniority nel titolo — euristica economica (no fetch descrizione).
SENIORITY_PATTERNS = {
    "junior": r"\b(junior|jr\.?|entry.level|graduate|intern(ship)?|apprendist\w*)\b",
    "mid": r"\b(mid.level|associate)\b",
    "senior": r"\b(senior|sr\.?|lead|principal|staff|head of|director|manager)\b",
}


@dataclass
class Profile:
    ruoli: list[str]                       # obbligatorio — tag liberi
    zone: list[str]                        # obbligatorio — sottoinsieme di ALL_REGIONS, o ["Tutto il mondo"]
    competenze: list[str] = field(default_factory=list)   # opzionale
    livello: str = "qualsiasi"             # junior|mid|senior|qualsiasi
    esclusioni: list[str] = field(default_factory=list)   # opzionale
    altro: str = ""                        # opzionale — smistato da LLM, vedi llm_dispatch.py

    def __post_init__(self):
        if not self.ruoli:
            raise ValueError("almeno un ruolo cercato è obbligatorio")
        if not self.zone:
            raise ValueError("almeno una zona geografica è obbligatoria")
        self.livello = self.livello.lower()
        if self.livello not in LEVELS:
            raise ValueError(f"livello deve essere uno di {LEVELS}")

    def regions_resolved(self) -> list[str]:
        """'Tutto il mondo' si espande nell'unione di tutti i bucket espliciti."""
        if any(z.lower() in ("tutto il mondo", "worldwide") for z in self.zone):
            return list(ALL_REGIONS)
        unknown = [z for z in self.zone if z not in REGION_MAP]
        if unknown:
            raise ValueError(f"zone non riconosciute: {unknown} — valide: {ALL_REGIONS}")
        return list(self.zone)
