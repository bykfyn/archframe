"""
Archframe pilot page generator.

WHAT THIS DOES:
  Builds one static, browse-only HTML page (docs/index.html) listing
  every production partner in data/production_partners.json - a real
  photo, name, craft/area tags, and a link straight to their own site.
  No search, no ask-box - at ~30 entries for this pilot, browsing is
  genuinely enough; building Formground's whole query-translation
  pipeline for a dataset this size would be solving a problem that
  doesn't exist yet.

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
  Sheerd.com per the ecosystem's own placeholder decision - see
  project memory). No search. No monetization. Production partners
  only - not architects.

RUN:
    python3 generate_pilot_page.py
"""

import html
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "production_partners.json"
OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "index.html"

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
  .wordmark { font-size: 15px; font-weight: 700; letter-spacing: -0.01em; margin: 0 0 28px; }
  h1 { font-size: 22px; font-weight: 600; margin: 0 0 10px; }
  .intro { font-size: 14px; color: var(--text-secondary); line-height: 1.6; max-width: 62ch; margin: 0 0 8px; }
  .pilot-note { font-size: 12px; color: var(--text-muted); margin: 0 0 36px; }
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
  .card-title { font-size: 14px; font-weight: 500; margin: 0 0 6px; color: var(--text-primary); }
  .card:hover .card-title { text-decoration: underline; }
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
    tags = "".join(f'<span class="tag">{html.escape(a)}</span>' for a in partner.get("areas", []))
    image = (
        f'<img src="{html.escape(partner["image_url"])}" alt="{name}" loading="lazy">'
        if partner.get("image_url")
        else '<span class="fallback">No photo yet</span>'
    )
    website = partner.get("website")
    tag_open = (
        f'<a class="card" href="{html.escape(website)}" target="_blank" rel="noopener noreferrer">'
        if website else '<div class="card no-link">'
    )
    tag_close = "</a>" if website else "</div>"
    return f"""
      {tag_open}
        <div class="card-image">{image}</div>
        <div class="card-body">
          <p class="card-title">{name}</p>
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
  <p class="wordmark">archframe</p>
  <h1>Production partners</h1>
  <p class="intro">
    Real workshops and fabricators — carpenters, metalworkers, upholsterers,
    material suppliers — for architects and designers commissioning custom
    work, or brands looking for production capacity. Every card links
    straight to the workshop's own site.
  </p>
  <p class="pilot-note">Early pilot — production partners only, {len(partners)} listed so far.</p>
  <div class="grid">{cards}
  </div>
  <p class="foot-note">Pilot concept. Not yet a finished product.</p>
</main>
</body>
</html>
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(page)
    print(f"Generated {OUTPUT_PATH} with {len(partners)} production partners.")


if __name__ == "__main__":
    generate()
