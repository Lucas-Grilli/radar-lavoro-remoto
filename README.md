<h1 align="center">Radar Lavoro Remoto</h1>

<p align="center">
  <strong>Cerca lavoro da remoto all'estero, e verifica quali annunci lo sono davvero.</strong><br>
  Per chi vive in Italia e vuole un impiego fuori dal paese senza trasferirsi: raccoglie gli annunci da più bacheche insieme, li filtra sul ruolo che cerchi, e apre ogni annuncio buono per controllare se il "remoto" dichiarato è vero.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563eb.svg" alt="Licenza MIT"></a>
  <img src="https://img.shields.io/badge/status-v0.2-2563eb.svg" alt="v0.2">
</p>

<p align="center">
  <a href="#per-chi-è">Per chi è</a> ·
  <a href="#come-funziona">Come funziona</a> ·
  <a href="#come-si-usa">Come si usa</a> ·
  <a href="#limiti">Limiti</a> ·
  <a href="#come-è-fatto">Come è fatto</a>
</p>

Cercare lavoro remoto all'estero oggi vuol dire aprire più bacheche, ripetere la stessa ricerca su ognuna, e leggere centinaia di annunci per scoprire alla fine che molti non c'entrano col ruolo cercato — o non sono davvero remoti come dichiarano.

---

## Per chi è

È per te, se:

- Vivi in Italia e cerchi un lavoro da remoto in un'azienda straniera.
- Sei a tuo agio ad aprire un terminale e lanciare due comandi — non è un sito con un bottone.
- Preferisci una pagina tua con tutti gli annunci, invece di quattro schede diverse del browser.

Se cerchi lavoro in Italia, o preferisci uno strumento senza installare niente, oggi non è lo strumento giusto per te.

---

## Come funziona

Quattro domande — che ruoli cerchi, dove, che competenze, che livello — poi il programma:

1. **Cerca su LinkedIn e Indeed, regione per regione.** Mai una ricerca "in tutto il mondo" generica: su LinkedIn restituisce un insieme di annunci quasi separato da quello che si ottiene cercando regione per regione — verificato, 2 annunci in comune su 190 tra i due approcci.
2. **Filtra sul ruolo che hai scritto, cercato nel titolo.** Non per parola sciolta: cercare "formatore AI" pesca anche medici e ingegneri ML, perché "formatore" e "AI" matchano da soli. Qui serve il ruolo intero.
3. **Apre ogni annuncio pertinente e ne legge il testo**, per dire se è davvero remoto. Il filtro "solo remoto" delle bacheche non è affidabile — verificato, con quel filtro attivo solo 12 annunci su 72 confermavano il remoto nel testo dell'annuncio.
4. **Scrive una pagina HTML** con tutto, filtrabile per pertinenza, regione, bacheca e stato di verifica.

---

## Come si usa

Serve **Python 3.10 o superiore**. Due comandi:

```bash
pip install -r requirements.txt
python -m engine.run
```

Il programma fa le domande, poi parte. A fine ricerca dice quale file aprire nel browser.

Non serve preparare nessun file: le risposte vengono salvate in `mio-profilo.json`, così la volta dopo si può rilanciare la stessa ricerca senza ridigitare nulla:

```bash
python -m engine.run --profile mio-profilo.json
```

La ricerca richiede qualche minuto: interroga più bacheche, poi apre uno per uno gli annunci migliori per verificare il remoto. È lenta di proposito — fa le pause necessarie a non farsi bloccare.

### Opzioni

| Opzione | Cosa fa |
|---|---|
| `--giorni 7` | Cerca solo negli ultimi 7 giorni (default: 30) |
| `--profile file.json` | Riusa un profilo salvato invece di rispondere alle domande |
| `--out pagina.html` | Sceglie dove scrivere la pagina |
| `--no-verify` | Salta la verifica del remoto: molto più veloce, ma non si sa quali annunci sono davvero remoti |

### I campi del profilo

| Campo | Obbligatorio | Cosa farne |
|---|---|---|
| `ruoli` | **Sì** | I titoli da cercare, **in inglese** (le bacheche estere sono in inglese). L'unico campo che decide se un annuncio è "in linea". |
| `zone` | **Sì** | Dove cercare: `USA`, `Canada`, `UK & Irlanda`, `Europa`, `Asia-Pacifico`, oppure `Tutto il mondo` per tutte insieme. |
| `competenze` | No | Strumenti/tecnologie. Non escludono nessun annuncio: marcano quelli che le nominano davvero, come conferma in più. |
| `livello` | No | `junior`, `mid`, `senior` o `qualsiasi` (default). Scarta gli annunci che dichiarano un livello diverso; quelli che non lo dichiarano restano. |
| `esclusioni` | No | Parole che, se compaiono nel titolo, scartano l'annuncio. |

### Come leggere i risultati

Ogni annuncio finisce in una di tre fasce:

- **In linea** — il ruolo cercato è nel titolo. Sono questi da guardare, ed è la vista che si apre di default.
- **Generico** — pescato dalla ricerca ma il titolo non corrisponde al ruolo. Ogni tanto c'è qualcosa di buono.
- **Fuori target** — scartato da un'esclusione o dal livello.

Sugli annunci "in linea":

| Etichetta | Significato |
|---|---|
| `remote confermato` | L'annuncio dice esplicitamente che è remoto |
| `SOSPETTO on-site/hybrid` | Nomina ufficio o ibrido: probabilmente non è remoto nonostante il filtro |
| `ambiguo` | Il testo non lo dice in nessuna direzione — va aperto e letto |
| `competenze confermate` | Le competenze indicate compaiono nel testo dell'annuncio |

La pagina è un file HTML statico: funziona offline, si può salvare o mandare a qualcuno.

---

## Limiti

- **Le bacheche bloccano chi cerca troppo.** Ricerche ravvicinate fanno rifiutare le richieste da LinkedIn (errore 429). Non c'è modo di aggirarlo senza un servizio proxy a pagamento.
- **Glassdoor e ZipRecruiter non sono inclusi.** Provati: rispondono "403 Forbidden" a ogni richiesta senza un proxy a pagamento.
- **Indeed è interrogato solo su USA e UK**, le uniche zone dove ha dato risultati utili.
- **Le ricerche sono in inglese.** È pensato per cercare all'estero: ruoli e competenze vanno scritti in inglese.
- **Lo stipendio compare raramente.** Poche bacheche lo dichiarano. Quando manca, non c'è modo di saperlo senza aprire l'annuncio.
- **La verifica del remoto legge il testo, non capisce il contesto.** Un annuncio che dice "remote-first, but we meet in the office monthly" risulta "remote confermato". Il badge riduce il lavoro di lettura, non lo elimina.

---

## Come è fatto

Il lavoro di raccolta lo fa [JobSpy](https://github.com/speedyapply/JobSpy), libreria open source che interroga le bacheche. Il resto — profilo, filtri, verifica del remoto, pagina — è in `engine/`, un file per passaggio:

| File | Cosa fa |
|---|---|
| `ask.py` | Le domande iniziali |
| `profile.py` | I campi del profilo e la mappa delle regioni |
| `build_query.py` | Profilo → termini di ricerca e filtri |
| `search.py` | Interroga le bacheche, una regione alla volta |
| `filter.py` | Assegna la fascia a ogni annuncio |
| `verify_remote.py` | Apre gli annunci in linea e verifica remoto e competenze |
| `render_dashboard.py` | Genera la pagina HTML |
| `run.py` | Mette tutto in fila |

Note tecniche e trappole incontrate costruendolo: [engine/README.md](engine/README.md).

---

## Sviluppi futuri

Idee in valutazione, non promesse:

- Glassdoor e ZipRecruiter dietro un servizio proxy, se il costo si giustifica con l'uso reale.
- Una versione online, se lo scraping regge da un IP non residenziale — da verificare, oggi non testato.

---

## Licenza

MIT.
