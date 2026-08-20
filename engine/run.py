"""Radar Remoto — cerca lavoro da remoto all'estero a partire da un profilo.

    python -m engine.run --profile mio-profilo.json

Produce due file accanto al profilo: `risultati.json` (i dati grezzi) e
`risultati.html` (la pagina da aprire nel browser).

Pipeline: profilo -> ricerca per regione esplicita -> filtro sul ruolo ->
verifica remoto e competenze sugli annunci in linea -> pagina HTML.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# Le console Windows usano cp1252 di default: senza questo gli accenti
# italiani escono come "�" e il programma sembra rotto appena scaricato.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

from .build_query import build_filters
from .filter import apply_filters
from .profile import ALL_REGIONS, Profile
from .render_dashboard import render
from .search import run_search
from .verify_remote import verify_remote_status


def search_for_profile(profile: Profile, hours_old: int = 720, verify: bool = True):
    filters = build_filters(profile)

    print(f"Cerco: {', '.join(profile.ruoli)}")
    print(f"Zone: {', '.join(profile.regions_resolved())}")
    print("Solo lavoro remoto. Attendere, ci vogliono alcuni minuti...\n")

    raw = run_search(profile, hours_old=hours_old)
    if raw.empty:
        return raw

    tiered = apply_filters(raw, profile, filters)

    if verify:
        in_linea = tiered[tiered["tier"] == "In linea"]
        resto = tiered[tiered["tier"] != "In linea"]
        if not in_linea.empty:
            print(f"Verifico il remoto reale su {len(in_linea)} annunci in linea...")
            in_linea = verify_remote_status(in_linea, domain_match=filters["domain_match"])
        tiered = pd.concat([in_linea, resto], ignore_index=True)

    return tiered


def _load_profile(path: str) -> Profile:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    try:
        return Profile(**data)
    except TypeError as e:
        raise SystemExit(
            f"Il profilo {path} ha campi non validi: {e}\n"
            "Campi ammessi: ruoli, competenze, livello, zone, esclusioni."
        )


def main():
    ap = argparse.ArgumentParser(description="Cerca lavoro da remoto all'estero.")
    ap.add_argument("--profile", help="riusa un profilo salvato invece di rispondere alle domande")
    ap.add_argument("--out", help="dove scrivere la pagina HTML (default: risultati.html)")
    ap.add_argument("--giorni", type=int, default=30, help="quanto indietro cercare, in giorni (default 30)")
    ap.add_argument("--no-verify", action="store_true",
                    help="salta la verifica del remoto reale: più veloce, ma il filtro remoto di LinkedIn non è affidabile")
    args = ap.parse_args()

    if args.profile:
        profile = _load_profile(args.profile)
        profile_path = Path(args.profile)
    else:
        from .ask import chiedi_profilo
        profile = chiedi_profilo()
        profile_path = Path("mio-profilo.json")
        profile_path.write_text(
            json.dumps({
                "ruoli": profile.ruoli, "competenze": profile.competenze,
                "livello": profile.livello, "zone": profile.zone,
                "esclusioni": profile.esclusioni,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nProfilo salvato in {profile_path.name} — per rilanciare senza ridigitare:")
        print(f"  python -m engine.run --profile {profile_path.name}\n")

    profile_dict = {
        "ruoli": profile.ruoli, "competenze": profile.competenze,
        "livello": profile.livello, "zone": profile.zone,
        "esclusioni": profile.esclusioni,
    }

    df = search_for_profile(profile, hours_old=args.giorni * 24, verify=not args.no_verify)

    if df.empty:
        print("\nNessun annuncio trovato. Prova ad allargare i ruoli o le zone geografiche.")
        return

    html_path = Path(args.out) if args.out else profile_path.with_name("risultati.html")
    json_path = html_path.with_suffix(".json")

    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    records = json.loads(df.to_json(orient="records", force_ascii=False))
    html_path.write_text(render(records, profile_dict), encoding="utf-8")

    counts = df["tier"].value_counts()
    in_linea_n = int(counts.get("In linea", 0))
    print(f"\n{len(df)} annunci raccolti:")
    for tier in ("In linea", "Generico", "Fuori target"):
        if tier in counts:
            print(f"  {counts[tier]:>4}  {tier}")

    if in_linea_n < 5:
        print("\nPochi annunci in linea. Cosa puoi provare, nell'ordine:")
        if len(profile.ruoli) < 3:
            print(f"  - aggiungi varianti del ruolo (ora ne hai {len(profile.ruoli)}):")
            print("    ogni azienda scrive il titolo a modo suo")
        if len(profile.regions_resolved()) < len(ALL_REGIONS):
            print("  - allarga le zone geografiche")
        if args.giorni <= 30:
            print(f"  - allarga la finestra: --giorni {args.giorni * 2}")
        if int(counts.get("Fuori target", 0)) > in_linea_n:
            print("  - controlla livello ed esclusioni: stanno scartando parecchio")
        print("  - guarda comunque la fascia 'Generico' nella pagina: a volte c'è del buono")

    if "remote_status" in df.columns:
        confermati = int((df["remote_status"] == "remote confermato").sum())
        sospetti = int((df["remote_status"] == "SOSPETTO on-site/hybrid").sum())
        if sospetti:
            plurale = "annunci nominano" if sospetti > 1 else "annuncio nomina"
            print(f"\nAttenzione: {sospetti} {plurale} ufficio o ibrido")
            print(f"nonostante il filtro remoto. Solo {confermati} confermano il remoto nel testo.")
            print("Usa il filtro \"Verifica remoto\" nella pagina.")

    print(f"\nApri questo file nel browser:\n  {html_path.resolve()}")
    print(f"Dati grezzi: {json_path.name}")


if __name__ == "__main__":
    main()
