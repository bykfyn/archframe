"""
Archframe pilot site generator.

WHAT THIS DOES:
  Builds the static pilot site in docs/ from data/production_partners.json
  and data/associations.json:
    - docs/index.html - the main grid, name/craft/country filterable by a
      plain client-side substring search.
    - docs/partners/<slug>.html - one real profile page per production
      partner (photo, tags, which association(s) vouch for them, a link
      out to their own site).
    - docs/associations.html - an index of associations used as sources.
    - docs/associations/<slug>.html - one profile per association
      (description, own website, and the real "Associated" grid of its
      members - the same pattern found on sheerd.com's own brand/
      association profiles, e.g. Ughle <-> Interior Cluster Sweden).

WHY ASSOCIATIONS ARE MODELLED AS ENTITIES, NOT JUST A TEXT FIELD:
  Associations are lead-generation sources feeding one shared, deduplicated
  company directory - not one dataset per source. A production partner can
  belong to more than one association (`"associations": [...]` is a list),
  and that's a legitimacy signal, not a duplicate-data problem. This is
  also, concretely, a first working instance of Brandvue's actual thesis
  (one canonical company profile, not siloed per-association data) - see
  project memory ("Architecture pivot: associations as sources, not
  silos") before changing this shape.

WHY THIS LOOKS LIKE FORMGROUND, BUT ISN'T FORMGROUND'S CODE:
  The card format (image, title, body) deliberately echoes Formground's
  own proven pattern - same instinct, not a shared codebase. This is a
  new, standalone pilot, not merged into Coreframe/Formground's repo,
  per the explicit decision not to touch a live, working product's
  code for an unproven one. If this pilot validates the concept, a
  real shared component only gets extracted once there are two real
  examples to generalize from, not one guess.

STATUS:
  Pilot only. No name/domain finalized yet (hosted at sheerd.world per
  the ecosystem's own placeholder decision - see project memory). No
  monetization. Production partners only - not architects. English-only
  for now; a Swedish variant is deferred until a specific pitch to a
  Swedish association needs it. Single source (Interior Cluster) for
  now, deliberately - the associations/profile-pages architecture is
  being proven on one clean source before more (messier) sources are
  merged in.

RUN:
    python3 generate_pilot_page.py
"""

import html
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PARTNERS_PATH = DATA_DIR / "production_partners.json"
ASSOCIATIONS_PATH = DATA_DIR / "associations.json"
DOCS_DIR = Path(__file__).parent.parent / "docs"

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
  .wordmark a { color: inherit; text-decoration: none; }
  .wordmark-rule { width: 40px; height: 1px; background: var(--border-strong); margin: 14px auto 0; }
  .site-nav { font-size: 12px; color: var(--text-muted); margin: 14px 0 0; }
  .site-nav a { color: var(--text-secondary); text-decoration: none; }
  .site-nav a:hover { text-decoration: underline; }
  .site-nav .current { color: var(--text-primary); font-weight: 600; }
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

  /* --- profile pages (partner + association) --- */
  .back-link { display: inline-block; font-size: 12px; color: var(--text-secondary); text-decoration: none; margin: 0 0 28px; }
  .back-link:hover { text-decoration: underline; }
  .profile-image {
    aspect-ratio: 16/9; background: var(--surface-1); border-radius: 12px;
    overflow: hidden; display: flex; align-items: center; justify-content: center;
    margin: 0 0 24px;
  }
  .profile-image img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .profile-image .fallback { font-size: 13px; color: var(--text-muted); }
  .profile-title { font-size: 24px; font-weight: 600; margin: 0 0 6px; }
  .profile-meta { font-size: 13px; color: var(--text-muted); margin: 0 0 14px; }
  .profile-tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 24px; }
  .profile-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.6; max-width: 62ch; margin: 0 0 24px; }
  .member-of { font-size: 13px; color: var(--text-secondary); margin: 0 0 28px; }
  .member-of a { color: var(--text-accent); text-decoration: none; }
  .member-of a:hover { text-decoration: underline; }
  .btn {
    display: inline-block; font-size: 14px; font-weight: 500; color: var(--text-primary);
    background: var(--surface-2); border: 0.5px solid var(--border-strong);
    border-radius: 999px; padding: 10px 20px; text-decoration: none; margin: 0 0 36px;
  }
  .btn:hover { border-color: var(--text-accent); }
  .section-heading { font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin: 0 0 16px; }

  /* --- associations index: text-forward, not a photo card --- */
  /* An association's real content is its name/description/member count,
     not a photo the way a partner's workshop is - reusing the photo-card
     component here left a large empty "no image" box with nothing to
     fill it. Same border/radius/background language, different shape. */
  .assoc-list { display: flex; flex-direction: column; gap: 12px; }
  .assoc-row {
    display: block; background: var(--surface-2); border: 0.5px solid var(--border);
    border-radius: 12px; padding: 18px 20px; text-decoration: none; color: inherit;
  }
  .assoc-row:hover .assoc-name { text-decoration: underline; }
  .assoc-name { font-size: 15px; font-weight: 600; margin: 0 0 6px; color: var(--text-primary); }
  .assoc-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin: 0 0 8px; max-width: 62ch; }
  .assoc-count { font-size: 11px; color: var(--text-muted); margin: 0; }
"""


# Swedish letters have no ASCII equivalent that a plain regex strip would
# produce correctly - stripping them outright turns "Elmo Läder" into the
# unreadable slug "elmo-l-der" instead of "elmo-lader". 8 of 30 real
# partner names use at least one of these.
SWEDISH_TRANSLITERATION = str.maketrans("åäöÅÄÖ", "aaoAAO")


def slugify(name):
    slug = name.translate(SWEDISH_TRANSLITERATION).lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def load_data():
    partners = json.loads(PARTNERS_PATH.read_text())
    associations = json.loads(ASSOCIATIONS_PATH.read_text())
    for p in partners:
        p["slug"] = slugify(p["name"])
    for a in associations:
        a["slug"] = a["id"]
    return partners, associations


def page_shell(title, body, depth=0, robots="noindex, follow"):
    """depth is how many directories deep this page is under docs/, so
    relative links (style.css, index.html, partners/, associations/) work
    the same whether the page sits at docs/ or docs/partners/."""
    prefix = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="robots" content="{robots}">
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def site_nav(prefix, current):
    links = [
        ("Production partners", f"{prefix}index.html", "index"),
        ("Associations", f"{prefix}associations.html", "associations"),
    ]
    parts = []
    for label, href, key in links:
        if key == current:
            parts.append(f'<span class="current">{label}</span>')
        else:
            parts.append(f'<a href="{href}">{label}</a>')
    return '<p class="site-nav">' + " &middot; ".join(parts) + "</p>"


def header_html(prefix, current, heading, intro=""):
    return f"""
  <div class="header">
    <p class="wordmark"><a href="{prefix}index.html">Archframe</a></p>
    <div class="wordmark-rule"></div>
    {site_nav(prefix, current)}
    <h1>{heading}</h1>
    {f'<p class="intro">{intro}</p>' if intro else ""}
  </div>"""


def partner_card_html(partner, link_prefix=""):
    name = html.escape(partner["name"])
    country = partner.get("country", "")
    translated_areas = [AREA_TRANSLATIONS.get(a, a) for a in partner.get("areas", [])]
    tags = "".join(f'<span class="tag">{html.escape(a)}</span>' for a in translated_areas)
    image = (
        f'<img src="{html.escape(partner["image_url"])}" alt="{name}" loading="lazy">'
        if partner.get("image_url")
        else '<span class="fallback">No photo yet</span>'
    )
    search_text = html.escape(" ".join([partner["name"], country, *translated_areas]).lower())
    href = f'{link_prefix}partners/{partner["slug"]}.html'
    country_html = f'<p class="card-meta">{html.escape(country)}</p>' if country else ""
    return f"""
      <a class="card" href="{href}" data-search="{search_text}">
        <div class="card-image">{image}</div>
        <div class="card-body">
          <p class="card-title">{name}</p>
          {country_html}
          <div class="card-tags">{tags}</div>
        </div>
      </a>"""


def generate_index(partners, associations):
    cards = "".join(partner_card_html(p) for p in partners)
    body = header_html(
        "", "index", "Production partners",
        "Real workshops and fabricators — carpenters, metalworkers, upholsterers, "
        "material suppliers — for architects and designers commissioning custom "
        "work, or brands looking for production capacity. Each profile links "
        "straight to the workshop's own site.",
    ) + f"""
    <p class="pilot-note">Early pilot — production partners only, {len(partners)} listed so far.</p>
    <div class="search-wrap">
      <input type="text" class="search-input" id="search" placeholder="Search by name, craft, or country" autocomplete="off">
    </div>
  <div class="grid" id="grid">{cards}
  </div>
  <p class="no-results" id="no-results" hidden>No matches. Try a different search.</p>
  <p class="foot-note">Pilot concept. Not yet a finished product.</p>
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
</script>"""
    (DOCS_DIR / "index.html").write_text(page_shell("Archframe (pilot) — Production Partners", body))


def generate_partner_pages(partners, associations_by_id):
    out_dir = DOCS_DIR / "partners"
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in partners:
        name = html.escape(p["name"])
        country = p.get("country", "")
        translated_areas = [AREA_TRANSLATIONS.get(a, a) for a in p.get("areas", [])]
        tags = "".join(f'<span class="tag">{html.escape(a)}</span>' for a in translated_areas)
        image = (
            f'<img src="{html.escape(p["image_url"])}" alt="{name}">'
            if p.get("image_url")
            else '<span class="fallback">No photo yet</span>'
        )
        member_links = ", ".join(
            f'<a href="../associations/{associations_by_id[aid]["slug"]}.html">{html.escape(associations_by_id[aid]["name"])}</a>'
            for aid in p.get("associations", [])
            if aid in associations_by_id
        )
        member_of_html = (
            f'<p class="member-of">Member of: {member_links}</p>' if member_links else ""
        )
        website = p.get("website")
        website_html = (
            f'<a class="btn" href="{html.escape(website)}" target="_blank" rel="noopener noreferrer">Visit their website &rarr;</a>'
            if website else ""
        )
        body = f"""
  {header_html("../", "index", "")}
  <a class="back-link" href="../index.html">&larr; All production partners</a>
  <div class="profile-image">{image}</div>
  <h1 class="profile-title">{name}</h1>
  <p class="profile-meta">{html.escape(country)}</p>
  <div class="profile-tags">{tags}</div>
  {member_of_html}
  {website_html}
"""
        page = page_shell(f"{p['name']} — Archframe", body, depth=1)
        (out_dir / f"{p['slug']}.html").write_text(page)


def association_row_html(association, member_count):
    name = html.escape(association["name"])
    meta = f"{member_count} member{'s' if member_count != 1 else ''} listed here"
    return f"""
      <a class="assoc-row" href="associations/{association['slug']}.html">
        <p class="assoc-name">{name}</p>
        <p class="assoc-desc">{html.escape(association['description'])}</p>
        <p class="assoc-count">{meta}</p>
      </a>"""


def generate_associations_index(associations, partners):
    rows = "".join(
        association_row_html(a, sum(1 for p in partners if a["id"] in p.get("associations", [])))
        for a in associations
    )
    body = header_html(
        "", "associations", "Associations",
        "The real trade and craft associations whose public member data seeds this "
        "directory. Archframe doesn't replace an association's own membership "
        "criteria — it re-presents their members with real photos, search, and a "
        "shared profile that can span more than one association.",
    ) + f"""
  <div class="assoc-list">{rows}
  </div>
  <p class="foot-note">Pilot concept. Not yet a finished product.</p>"""
    (DOCS_DIR / "associations.html").write_text(page_shell("Associations — Archframe", body))


def generate_association_pages(associations, partners):
    out_dir = DOCS_DIR / "associations"
    out_dir.mkdir(parents=True, exist_ok=True)
    for a in associations:
        members = [p for p in partners if a["id"] in p.get("associations", [])]
        cards = "".join(partner_card_html(p, link_prefix="../") for p in members)
        body = f"""
  {header_html("../", "associations", "")}
  <a class="back-link" href="../associations.html">&larr; All associations</a>
  <h1 class="profile-title">{html.escape(a['name'])}</h1>
  <p class="profile-meta">{html.escape(a.get('country', ''))}</p>
  <p class="profile-desc">{html.escape(a['description'])}</p>
  <a class="btn" href="{html.escape(a['website'])}" target="_blank" rel="noopener noreferrer">Visit {html.escape(a['name'])} &rarr;</a>
  <p class="section-heading">Associated ({len(members)})</p>
  <div class="grid">{cards}
  </div>"""
        page = page_shell(f"{a['name']} — Archframe", body, depth=1)
        (out_dir / f"{a['slug']}.html").write_text(page)


def generate():
    partners, associations = load_data()
    associations_by_id = {a["id"]: a for a in associations}

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "style.css").write_text(PAGE_CSS)

    generate_index(partners, associations)
    generate_partner_pages(partners, associations_by_id)
    generate_associations_index(associations, partners)
    generate_association_pages(associations, partners)

    print(
        f"Generated docs/index.html, docs/associations.html, "
        f"{len(partners)} partner pages, and {len(associations)} association pages."
    )


if __name__ == "__main__":
    generate()
