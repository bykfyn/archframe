"""
Archframe pilot scraper - Interior Cluster (interiorcluster.se).

WHAT THIS DOES:
  Fetches Interior Cluster's real member page and saves every real
  "Underleverantör" (subcontractor/production-partner) entry - name,
  external link, image, and their own real area/craft tag - to
  data/production_partners.json. This is Archframe's v1 pilot category:
  production partners only, seeded from one real, well-structured
  association source - not architects, not Interior Cluster's other
  member types (Möbelproducent is Formground's territory; Formgivare/
  Intressent are designers/institutions, not production partners).

WHY THIS SOURCE, WHY THIS SELECTOR:
  Checked live (2026-09-15): robots.txt fully open, and - better than
  first assumed - each member sits in a `.member-column` wrapper
  carrying real `data-medlemstyp` (member type) and `data-omrade`
  (area/craft) attributes directly in the server-rendered HTML, not
  just inferred from page position. Selecting on
  `[data-medlemstyp="underleverantör"]` is robust to Interior Cluster
  reordering the page or adding/removing members within the section -
  it doesn't depend on which name happens to be first or last today.

DATA MODEL - DELIBERATELY BUYER-AGNOSTIC:
  Each entry is a craftsperson/workshop entity (name, area/craft tag,
  external link, image) - not modelled as "belongs to Archframe"
  specifically. The same real business could equally be a lead for a
  Formground brand's own outsourced production, not just an architect's
  direct commission - see project memory on why this dataset should
  stay shared/reusable rather than siloed to one buyer relationship.

RUN:
    python3 scrape_interior_cluster.py
"""

import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://interiorcluster.se/medlemmar"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "production_partners.json"

# Case varies in the wild ("underleverantör" confirmed lowercase in the
# real HTML) - matched case-insensitively rather than assuming Interior
# Cluster keeps it consistent forever.
TARGET_MEDLEMSTYP = "underleverantör"

# Interior Cluster's own generic "no photo submitted" placeholder,
# confirmed reused verbatim across at least two different real members
# (Grimslöv Trä & List, Åberg & Söner) - not a real distinguishing
# photo of either business, so treated the same as "no image" rather
# than displayed as if it were one.
PLACEHOLDER_IMAGE_FILENAME = "medlemsbild_1080x6802.jpg"


def _background_image_url(style_attr):
    """Interior Cluster sets each card's photo via an inline
    `background-image: url(...)` style - real, confirmed shape in the
    server-rendered HTML (not JS-injected), so plain requests +
    BeautifulSoup can read it directly, no headless browser needed."""
    if not style_attr:
        return None
    match = re.search(r'url\(["\']?(.*?)["\']?\)', style_attr)
    return match.group(1) if match else None


def scrape():
    resp = requests.get(SOURCE_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    columns = [
        col for col in soup.select(".member-column")
        if (col.get("data-medlemstyp") or "").strip().lower() == TARGET_MEDLEMSTYP
    ]
    if not columns:
        raise RuntimeError(
            f'No .member-column elements found with data-medlemstyp="{TARGET_MEDLEMSTYP}" - '
            "Interior Cluster's page structure may have changed. Re-check the live page "
            "before assuming this source is still usable as-is."
        )

    partners = []
    for col in columns:
        name = (col.get("data-name") or "").strip()
        # A member with more than one real area (e.g. Bendinggroup: wood
        # processing *and* metal) has them tab-separated in the raw
        # attribute, confirmed against the live HTML - split into a real
        # list rather than storing one string with a literal tab in it.
        areas = [a.strip() for a in (col.get("data-omrade") or "").split("\t") if a.strip()]

        link_el = col.select_one(".button-primary a[href]")
        website = link_el["href"].strip() if link_el else None

        bg_el = col.select_one(".member-card-bg")
        image = _background_image_url(bg_el.get("style", "")) if bg_el else None
        if image and PLACEHOLDER_IMAGE_FILENAME in image:
            image = None  # Interior Cluster's own generic stand-in, not a real photo.

        partners.append({
            "name": name,
            "areas": areas,
            # Not scraped per-member - Interior Cluster's own "About" text
            # states it is specifically a national Swedish cluster, so this
            # is a confirmed fact about every member from this source, not
            # a guess. A future non-Swedish source supplies its own value
            # instead of this being retrofitted later.
            "country": "Sweden",
            "website": website,
            "image_url": image,
            # Associations are lead-generation sources into one shared
            # company directory, not per-source silos - a company found via
            # a second association later gets this same id appended, not a
            # separate record. See data/associations.json for the entity
            # this id points to (name, description, own website).
            "associations": ["interior-cluster"],
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(partners, ensure_ascii=False, indent=2))

    no_website = sum(1 for p in partners if not p["website"])
    no_image = sum(1 for p in partners if not p["image_url"])
    print(
        f"Saved {len(partners)} production partners to {OUTPUT_PATH} "
        f"({no_website} with no external link, {no_image} with no real photo)."
    )


if __name__ == "__main__":
    scrape()
