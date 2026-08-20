# Radar Lavoro Remoto

![licenza MIT](https://img.shields.io/badge/licenza-MIT-black)
![stato: funzionante](https://img.shields.io/badge/stato-funzionante-brightgreen)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

Cerca lavoro **da remoto all'estero** su più bacheche insieme, scarta il rumore
e ti dice quali annunci sono davvero remoti — perché molti non lo sono, anche
quando il filtro della bacheca dice di sì.

Rispondi a cinque domande, aspetti qualche minuto, ti si apre una pagina con i
risultati ordinati per pertinenza e link diretti agli annunci.

---

## Il problema che risolve

Cercare lavoro remoto all'estero significa aprire quattro siti, ripetere la
stessa ricerca su ognuno, e leggere centinaia di annunci per scoprire che:

- **Il filtro "remoto" mente.** Nei test, su 72 annunci trovati con il filtro
  "solo remoto" di LinkedIn attivo, **solo 12 confermavano il remoto** nel testo
  dell'annuncio. Uno diceva letteralmente *"Fully on-site — Barcelona or
  Valencia"*. Questo strumento apre ogni annuncio e te lo dice.
- **Le ricerche per parola chiave pescano a caso.** Cercando "formatore AI"
  arrivano medici e istruttori di sicurezza (matchano "formatore") e ingegneri
  ML (matchano "AI"). Qui il filtro richiede che il **ruolo** sia nel titolo,
  e le tue competenze vengono cercate nel **testo** dell'annuncio, dove
  stanno davvero.
- **"Cerca in tutto il mondo" non cerca in tutto il mondo.** Su LinkedIn la
  ricerca "Worldwide" restituisce un insieme di annunci quasi **separato** da
  quello che ottieni cercando regione per regione (nei test: 2 annunci in comune
  su 190). Questo strumento interroga sempre ogni regione esplicitamente.

---

## Uso

Serve **Python 3.10 o superiore**. Due comandi:

```bash
pip install -r requirements.txt
python -m engine.run
```

Il programma ti fa cinque domande (che ruoli cerchi, dove, che livello…), poi
parte. A fine ricerca ti dice quale file aprire nel browser.

Non devi preparare nessun file: le risposte vengono salvate in
`mio-profilo.json`, così la volta dopo puoi rilanciare la stessa ricerca senza
ridigitare nulla:

```bash
python -m engine.run --profile mio-profilo.json
```

La ricerca richiede qualche minuto: interroga più bacheche, poi apre uno per
uno gli annunci migliori per verificare il remoto. È lenta di proposito — fa
le pause necessarie a non farsi bloccare dalle bacheche.

### Opzioni

| Opzione | Cosa fa |
|---|---|
| `--giorni 7` | Cerca solo negli ultimi 7 giorni (default: 30) |
| `--profile file.json` | Riusa un profilo salvato invece di rispondere alle domande |
| `--out pagina.html` | Scegli dove scrivere la pagina |
| `--no-verify` | Salta la verifica del remoto: molto più veloce, ma non saprai quali annunci sono davvero remoti |

---

## I campi del profilo

| Campo | Obbligatorio | Cosa farne |
|---|---|---|
| `ruoli` | **Sì** | I titoli che cerchi, **in inglese** (le bacheche estere sono in inglese). È l'unico campo che decide se un annuncio è "in linea". |
| `zone` | **Sì** | Dove cercare: `USA`, `Canada`, `UK & Irlanda`, `Europa`, `Asia-Pacifico`, oppure `Tutto il mondo` per tutte insieme. |
| `competenze` | No | I tuoi strumenti/tecnologie. Non escludono nessun annuncio: servono a marcare quelli che le nominano davvero, come conferma in più. |
| `livello` | No | `junior`, `mid`, `senior` o `qualsiasi` (default). Scarta gli annunci che dichiarano un livello **diverso** dal tuo; quelli che non lo dichiarano restano. |
| `esclusioni` | No | Parole che, se compaiono nel titolo, scartano l'annuncio. |
| `altro` | No | Testo libero, in italiano. Viene letto da un modello AI che lo smista sugli altri campi. **Richiede una chiave API Anthropic** (sotto). Senza chiave il campo viene ignorato con un avviso, e tutto il resto funziona. |

### Il campo "altro da sapere"

È l'unica parte che costa qualcosa, ed è opzionale. Costa **una chiamata per
ricerca** (non una per annuncio): frazioni di centesimo.

Per usarlo serve una chiave da [console.anthropic.com](https://console.anthropic.com):

```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-...

# Linux / macOS
export ANTHROPIC_API_KEY=sk-ant-...
```

Se lasci il campo vuoto, non parte nessuna chiamata e non spendi nulla.

---

## Come legge i risultati la pagina

Ogni annuncio finisce in una di tre fasce:

- **In linea** — il ruolo che cerchi è nel titolo. Sono questi che devi
  guardare, ed è la vista che si apre di default.
- **Generico** — la ricerca l'ha pescato ma il titolo non corrisponde al ruolo.
  Ogni tanto c'è qualcosa di buono, sfoglialo se hai tempo.
- **Fuori target** — scartato da una tua esclusione o dal livello.

Sugli annunci "in linea" trovi anche:

| Etichetta | Significato |
|---|---|
| `remote confermato` | L'annuncio dice esplicitamente che è remoto |
| `SOSPETTO on-site/hybrid` | Nomina ufficio o ibrido: **probabilmente non è remoto** nonostante il filtro |
| `ambiguo` | Il testo non lo dice in nessuna direzione — va aperto e letto |
| `competenze confermate` | Le tue competenze compaiono nel testo dell'annuncio |

I filtri in cima alla pagina (pertinenza, verifica remoto, regione, bacheca)
si combinano tra loro. La pagina è un file HTML statico: funziona offline,
puoi salvarlo o mandarlo a qualcuno.

---

## Limiti — leggili prima di lamentarti

- **Le bacheche bloccano chi cerca troppo.** Se lanci molte ricerche di fila,
  LinkedIn inizia a rifiutare le richieste (errore 429). Aspetta, o distanzia
  le ricerche. Non c'è modo di aggirarlo senza pagare un servizio proxy.
- **Glassdoor e ZipRecruiter non sono inclusi.** Sono stati provati: rispondono
  "403 Forbidden" a ogni richiesta senza un proxy a pagamento. Meglio non
  includerli che farti aspettare per niente.
- **Indeed è interrogato solo su USA e UK**, dove ha dato risultati. Altrove
  non ha prodotto nulla di utile nei test.
- **Le ricerche sono in inglese.** È pensato per cercare all'estero: scrivi
  ruoli e competenze in inglese.
- **Lo stipendio quasi non c'è.** Poche bacheche lo dichiarano — nei test, 13
  annunci su 193. Quando c'è lo vedi, quando manca non c'è modo di saperlo
  senza aprire l'annuncio.
- **La verifica del remoto legge il testo, non capisce il contesto.** Un
  annuncio che dice "remote-first, but we meet in the office monthly" risulta
  "remote confermato". Il badge riduce il lavoro di lettura, non lo elimina.

---

## Come è fatto

Il lavoro di raccolta lo fa [JobSpy](https://github.com/speedyapply/JobSpy),
libreria open source che interroga le bacheche. Il resto — profilo, filtri,
verifica del remoto, pagina — è in `engine/`, un file per passaggio:

| File | Cosa fa |
|---|---|
| `ask.py` | Le domande iniziali |
| `profile.py` | I campi del profilo e la mappa delle regioni |
| `build_query.py` | Profilo → termini di ricerca e filtri |
| `search.py` | Interroga le bacheche, una regione alla volta |
| `filter.py` | Assegna la fascia a ogni annuncio |
| `verify_remote.py` | Apre gli annunci in linea e verifica remoto e competenze |
| `llm_dispatch.py` | Smista il campo "altro da sapere" |
| `render_dashboard.py` | Genera la pagina HTML |
| `run.py` | Mette tutto in fila |

Note tecniche e trappole incontrate costruendolo: [engine/README.md](engine/README.md).

---

## Licenza

MIT.
