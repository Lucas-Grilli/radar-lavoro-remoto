"""Genera la pagina risultati (dashboard.html) dall'output di run.py.

    python -m engine.render_dashboard --data risultati.json --profile profilo.json --out dashboard.html

Stesso design validato nell'Artifact del 19/08, reso generico: conteggi e
testo si calcolano dai dati veri, non più scritti a mano per il caso di
chi l'ha costruito.
"""

import argparse
import json
import re


def _fmt_salary(row) -> str | None:
    mn, mx = row.get("min_amount"), row.get("max_amount")
    if mn is None and mx is None:
        return None
    cur = row.get("currency") or ""
    interval = {"yearly": "/anno", "monthly": "/mese", "hourly": "/ora",
                "weekly": "/sett", "daily": "/g"}.get(row.get("interval"), "")

    def fmt_n(v):
        if v is None:
            return None
        v = int(v)
        return f"{v/1000:.0f}k" if v >= 1000 else str(v)

    a, b = fmt_n(mn), fmt_n(mx)
    core = f"{a}–{b}" if a and b and a != b else (a or b)
    return f"{cur} {core}{interval}".strip()


def _strip_md(t):
    if not t:
        return None
    t = re.sub(r"\*\*|\*|__|_", "", t)
    t = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


def _snippet(t, n=220):
    t = _strip_md(t)
    if not t:
        return None
    return (t[:n].rsplit(" ", 1)[0] + "…") if len(t) > n else t


def prepare_records(data: list[dict]) -> list[dict]:
    """Riduce le righe grezze del motore ai campi che servono alla pagina."""
    out = []
    for r in data:
        out.append({
            "tier": r.get("tier"),
            "site": r.get("site"),
            "title": r.get("title"),
            "company": r.get("company"),
            "location": r.get("location"),
            "region": r.get("region"),
            "job_url": r.get("job_url"),
            "remote_status": r.get("remote_status"),
            "competenze_confermate": r.get("competenze_confermate"),
            "date_posted": r.get("date_posted"),
            "salary_fmt": _fmt_salary(r),
            "desc_snippet": r.get("desc_snippet") or _snippet(r.get("description")),
        })
    return out


def render(data: list[dict], profile: dict) -> str:
    records = prepare_records(data)
    total = len(records)
    by_tier = {"In linea": 0, "Generico": 0, "Fuori target": 0}
    for r in records:
        by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1

    in_linea = [r for r in records if r["tier"] == "In linea"]
    verified = [r for r in in_linea if r.get("remote_status")]
    has_competenze = profile.get("competenze")

    ruoli_txt = ", ".join(profile.get("ruoli", []))
    zone_txt = ", ".join(profile.get("zone", []))
    subtitle = (
        f"{total} annunci raccolti su LinkedIn e Indeed per <b>{ruoli_txt}</b>, "
        f"zone: {zone_txt}. Solo lavoro remoto, ricerca in inglese."
    )

    alert_html = ""
    if verified:
        confermati = sum(1 for r in verified if r["remote_status"] == "remote confermato")
        sospetti = sum(1 for r in verified if r["remote_status"] == "SOSPETTO on-site/hybrid")
        alert_html = f"""<div class="alert">
    <span class="dot"></span>
    <span><b>Il filtro "remoto" di LinkedIn non è affidabile.</b> Sui {len(verified)} annunci "in linea" verificati: {confermati} confermano il remoto nella descrizione, {sospetti} nominano on-site/hybrid nonostante il filtro. Usa il filtro "Verifica remoto" prima di aprire un annuncio.</span>
  </div>"""

    regions = sorted({r["region"] for r in records if r.get("region")})
    region_chips_html = "\n".join(
        f'<button class="chip" data-region="{r}" aria-pressed="true">{r}</button>' for r in regions
    )

    sites = sorted({r["site"] for r in records if r.get("site")})
    site_chips_html = "\n".join(
        f'<button class="chip" data-site="{s}" aria-pressed="true">{s}</button>' for s in sites
    )

    remote_status_present = any(r.get("remote_status") for r in records)
    remote_labels = {
        "remote confermato": ("Confermato remoto", "-ok"),
        "ambiguo": ("Ambiguo", "-warn"),
        "SOSPETTO on-site/hybrid": ("Sospetto on-site", "-bad"),
        "non verificato": ("Non verificato", ""),
    }
    remote_chips_html = "\n".join(
        f'<button class="chip {cls}" data-remote="{key}" aria-pressed="true">{label}</button>'
        for key, (label, cls) in remote_labels.items()
    )

    data_json = json.dumps(records, ensure_ascii=False)
    profile_note = (
        f'Competenze richieste: <span class="mono">{", ".join(profile.get("competenze", []))}</span> — '
        '"competenze confermate" è calcolato sulla descrizione reale, non sul titolo.'
        if has_competenze else
        "Nessuna competenza specifica richiesta: il tier si basa solo sul ruolo."
    )

    return HTML_TEMPLATE.format(
        subtitle=subtitle,
        alert_html=alert_html,
        total=total,
        in_linea=by_tier.get("In linea", 0),
        generico=by_tier.get("Generico", 0),
        fuori=by_tier.get("Fuori target", 0),
        profile_note=profile_note,
        region_chips_html=region_chips_html,
        site_chips_html=site_chips_html,
        remote_filter_html=(
            f'<div class="controls" style="margin-top:-8px;">\n'
            f'    <span class="filter-label">Verifica remoto</span>\n'
            f'    <div class="chip-group" id="remoteChips">\n{remote_chips_html}\n    </div>\n  </div>'
            if remote_status_present else ""
        ),
        data_json=data_json,
    )


HTML_TEMPLATE = """<meta charset="utf-8">
<title>Radar Lavoro Remoto</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{{
    --bg: #EEF0F4; --surface: #FFFFFF; --surface-2: #E4E7EE; --surface-3: #DADEE7;
    --ink: #161A24; --ink-muted: #5B6274; --ink-faint: #868DA0; --border: #D7DBE4;
    --accent: #B5701C; --accent-ink: #FFFFFF;
    --tier-in: #147A5F; --tier-in-bg: #DCF0E9;
    --tier-generic: #6B7184; --tier-generic-bg: #E7E9EF;
    --tier-out: #A8442F; --tier-out-bg: #F5E3DE;
    --warn: #97650B; --warn-bg: #F3E6C9;
    --shadow: 0 1px 2px rgba(22,26,36,.04), 0 8px 24px -12px rgba(22,26,36,.12);
  }}
  @media (prefers-color-scheme: dark){{
    :root:not([data-theme="light"]){{
      --bg: #12151E; --surface: #191D28; --surface-2: #20242F; --surface-3: #282D3B;
      --ink: #E7E9F0; --ink-muted: #9AA0B4; --ink-faint: #6D7387; --border: #2B303D;
      --accent: #E0973A; --accent-ink: #171205;
      --tier-in: #49C39B; --tier-in-bg: #163229;
      --tier-generic: #9096A8; --tier-generic-bg: #23273240;
      --tier-out: #E08A75; --tier-out-bg: #33201B;
      --warn: #E3B25C; --warn-bg: #332707;
      --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px -12px rgba(0,0,0,.5);
    }}
  }}
  :root[data-theme="dark"]{{
    --bg: #12151E; --surface: #191D28; --surface-2: #20242F; --surface-3: #282D3B;
    --ink: #E7E9F0; --ink-muted: #9AA0B4; --ink-faint: #6D7387; --border: #2B303D;
    --accent: #E0973A; --accent-ink: #171205;
    --tier-in: #49C39B; --tier-in-bg: #163229;
    --tier-generic: #9096A8; --tier-generic-bg: #23273240;
    --tier-out: #E08A75; --tier-out-bg: #33201B;
    --warn: #E3B25C; --warn-bg: #332707;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px -12px rgba(0,0,0,.5);
  }}
  *{{box-sizing:border-box;}}
  html,body{{margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--ink);font-family:"Archivo",ui-sans-serif,system-ui,sans-serif;font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased;}}
  .mono{{font-family:"IBM Plex Mono",ui-monospace,monospace;}}
  .wrap{{max-width:1040px;margin:0 auto;padding:40px 24px 80px;}}
  .eyebrow{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:600;display:flex;align-items:center;gap:8px;}}
  .eyebrow::before{{content:"";width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb, var(--accent) 25%, transparent);}}
  h1{{font-size:clamp(28px,4vw,38px);font-weight:800;letter-spacing:-.01em;margin:10px 0 8px;text-wrap:balance;}}
  .subtitle{{color:var(--ink-muted);font-size:15px;max-width:68ch;margin:0 0 20px;}}
  .subtitle b{{color:var(--ink);font-weight:600;}}
  .profile-note{{color:var(--ink-faint);font-size:12.5px;margin:0 0 24px;}}
  .alert{{display:flex;gap:12px;align-items:flex-start;background:var(--warn-bg);border:1px solid color-mix(in srgb, var(--warn) 35%, transparent);border-radius:12px;padding:14px 16px;margin-bottom:24px;font-size:13.5px;color:var(--ink);}}
  .alert .dot{{width:8px;height:8px;border-radius:50%;background:var(--warn);flex:none;margin-top:6px;}}
  .alert b{{color:var(--warn);}}
  .stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:14px;overflow:hidden;margin-bottom:20px;}}
  .stat{{background:var(--surface);padding:18px 20px;}}
  .stat .n{{font-family:"IBM Plex Mono",monospace;font-size:28px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1;}}
  .stat .l{{color:var(--ink-muted);font-size:12.5px;margin-top:4px;text-transform:uppercase;letter-spacing:.04em;}}
  .stat.-in .n{{color:var(--tier-in);}} .stat.-generic .n{{color:var(--tier-generic);}} .stat.-out .n{{color:var(--tier-out);}}
  .controls{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:12px;position:sticky;top:0;padding:14px 0;background:linear-gradient(var(--bg) 70%, transparent);z-index:5;}}
  .filter-label{{font-family:"IBM Plex Mono",monospace;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-faint);margin:2px 8px 6px 0;width:100%;}}
  .chip-group{{display:flex;gap:6px;flex-wrap:wrap;align-items:center;}}
  .chip{{font-family:"IBM Plex Mono",monospace;font-size:12.5px;padding:7px 12px;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--ink-muted);cursor:pointer;user-select:none;transition:border-color .12s,color .12s,background .12s;white-space:nowrap;}}
  .chip:hover{{border-color:var(--ink-faint);}}
  .chip[aria-pressed="true"]{{background:var(--ink);color:var(--bg);border-color:var(--ink);}}
  .chip.-in[aria-pressed="true"]{{background:var(--tier-in);border-color:var(--tier-in);color:#fff;}}
  .chip.-generic[aria-pressed="true"]{{background:var(--tier-generic);border-color:var(--tier-generic);color:#fff;}}
  .chip.-out[aria-pressed="true"]{{background:var(--tier-out);border-color:var(--tier-out);color:#fff;}}
  .chip.-ok[aria-pressed="true"]{{background:var(--tier-in);border-color:var(--tier-in);color:#fff;}}
  .chip.-warn[aria-pressed="true"]{{background:var(--warn);border-color:var(--warn);color:#fff;}}
  .chip.-bad[aria-pressed="true"]{{background:var(--tier-out);border-color:var(--tier-out);color:#fff;}}
  .search{{position:relative;margin-left:auto;}}
  .search input{{font-family:"Archivo",sans-serif;font-size:13.5px;padding:8px 14px 8px 32px;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--ink);width:220px;outline:none;transition:border-color .12s,width .15s;}}
  .search input:focus{{border-color:var(--accent);width:260px;}}
  .search input::placeholder{{color:var(--ink-faint);}}
  .search::before{{content:"";position:absolute;left:12px;top:50%;translate:0 -50%;width:12px;height:12px;border:1.5px solid var(--ink-faint);border-radius:50%;}}
  .search::after{{content:"";position:absolute;left:20px;top:63%;width:6px;height:1.5px;background:var(--ink-faint);rotate:45deg;transform-origin:left;}}
  .count-line{{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--ink-faint);margin:2px 0 16px;}}
  .list{{display:flex;flex-direction:column;gap:8px;}}
  .card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:16px;box-shadow:var(--shadow);animation:rise .25s ease backwards;}}
  @keyframes rise{{from{{opacity:0;transform:translateY(4px);}}to{{opacity:1;transform:none;}}}}
  @media (prefers-reduced-motion: reduce){{ .card{{animation:none;}} }}
  .tier-dot{{width:9px;height:9px;border-radius:50%;background:var(--tier-generic);flex:none;align-self:start;margin-top:6px;}}
  .card.-in .tier-dot{{background:var(--tier-in);}} .card.-out .tier-dot{{background:var(--tier-out);}}
  .card-main .role{{font-weight:600;font-size:15px;margin-bottom:3px;text-wrap:balance;}}
  .card-main .meta{{font-size:13px;color:var(--ink-muted);display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;}}
  .card-main .snippet{{font-size:12.5px;color:var(--ink-faint);margin-top:7px;line-height:1.5;max-width:72ch;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}}
  .tag{{font-family:"IBM Plex Mono",monospace;font-size:11px;padding:2px 7px;border-radius:5px;background:var(--surface-2);color:var(--ink-muted);text-transform:uppercase;letter-spacing:.03em;}}
  .tag.-plain{{text-transform:none;letter-spacing:0;}}
  .pill{{font-family:"IBM Plex Mono",monospace;font-size:11px;padding:2px 7px;border-radius:5px;text-transform:uppercase;letter-spacing:.03em;font-weight:600;}}
  .pill.-in{{background:var(--tier-in-bg);color:var(--tier-in);}} .pill.-generic{{background:var(--tier-generic-bg);color:var(--tier-generic);}} .pill.-out{{background:var(--tier-out-bg);color:var(--tier-out);}}
  .pill.-ok{{background:var(--tier-in-bg);color:var(--tier-in);}} .pill.-warn{{background:var(--warn-bg);color:var(--warn);}} .pill.-bad{{background:var(--tier-out-bg);color:var(--tier-out);}} .pill.-unk{{background:var(--surface-2);color:var(--ink-faint);}}
  .pill.-salary{{background:color-mix(in srgb, var(--accent) 16%, var(--surface));color:var(--accent);text-transform:none;letter-spacing:0;}}
  .card a.open{{font-family:"IBM Plex Mono",monospace;font-size:12.5px;font-weight:500;color:var(--accent);text-decoration:none;white-space:nowrap;padding:8px 14px;border-radius:8px;border:1px solid color-mix(in srgb, var(--accent) 40%, transparent);transition:background .12s,color .12s;align-self:start;}}
  .card a.open:hover, .card a.open:focus-visible{{background:var(--accent);color:var(--accent-ink);outline:none;}}
  .empty{{text-align:center;color:var(--ink-faint);padding:48px 0;font-size:14px;}}
  @media (max-width:640px){{ .stats{{grid-template-columns:repeat(2,1fr);}} .card{{grid-template-columns:1fr;}} .card .tier-dot{{display:none;}} .search{{margin-left:0;width:100%;}} .search input{{width:100%;}} }}
</style>
<div class="wrap">
  <div class="eyebrow">radar-lavoro-remoto</div>
  <h1>I tuoi risultati</h1>
  <p class="subtitle">{subtitle}</p>
  <p class="profile-note">{profile_note}</p>
  {alert_html}
  <div class="stats">
    <div class="stat"><div class="n mono">{total}</div><div class="l">Raccolti</div></div>
    <div class="stat -in"><div class="n mono">{in_linea}</div><div class="l">In linea</div></div>
    <div class="stat -generic"><div class="n mono">{generico}</div><div class="l">Generico</div></div>
    <div class="stat -out"><div class="n mono">{fuori}</div><div class="l">Fuori target</div></div>
  </div>
  <div class="controls">
    <span class="filter-label">Pertinenza</span>
    <div class="chip-group" id="tierChips">
      <button class="chip -in" data-tier="In linea" aria-pressed="true">In linea</button>
      <button class="chip -generic" data-tier="Generico" aria-pressed="false">Generico</button>
      <button class="chip -out" data-tier="Fuori target" aria-pressed="false">Fuori target</button>
      <button class="chip" data-tier="__all__" aria-pressed="false">Tutti</button>
    </div>
    <div class="search"><input type="text" id="searchInput" placeholder="Cerca ruolo o azienda…"></div>
  </div>
  {remote_filter_html}
  <div class="controls" style="margin-top:-8px;">
    <span class="filter-label">Regione</span>
    <div class="chip-group" id="regionChips">
      {region_chips_html}
    </div>
  </div>
  <div class="controls" style="margin-top:-8px;">
    <span class="filter-label">Bacheca</span>
    <div class="chip-group" id="siteChips">
      {site_chips_html}
    </div>
  </div>
  <p class="count-line" id="countLine"></p>
  <div class="list" id="list"></div>
  <div class="empty" id="emptyState" style="display:none;">Nessun annuncio corrisponde ai filtri.</div>
</div>
<script>
const DATA = {data_json};
function tierClass(t){{ return t === "In linea" ? "-in" : t === "Fuori target" ? "-out" : "-generic"; }}
const REMOTE_CLASS = {{"remote confermato":"-ok","ambiguo":"-warn","SOSPETTO on-site/hybrid":"-bad","non verificato":"-unk"}};
function remoteKey(d){{ return d.remote_status || "non verificato"; }}
function relDate(s){{
  if(!s) return null;
  const d = new Date(s);
  if(isNaN(d.getTime())) return null;
  const days = Math.floor((new Date() - d) / 86400000);
  if(days <= 0) return "oggi";
  if(days === 1) return "ieri";
  if(days < 30) return days + "g fa";
  return d.toLocaleDateString("it-IT", {{day:"numeric", month:"short"}});
}}
function escapeHtml(s){{ return String(s).replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c])); }}
let activeTier = "In linea", searchQuery = "";
const activeRegions = new Set(Array.from(document.querySelectorAll("#regionChips .chip")).map(c => c.dataset.region));
const activeSites = new Set(Array.from(document.querySelectorAll("#siteChips .chip")).map(c => c.dataset.site));
const remoteChipsEl = document.getElementById("remoteChips");
const activeRemote = remoteChipsEl
  ? new Set(Array.from(remoteChipsEl.querySelectorAll(".chip")).map(c => c.dataset.remote))
  : null;
function renderList(){{
  let rows = DATA;
  if(activeTier !== "__all__") rows = rows.filter(d => d.tier === activeTier);
  rows = rows.filter(d => activeRegions.has(d.region));
  rows = rows.filter(d => activeSites.has(d.site));
  if(activeRemote) rows = rows.filter(d => d.tier !== "In linea" || activeRemote.has(remoteKey(d)));
  if(searchQuery){{
    const q = searchQuery.toLowerCase();
    rows = rows.filter(d => (d.title||"").toLowerCase().includes(q) || (d.company||"").toLowerCase().includes(q));
  }}
  document.getElementById("countLine").textContent = rows.length + " annunci mostrati";
  const list = document.getElementById("list"), empty = document.getElementById("emptyState");
  if(rows.length === 0){{ list.innerHTML = ""; empty.style.display = "block"; return; }}
  empty.style.display = "none";
  list.innerHTML = rows.map((d,i) => {{
    const date = relDate(d.date_posted);
    return `<div class="card ${{tierClass(d.tier)}}" style="animation-delay:${{Math.min(i*14,300)}}ms">
      <span class="tier-dot"></span>
      <div class="card-main">
        <div class="role">${{escapeHtml(d.title || "—")}}</div>
        <div class="meta">
          <span>${{escapeHtml(d.company || "—")}}</span><span>·</span><span>${{escapeHtml(d.location || "—")}}</span>
          <span class="pill ${{tierClass(d.tier)}}">${{d.tier}}</span>
          ${{d.remote_status ? `<span class="pill ${{REMOTE_CLASS[d.remote_status]||'-unk'}}">${{d.remote_status}}</span>` : ""}}
          ${{d.competenze_confermate === true ? `<span class="pill -ok">competenze confermate</span>` : (d.competenze_confermate === false ? `<span class="pill -unk">competenze non confermate</span>` : "")}}
          ${{d.salary_fmt ? `<span class="pill -salary">${{escapeHtml(d.salary_fmt)}}</span>` : ""}}
          <span class="tag">${{d.site}}</span><span class="tag">${{d.region}}</span>
          ${{date ? `<span class="tag -plain">${{date}}</span>` : ""}}
        </div>
        ${{d.desc_snippet ? `<div class="snippet">${{escapeHtml(d.desc_snippet)}}</div>` : ""}}
      </div>
      <a class="open" href="${{d.job_url}}" target="_blank" rel="noopener noreferrer">Apri annuncio →</a>
    </div>`;
  }}).join("");
}}
document.getElementById("tierChips").addEventListener("click", (e) => {{
  const btn = e.target.closest(".chip"); if(!btn) return;
  activeTier = btn.dataset.tier;
  document.querySelectorAll("#tierChips .chip").forEach(c => c.setAttribute("aria-pressed", c === btn ? "true" : "false"));
  renderList();
}});
document.getElementById("searchInput").addEventListener("input", (e) => {{ searchQuery = e.target.value.trim(); renderList(); }});
document.getElementById("regionChips").addEventListener("click", (e) => {{
  const btn = e.target.closest(".chip"); if(!btn) return;
  const r = btn.dataset.region;
  if(activeRegions.has(r)){{ activeRegions.delete(r); btn.setAttribute("aria-pressed","false"); }}
  else {{ activeRegions.add(r); btn.setAttribute("aria-pressed","true"); }}
  renderList();
}});
document.getElementById("siteChips").addEventListener("click", (e) => {{
  const btn = e.target.closest(".chip"); if(!btn) return;
  const s = btn.dataset.site;
  if(activeSites.has(s)){{ activeSites.delete(s); btn.setAttribute("aria-pressed","false"); }}
  else {{ activeSites.add(s); btn.setAttribute("aria-pressed","true"); }}
  renderList();
}});
if(remoteChipsEl) remoteChipsEl.addEventListener("click", (e) => {{
  const btn = e.target.closest(".chip"); if(!btn) return;
  const r = btn.dataset.remote;
  if(activeRemote.has(r)){{ activeRemote.delete(r); btn.setAttribute("aria-pressed","false"); }}
  else {{ activeRemote.add(r); btn.setAttribute("aria-pressed","true"); }}
  renderList();
}});
renderList();
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)
    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)

    html = render(data, profile)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"scritto {args.out}")


if __name__ == "__main__":
    main()
