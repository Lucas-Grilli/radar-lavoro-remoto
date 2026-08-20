"""Domande interattive — così non serve preparare nessun file a mano.

Chi lancia il programma senza `--profile` finisce qui: risponde a cinque
domande, il profilo viene salvato e la ricerca parte. Il file salvato serve
a rilanciare la stessa ricerca dopo, senza ripetere le domande.
"""

from .profile import ALL_REGIONS, LEVELS, Profile


def _lista(prompt: str, obbligatorio: bool = False) -> list[str]:
    while True:
        raw = input(prompt).strip()
        valori = [v.strip() for v in raw.split(",") if v.strip()]
        if valori or not obbligatorio:
            return valori
        print("  Serve almeno una risposta.\n")


def _livello() -> str:
    print("\nChe livello cerchi?")
    for i, lvl in enumerate(LEVELS, 1):
        print(f"  {i}. {lvl}")
    raw = input("Numero (invio = qualsiasi): ").strip()
    if not raw:
        return "qualsiasi"
    try:
        return LEVELS[int(raw) - 1]
    except (ValueError, IndexError):
        print("  Non ho capito, uso 'qualsiasi'.")
        return "qualsiasi"


def _zone() -> list[str]:
    print("\nDove cerchi? (puoi indicare più numeri separati da virgola)")
    for i, z in enumerate(ALL_REGIONS, 1):
        print(f"  {i}. {z}")
    print(f"  {len(ALL_REGIONS) + 1}. Tutto il mondo")
    while True:
        raw = input("Numeri (invio = tutto il mondo): ").strip()
        if not raw:
            return ["Tutto il mondo"]
        try:
            scelte = [int(n.strip()) for n in raw.split(",") if n.strip()]
            if any(n == len(ALL_REGIONS) + 1 for n in scelte):
                return ["Tutto il mondo"]
            zone = [ALL_REGIONS[n - 1] for n in scelte]
            if zone:
                return zone
        except (ValueError, IndexError):
            pass
        print("  Non ho capito. Scrivi i numeri separati da virgola, es: 1,3\n")


def chiedi_profilo() -> Profile:
    print("=" * 66)
    print("  RADAR REMOTO — cerca lavoro da remoto all'estero")
    print("=" * 66)
    print("\nCinque domande e parte la ricerca.")
    print("Scrivi ruoli e competenze IN INGLESE: le bacheche estere sono in inglese.\n")

    print("Un annuncio è \"in linea\" se uno di questi titoli compare nel suo titolo.")
    print("Scrivine 2-4 varianti corte: i titoli lunghi non li usa quasi nessuno.")
    ruoli = _lista(
        "\n1. Che ruoli cerchi? (separati da virgola)\n"
        "   es: Backend Developer, Backend Engineer, Node.js Developer\n"
        "   > ",
        obbligatorio=True,
    )
    if len(ruoli) == 1:
        print("\n   Ne hai messo uno solo: rischi di vedere pochi annunci, perché ogni")
        print("   azienda scrive il titolo a modo suo.")
        extra = _lista("   Altre varianti? (invio per tenere solo questo)\n   > ")
        ruoli.extend(extra)

    competenze = _lista(
        "\n2. Le tue competenze/tecnologie? (invio per saltare)\n"
        "   es: JavaScript, Node.js, PostgreSQL\n"
        "   > "
    )

    livello = _livello()
    zone = _zone()

    esclusioni = _lista(
        "\n4. Qualcosa da escludere? (invio per saltare)\n"
        "   es: blockchain, crypto\n"
        "   > "
    )

    altro = input(
        "\n5. Altro che dovrei sapere? (in italiano, invio per saltare)\n"
        "   es: preferirei evitare le grandi aziende\n"
        "   > "
    ).strip()

    return Profile(
        ruoli=ruoli,
        competenze=competenze,
        livello=livello,
        zone=zone,
        esclusioni=esclusioni,
        altro=altro,
    )
