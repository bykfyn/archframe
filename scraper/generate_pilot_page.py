"""
Archframe pilot page generator.

WHAT THIS DOES:
  Builds one static HTML page (docs/index.html) listing every
  production partner in data/production_partners.json - a real photo,
  name, country, craft/area tags, and a link straight to their own
  site. A plain client-side substring filter (name/area/country, no
  backend, no query parsing) narrows the grid as you type - no ask-box;
  building Formground's whole query-translation pipeline for a dataset
  this size would be solving a problem that doesn't exist yet.

WHY THIS LOOKS LIKE FORMGROUND, BUT ISN'T FORMGROUND'S CODE:
  The card format (image, title, body) deliberately echoes Formground's
  own proven pattern - same instinct, not a shared codebase. This is a
  new, standalone pilot, not merged into Coreframe/Formground's repo,
  per the explicit decision not to touch a live, working product's
  code for an unproven one. If this pilot validates the concept, a
  real shared component only gets extracted once there are two real
  examples to generalize from, not one guess.

STATUS:
  Pilot only. No name/domain finalized yet (temporarily hosted at
  Sheerd.world per the ecosystem's own placeholder decision - see
  project memory). No monetization. Production partners only - not
  architects. English-only for now; a Swedish variant is deferred
  until a specific pitch to a Swedish association needs it.

RUN:
    python3 generate_pilot_page.py
"""

import html
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "production_partners.json"
OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "index.html"

# Interior Cluster's own area/craft vocabulary is Swedish; the pilot page
# is in English, so each of the 8 real values seen in the source data is
# translated for display. Untranslated values (a new category Interior
# Cluster adds later) fall back to the raw Swedish rather than being
# dropped, so a source change surfaces as an odd label, not a silent gap.
AREA_TRANSLATIONS = {
    "Beslag/komponenter": "Fittings & components",
    "Glas": "Glass",
    "Grossist": "Wholesaler",
    "Metall": "Metal",
    "Plast Beslag/komponenter": "Plastic fittings & components",
    "Textil/läder/klädsel": "Textile / leather / upholstery",
    "Trä (bearbetning)": "Wood (machining)",
    "Trä (material)": "Wood (material)",
}

PAGE_CSS = """
  :root {
    --bg: #faf9f7;
    --surface-1: #f1efec;
    --surface-2: #ffffff;
    --text-primary: #1c1b1a;
    --text-secondary: #57534e;
    --text-muted: #948d85;
    --text-accent: #4a6670;
    --border: #e4e0da;
    --border-strong: #c9c2b8;
    --radius: 10px;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  main { max-width: 1100px; margin: 0 auto; padding: 56px 20px 60px; }
  .header { text-align: center; margin: 0 0 36px; }
  .wordmark {
    font-size: 22px; font-weight: 500; letter-spacing: 0.22em;
    text-transform: uppercase; color: var(--text-primary); margin: 0;
  }
  .wordmark-rule { width: 40px; height: 1px; background: var(--border-strong); margin: 14px auto 0; }
  h1 { font-size: 22px; font-weight: 600; margin: 14px 0 10px; }
  .intro { font-size: 14px; color: var(--text-secondary); line-height: 1.6; max-width: 62ch; margin: 0 auto 8px; }
  .pilot-note { font-size: 12px; color: var(--text-muted); margin: 0 0 28px; }
  .search-wrap { max-width: 420px; margin: 0 auto 36px; }
  .search-input {
    width: 100%; font: inherit; font-size: 14px; color: var(--text-primary);
    background: var(--surface-2); border: 0.5px solid var(--border-strong);
    border-radius: 999px; padding: 10px 16px; outline: none;
  }
  .search-input::placeholder { color: var(--text-muted); }
  .search-input:focus { border-color: var(--text-accent); }
  .no-results {
    text-align: center; font-size: 13px; color: var(--text-muted);
    padding: 32px 0;
  }
  .grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 16px;
  }
  .card {
    background: var(--surface-2); border: 0.5px solid var(--border);
    border-radius: 12px; overflow: hidden; text-decoration: none; color: inherit;
    display: block;
  }
  .card.no-link { cursor: default; }
  .card-image {
    aspect-ratio: 4/3; background: var(--surface-1);
    display: flex; align-items: center; justify-content: center; overflow: hidden;
  }
  .card-image img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .card-image .fallback { font-size: 12px; color: var(--text-muted); }
  .card-body { padding: 12px 14px 14px; }
  .card-title { font-size: 14px; font-weight: 500; margin: 0 0 4px; color: var(--text-primary); }
  .card:hover .card-title { text-decoration: underline; }
  .card-meta { font-size: 11px; color: var(--text-muted); margin: 0 0 8px; }
  .card-tags { display: flex; flex-wrap: wrap; gap: 4px; }
  .tag {
    font-size: 10px; color: var(--text-secondary);
    border: 0.5px solid var(--border); border-radius: 999px; padding: 2px 8px;
  }
  .foot-note {
    font-size: 11px; color: var(--text-muted); margin-top: 48px; padding-top: 20px;
    border-top: 0.5px solid var(--border); line-height: 1.6;
  }
"""


def card_html(partner):
    name = html.escape(partner["name"])
    country = partner.get("country", "")
    translated_areas = [AREA_TRANSLATIONS.get(a, a) for a in partner.get("areas", [])]
    tags = "".join(f'<span class="tag">{html.escape(a)}</span>' for a in translated_areas)
    image = (
        f'<img src="{html.escape(partner["image_url"])}" alt="{name}" loading="lazy">'
        if partner.get("image_url")
        else '<span class="fallback">No photo yet</span>'
    )
    website = partner.get("website")
    search_text = html.escape(" ".join([partner["name"], country, *translated_areas]).lower())
    tag_open = (
        f'<a class="card" href="{html.escape(website)}" target="_blank" '
        f'rel="noopener noreferrer" data-search="{search_text}">'
        if website else f'<div class="card no-link" data-search="{search_text}">'
    )
    tag_close = "</a>" if website else "</div>"
    country_html = f'<p class="card-meta">{html.escape(country)}</p>' if country else ""
    return f"""
      {tag_open}
        <div class="card-image">{image}</div>
        <div class="card-body">
          <p class="card-title">{name}</p>
          {country_html}
          <div class="card-tags">{tags}</div>
        </div>
      {tag_close}"""


def generate():
    partners = json.loads(DATA_PATH.read_text())
    cards = "".join(card_html(p) for p in partners)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Archframe (pilot) — Production Partners</title>
<meta name="robots" content="noindex, follow">
<style>{PAGE_CSS}</style>
</head>
<body>
<main>
  <div class="header">
    <p class="wordmark">Archframe</p>
    <div class="wordmark-rule"></div>
    <h1>Production partners</h1>
    <p class="intro">
      Real workshops and fabricators — carpenters, metalworkers, upholsterers,
      material suppliers — for architects and designers commissioning custom
      work, or brands looking for production capacity. Every card links
      straight to the workshop's own site.
    </p>
    <p class="pilot-note">Early pilot — production partners only, {len(partners)} listed so far.</p>
    <div class="search-wrap">
      <input type="text" class="search-input" id="search" placeholder="Search by name, craft, or country" autocomplete="off">
    </div>
  </div>
  <div class="grid" id="grid">{cards}
  </div>
  <p class="no-results" id="no-results" hidden>No matches. Try a different search.</p>
  <p class="foot-note">Pilot concept. Not yet a finished product.</p>
</main>
<script>
  var input = document.getElementById("search");
  var cards = Array.prototype.slice.call(document.querySelectorAll("#grid .card"));
  var noResults = document.getElementById("no-results");
  input.addEventListener("input", function () {{
    var query = input.value.trim().toLowerCase();
    var anyVisible = false;
    cards.forEach(function (card) {{
      var match = (card.dataset.search || "").indexOf(query) !== -1;
      card.style.display = match ? "" : "none";
      if (match) anyVisible = true;
    }});
    noResults.hidden = anyVisible;
  }});
</script>
</body>
</html>
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(page)
    print(f"Generated {OUTPUT_PATH} with {len(partners)} production partners.")


if __name__ == "__main__":
    generate()
