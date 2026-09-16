"""
Merges every data/sources/*.json file into the real, final
data/production_partners.json.

WHY THIS EXISTS:
  Associations are lead-generation sources feeding one shared,
  deduplicated company directory, not one dataset per source (see
  project memory: "Architecture pivot: associations as sources, not
  silos"). A company found via more than one association is a
  legitimacy signal, not a duplicate-data problem - this script is
  where that merge actually happens, so each source scraper can stay
  simple and just describe what it found, not worry about what other
  sources already know.

MERGE KEY:
  Normalized website domain + path first (most reliable - two listings
  of the same real company almost always link to the exact same page
  even if the name is capitalized differently or has a different legal
  suffix), falling back to a normalized name for the rare company with
  no website at all. Domain alone is NOT enough: real data already
  caught a case of it being wrong - Interior Cluster lists "WOG Metall"
  (https://www.wogtra.se/wog-metall/) and "WOG Trä"
  (https://www.wogtra.se/wog-tra/) as two genuinely distinct entries
  (different craft, different photo) that are sibling divisions sharing
  one parent domain with different paths - domain-only merging silently
  collapsed them into one. This is the same instinct as Coreframe's
  product-variant merging, one level up (company identity, not product
  variants) - and a live reminder that a merge key needs real data to
  stress-test it, not just a plausible-sounding design.

WHEN TWO SOURCES DESCRIBE THE SAME COMPANY:
  Associations are unioned (so a company shows correctly as a member of
  both). Any other field keeps its first real (non-null) value and only
  takes a later source's value to fill an actual gap - never overwrites
  a real value with another real value, so which source happens to run
  first doesn't quietly change what's shown.

RUN:
    python3 merge_partners.py
"""

import json
import re
from pathlib import Path
from urllib.parse import urlparse

SOURCES_DIR = Path(__file__).parent.parent / "data" / "sources"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "production_partners.json"

MERGEABLE_FIELDS = ["city", "country", "website", "image_url", "areas"]


def normalize_website(url):
    """Domain + path, not domain alone - see the module docstring for the
    real WOG Metall / WOG Trä case this guards against (two distinct
    sibling companies sharing one domain via different paths)."""
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"//{url}")
    domain = re.sub(r"^www\.", "", parsed.netloc.lower())
    path = parsed.path.rstrip("/")
    return f"{domain}{path}" if domain else None


def normalize_name(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def merge_key(partner):
    website_key = normalize_website(partner.get("website"))
    return f"website:{website_key}" if website_key else f"name:{normalize_name(partner['name'])}"


def merge_into(existing, incoming):
    for aid in incoming.get("associations", []):
        if aid not in existing["associations"]:
            existing["associations"].append(aid)
    for field in MERGEABLE_FIELDS:
        existing_value = existing.get(field)
        incoming_value = incoming.get(field)
        if not existing_value and incoming_value:
            existing[field] = incoming_value


def merge():
    source_files = sorted(SOURCES_DIR.glob("*.json"))
    if not source_files:
        raise RuntimeError(f"No source files found in {SOURCES_DIR} - run the scrapers first.")

    merged = {}
    for path in source_files:
        for partner in json.loads(path.read_text()):
            key = merge_key(partner)
            if key in merged:
                merge_into(merged[key], partner)
            else:
                merged[key] = {**partner, "associations": list(partner.get("associations", []))}

    partners = sorted(merged.values(), key=lambda p: p["name"].lower())
    OUTPUT_PATH.write_text(json.dumps(partners, ensure_ascii=False, indent=2))

    multi_association = sum(1 for p in partners if len(p["associations"]) > 1)
    print(
        f"Merged {len(source_files)} source file(s) into {len(partners)} unique partners "
        f"({multi_association} found via more than one association) -> {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    merge()
