# engine

Note tecniche per chi vuole modificarlo. Per usarlo basta il
[README principale](../README.md).

## File

| File | Cosa fa |
|---|---|
| `ask.py` | Le cinque domande iniziali |
| `profile.py` | Schema del profilo + mappa delle regioni verso le bacheche |
| `build_query.py` | Profilo → termini di ricerca larghi + matcher di filtro |
| `search.py` | Chiama JobSpy su ogni regione esplicita richiesta |
| `filter.py` | Assegna la fascia (In linea / Generico / Fuori target) |
| `verify_remote.py` | Apre gli annunci in linea: verifica remoto e competenze |
| `llm_dispatch.py` | Smista il campo "altro da sapere" (opzionale, richiede una chiave API) |
| `render_dashboard.py` | Genera la pagina HTML statica |
| `run.py` | Orchestratore + interfaccia a riga di comando |

## Trappole già pagate

Se tocchi il codice, queste sono le cose che sembrano giuste e non lo sono.
Sono tutte emerse costruendolo, non teoriche.

**Il matching a frase esatta è troppo fragile.** Un titolo come
"AI **and** Automation Lead" non contiene la frase letterale "AI Automation" e
sfuggiva al filtro. `make_matcher()` matcha per parole: un tag multi-parola è
soddisfatto se tutte le sue parole compaiono nel titolo, anche lontane.

**"Fuori target" non è il default di "nessun match".** Ci finisce solo chi è
scartato da un'esclusione esplicita o da un livello dichiarato diverso. Un
annuncio che semplicemente non corrisponde è "Generico" — la ricerca getta una
rete larga, e non tutto quello che pesca è spazzatura.

**Le competenze non possono decidere il tier.** Cercare gli strumenti
specifici (es. "Copilot", "n8n") nel *titolo* azzerava la fascia "In linea":
quei nomi stanno nella descrizione, quasi mai nel titolo. Ora le competenze si
cercano nella descrizione completa, riusando il fetch che si fa già per la
verifica del remoto — costo zero in più — e diventano un badge, non un
cancello.

**`DescriptionFormat.PLAIN` non esiste** nel pacchetto `python-jobspy` di PyPI
(solo `MARKDOWN` e `HTML`). Il codice usa `MARKDOWN` più uno strip manuale.

**La whitelist paesi di JobSpy è incompleta** e un solo annuncio con un paese
fuori lista fa fallire *l'intera chiamata*, buttando via anche gli annunci già
raccolti (successo con "North Macedonia"). `search.py` applica un monkeypatch:
paese sconosciuto → `WORLDWIDE` invece di eccezione. C'è anche un `try/except`
per ogni coppia bacheca×regione, così un fallimento non fa perdere le altre.

**Le console Windows usano cp1252.** Senza
`sys.stdout.reconfigure(encoding="utf-8")` in `run.py`, gli accenti italiani
escono come `�` e il programma sembra rotto appena scaricato.

## Aggiungere una bacheca

Le bacheche stanno in `REGION_MAP` dentro `profile.py`, una voce per coppia
regione×bacheca. JobSpy ne supporta altre (Glassdoor, ZipRecruiter, Google
Jobs, Bayt, Naukri, BDJobs): aggiungerle è una riga.

Perché non ci sono già:

- **Glassdoor** e **ZipRecruiter** rispondono `403 Forbidden` a ogni richiesta
  senza un proxy a pagamento. Provate e tolte: meglio non interrogarle che far
  aspettare per niente.
- **Google Jobs** richiede una sintassi di ricerca copiata a mano da una
  ricerca fatta nel browser, e si blocca (`429`) quasi subito. Troppo fragile
  per un motore automatico.
- **Bayt** non ha filtro per località (solo parola chiave) e punta soprattutto
  al Golfo.
- **Naukri** e **BDJobs** coprono India e Bangladesh.
