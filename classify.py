#!/usr/bin/env python3
"""Classify forum comments as acceptable / toxic / spam with Cloudflare's Clef model,
then write an easy-to-scan HTML page of the results.

Usage:
    python3 classify.py                       # comments.json  -> results.html     (clef-flash, v1 criteria)
    python3 classify.py --v2                  # comments-v2.json -> results-v2.html (clef, v2 criteria)
    python3 classify.py --html-only           # rebuild the HTML from saved results, no API calls

Credentials are read from cloud-flare.local.sh (never committed). Standard library only.
"""

import argparse
import html
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from criteria import CRITERIA

HERE = Path(__file__).resolve().parent
API = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/@cf/cloudflare/{model}"
LABELS = ["acceptable", "toxic", "spam"]
try:  # use certifi's CA bundle if installed (fixes python.org macOS builds)
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()
LOW_CONFIDENCE = 0.5  # answers below this are flagged for a closer human look


# ---------------------------------------------------------------- API --------

def load_credentials(path):
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        sys.exit(f"Missing {path}. Copy cloud-flare.sh to cloud-flare.local.sh and add your "
                 "account ID and API token.")
    creds = dict(re.findall(r'export (\w+)="([^"]*)"', text))
    account, token = creds.get("CLOUDFLARE_ACCOUNT_ID"), creds.get("CLOUDFLARE_API_TOKEN")
    if not account or not token or "your-cloudflare" in token or account.startswith("0123456789abcdef"):
        sys.exit(f"{path} still has the placeholder account ID or token.")
    return account, token


def build_payload(item, criteria_version):
    spec = CRITERIA[criteria_version]
    return {
        "state": {"comment": item["comment"], "thread": item.get("thread", "")},
        "questions": {
            "moderation": {
                "type": "choice",
                "instructions": spec["instructions"],
                "criteria": spec["criteria"],
            }
        },
    }


def classify_one(item, *, url, token, criteria_version, retries=6):
    body = json.dumps(build_payload(item, criteria_version)).encode("utf-8")
    delay = 2.0
    last_error = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            if e.code in (401, 403):
                sys.exit(f"HTTP {e.code}: bad account ID or token (needs Workers AI Read + Edit).\n{detail}")
            if e.code == 429 or e.code >= 500:
                last_error = f"HTTP {e.code}: {detail}"
                time.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"comment {item['id']}: HTTP {e.code} {detail}")
        except (urllib.error.URLError, TimeoutError) as e:
            reason = getattr(e, "reason", e)
            if isinstance(reason, ssl.SSLCertVerificationError):
                sys.exit("SSL certificate check failed. On macOS with python.org Python, run:\n"
                         '  open "/Applications/Python 3.13/Install Certificates.command"\n'
                         "then try again.")
            last_error = repr(reason)
            time.sleep(delay)
            delay *= 2
            continue
        if not data.get("success"):
            raise RuntimeError(f"comment {item['id']}: {data.get('errors')}")
        answer = data["result"]["answers"]["moderation"]
        return {**item,
                "label": answer["choice"],
                "probabilities": answer["probabilities"],
                "confidence": answer.get("confidence")}
    raise RuntimeError(f"comment {item['id']}: gave up after {retries} attempts. Last error: {last_error}")


def classify_all(comments, *, account, token, model, criteria_version, workers):
    url = API.format(account=account, model=model)
    done = 0

    def run(item):
        nonlocal done
        result = classify_one(item, url=url, token=token, criteria_version=criteria_version)
        done += 1
        print(f"\r  {done}/{len(comments)} classified", end="", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run, comments))
    print()
    return results


# ---------------------------------------------------------------- HTML -------

def render_html(results, *, title, model, criteria_version, source):
    counts = {l: sum(r["label"] == l for r in results) for l in LABELS}
    low = sum((r.get("confidence") or 0) < LOW_CONFIDENCE for r in results)
    page_key = Path(source).stem

    cards = []
    for r in results:
        conf = r.get("confidence") or 0.0
        probs = r.get("probabilities", {})
        bars = "".join(
            f'<div class="bar"><span class="bl">{l}</span>'
            f'<span class="track"><span class="fill {l}" style="width:{probs.get(l, 0) * 100:.1f}%"></span></span>'
            f'<span class="bv">{probs.get(l, 0):.2f}</span></div>'
            for l in LABELS)
        options = "".join(f'<option value="{l}">{l}</option>' for l in LABELS)
        cards.append(f"""
<article class="card {r['label']}{' low' if conf < LOW_CONFIDENCE else ''}" data-id="{r['id']}"
  data-label="{r['label']}" data-conf="{conf:.4f}" data-text="{html.escape((r['comment'] + ' ' + r.get('author', '')).lower())}">
  <header>
    <span class="id">#{r['id']}</span>
    <span class="badge {r['label']}">{r['label']}</span>
    <span class="conf" title="Clef confidence">conf {conf:.2f}{' · check' if conf < LOW_CONFIDENCE else ''}</span>
    <span class="meta">{html.escape(r.get('author', ''))} · {html.escape(r.get('thread', ''))} · {html.escape(r.get('posted_at', ''))}</span>
  </header>
  <p class="comment">{html.escape(r['comment'])}</p>
  <div class="bars">{bars}</div>
  <details class="review">
    <summary>Disagree with Clef?</summary>
    <label><input type="checkbox" class="flag"> Clef is wrong / borderline</label>
    <label>My label <select class="mine">{options}</select></label>
    <label><input type="checkbox" class="borderline"> borderline</label>
    <textarea class="why" placeholder="Why (1–2 sentences, in your own words)"></textarea>
  </details>
</article>""")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#f6f6f3;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;
  --ok:#2f7d4f;--ok-bg:#e6f3ea;--tox:#b3261e;--tox-bg:#fbe7e5;--spam:#a05a00;--spam-bg:#fdf0dc;--warn:#6a3fb5}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--card:#21211f;--ink:#ecebe6;--muted:#9a9993;--line:#34332f;
  --ok:#6fcf93;--ok-bg:#1d3326;--tox:#ff8a80;--tox-bg:#3a1f1d;--spam:#ffb74d;--spam-bg:#3a2c16;--warn:#b79cff}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}}
.wrap{{max-width:960px;margin:0 auto;padding:24px 16px 80px}}
h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);margin:0 0 16px}}
.stats{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 14px}}
.stat b{{font-size:20px;display:block}}
.controls{{position:sticky;top:0;z-index:2;background:var(--bg);padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center;border-bottom:1px solid var(--line);margin-bottom:14px}}
button,select,input[type=search]{{font:inherit;color:inherit;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 10px;cursor:pointer}}
button.on{{outline:2px solid var(--ink)}} input[type=search]{{flex:1;min-width:160px;cursor:text}}
.card{{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:10px}}
.card.acceptable{{border-left-color:var(--ok)}} .card.toxic{{border-left-color:var(--tox)}} .card.spam{{border-left-color:var(--spam)}}
.card.flagged{{box-shadow:0 0 0 2px var(--warn)}}
header{{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}}
.id{{font-weight:700;font-variant-numeric:tabular-nums}}
.badge{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;padding:2px 8px;border-radius:999px}}
.badge.acceptable{{color:var(--ok);background:var(--ok-bg)}} .badge.toxic{{color:var(--tox);background:var(--tox-bg)}} .badge.spam{{color:var(--spam);background:var(--spam-bg)}}
.conf{{font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}} .low .conf{{color:var(--warn);font-weight:700}}
.meta{{font-size:13px;color:var(--muted);margin-left:auto}}
.comment{{margin:8px 0;white-space:pre-wrap;overflow-wrap:anywhere}}
.bars{{display:grid;grid-template-columns:repeat(3,1fr);gap:4px 14px}}
.bar{{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted)}}
.bl{{width:68px}} .bv{{width:32px;text-align:right;font-variant-numeric:tabular-nums}}
.track{{flex:1;height:6px;background:var(--line);border-radius:3px;overflow:hidden}}
.fill{{display:block;height:100%}} .fill.acceptable{{background:var(--ok)}} .fill.toxic{{background:var(--tox)}} .fill.spam{{background:var(--spam)}}
.review{{margin-top:8px;font-size:14px}} .review summary{{cursor:pointer;color:var(--muted)}}
.review label{{margin-right:14px;display:inline-flex;gap:6px;align-items:center;margin-top:6px}}
.review textarea{{display:block;width:100%;min-height:52px;margin-top:6px;font:inherit;color:inherit;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 8px}}
@media (max-width:640px){{.bars{{grid-template-columns:1fr}} .meta{{margin-left:0;width:100%}}}}
</style></head><body><div class="wrap">
<h1>{html.escape(title)}</h1>
<p class="sub">{len(results)} comments from <code>{html.escape(source)}</code> · model <code>{html.escape(model)}</code> · criteria {html.escape(criteria_version)} · confidence &lt; {LOW_CONFIDENCE} marked <b style="color:var(--warn)">check</b></p>
<div class="stats">
  <div class="stat"><b style="color:var(--ok)">{counts['acceptable']}</b>acceptable</div>
  <div class="stat"><b style="color:var(--tox)">{counts['toxic']}</b>toxic</div>
  <div class="stat"><b style="color:var(--spam)">{counts['spam']}</b>spam</div>
  <div class="stat"><b style="color:var(--warn)">{low}</b>low confidence</div>
</div>
<div class="controls">
  <button data-f="all" class="on">All</button><button data-f="acceptable">Acceptable</button>
  <button data-f="toxic">Toxic</button><button data-f="spam">Spam</button>
  <button data-f="low">Low confidence</button><button data-f="flagged">My flags</button>
  <select id="sort"><option value="id">Sort: id</option><option value="conf">Sort: least confident first</option></select>
  <input type="search" id="q" placeholder="Search text or author">
  <button id="export" title="Copy your flags as Markdown">Export my flags</button>
</div>
<main id="list">{''.join(cards)}</main>
</div>
<script>
const KEY = "clef-review-{page_key}";
const list = document.getElementById("list");
const cards = [...list.querySelectorAll(".card")];
let filter = "all";
function load() {{ try {{ return JSON.parse(localStorage.getItem(KEY)) || {{}}; }} catch (e) {{ return {{}}; }} }}
function save(s) {{ try {{ localStorage.setItem(KEY, JSON.stringify(s)); }} catch (e) {{}} }}
const state = load();
cards.forEach(c => {{
  const id = c.dataset.id, s = state[id] || {{}};
  const f = c.querySelector(".flag"), m = c.querySelector(".mine"), b = c.querySelector(".borderline"), w = c.querySelector(".why");
  m.value = s.mine || c.dataset.label; f.checked = !!s.flag; b.checked = !!s.borderline; w.value = s.why || "";
  if (s.flag) {{ c.classList.add("flagged"); c.querySelector("details").open = true; }}
  const upd = () => {{ state[id] = {{flag: f.checked, mine: m.value, borderline: b.checked, why: w.value}};
    c.classList.toggle("flagged", f.checked); save(state); }};
  [f, m, b].forEach(el => el.addEventListener("change", upd)); w.addEventListener("input", upd);
  m.addEventListener("change", () => {{ if (m.value !== c.dataset.label) {{ f.checked = true; upd(); }} }});
}});
function apply() {{
  const q = document.getElementById("q").value.toLowerCase();
  cards.forEach(c => {{
    const ok = (filter === "all" || c.dataset.label === filter ||
      (filter === "low" && c.classList.contains("low")) || (filter === "flagged" && c.classList.contains("flagged")))
      && (!q || c.dataset.text.includes(q));
    c.style.display = ok ? "" : "none";
  }});
}}
document.querySelectorAll("[data-f]").forEach(b => b.addEventListener("click", () => {{
  document.querySelectorAll("[data-f]").forEach(x => x.classList.remove("on")); b.classList.add("on");
  filter = b.dataset.f; apply(); }}));
document.getElementById("q").addEventListener("input", apply);
document.getElementById("sort").addEventListener("change", e => {{
  const by = e.target.value;
  [...cards].sort((a, b) => by === "conf" ? a.dataset.conf - b.dataset.conf : a.dataset.id - b.dataset.id)
    .forEach(c => list.appendChild(c)); }});
document.getElementById("export").addEventListener("click", () => {{
  const rows = cards.filter(c => c.classList.contains("flagged")).map(c => {{
    const s = state[c.dataset.id] || {{}};
    return `## Comment ${{c.dataset.id}}${{s.borderline ? " (borderline)" : ""}}\\n\\n` +
      `- **Clef:** ${{c.dataset.label}}\\n- **Correct:** ${{s.mine}}\\n- **Why:** ${{(s.why || "").trim()}}\\n`; }});
  const md = rows.join("\\n");
  const done = () => alert(`Copied ${{rows.length}} entries as Markdown. Paste them into your MISTAKES file.`);
  if (navigator.clipboard) navigator.clipboard.writeText(md).then(done, () => prompt("Copy this:", md));
  else prompt("Copy this:", md);
}});
</script></body></html>
"""


# ---------------------------------------------------------------- main -------

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--v2", action="store_true", help="use comments-v2.json, model clef, criteria v2")
    p.add_argument("--input"); p.add_argument("--model"); p.add_argument("--criteria", choices=sorted(CRITERIA))
    p.add_argument("--html"); p.add_argument("--results")
    p.add_argument("--creds", default=str(HERE / "cloud-flare.local.sh"))
    p.add_argument("--workers", type=int, default=4, help="parallel requests (default 4)")
    p.add_argument("--html-only", action="store_true", help="rebuild HTML from the saved results JSON")
    a = p.parse_args()

    suffix = "-v2" if a.v2 else ""
    source = a.input or f"comments{suffix}.json"
    model = a.model or ("clef" if a.v2 else "clef-flash")
    criteria_version = a.criteria or ("v2" if a.v2 else "v1")
    html_path = Path(a.html or HERE / f"results{suffix}.html")
    results_path = Path(a.results or HERE / f"results{suffix}.json")

    if a.html_only:
        saved = json.loads(results_path.read_text())
        results, model, criteria_version = saved["results"], saved["model"], saved["criteria"]
    else:
        comments = json.loads((HERE / source).read_text())["comments"]
        account, token = load_credentials(a.creds)
        print(f"Classifying {len(comments)} comments from {source} with {model} (criteria {criteria_version})")
        results = classify_all(comments, account=account, token=token, model=model,
                               criteria_version=criteria_version, workers=a.workers)
        results_path.write_text(json.dumps({"source": source, "model": model, "criteria": criteria_version,
                                            "results": results}, indent=1, ensure_ascii=False))

    title = f"Clef moderation results{' (v2)' if a.v2 else ''}"
    html_path.write_text(render_html(results, title=title, model=model,
                                     criteria_version=criteria_version, source=source), encoding="utf-8")
    counts = {l: sum(r["label"] == l for r in results) for l in LABELS}
    print(f"Wrote {html_path.name} and {results_path.name}: {counts}")


if __name__ == "__main__":
    main()
