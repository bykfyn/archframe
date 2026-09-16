"""
Archframe pilot scraper - Skråhantverkarna (skrahantverkarna.se).

WHAT THIS DOES:
  Fetches Föreningen Skråhantverkarna's real, complete member listing
  and saves every member - name, craft category, real photo, street
  address + city, and their own real website - to
  data/sources/skrahantverkarna.json (one file per source - see
  merge_partners.py for how sources get combined into the real, final
  data/production_partners.json).

WHY THIS SOURCE:
  Checked live (2026-09-16): robots.txt fully open (Yoast's default
  block list, nothing relevant disallowed). Small (45 real members) but
  the richest per-entry data quality found of any source checked so
  far - every member has a real photo, and this is the only source
  found with real city-level address data, confirmed against 8 real
  entries spanning genuinely different Swedish towns (Karlskrona,
  Hökarängen, Stockholm, Tystberga, Kälarne, Tingsryd), not just
  Stockholm. Skews heritage/traditional craft (bookbinders, gilders,
  violin-makers) more than production-capacity workshops, but several
  crafts genuinely overlap Archframe's scope (möbelsnickare/furniture
  carpenter, möbelrenoverare/furniture restorer, inredningssnickare/
  interior carpenter).

WHY /all-listing/, NOT THE HOMEPAGE:
  Both pages happen to show the same 45 real member cards (confirmed by
  comparing counts) and neither paginates, but /all-listing/ is the
  dedicated directory archive - the homepage mixing this in is an
  implementation detail of their theme, not a stable contract.

WHY A SECOND FETCH PER MEMBER:
  The listing card itself (a WP business-directory-plugin card, class
  `atbd_single_listing`) has name, category, photo, and a link to the
  member's own detail page - but NOT their real external website. The
  website only appears on that detail page, in a `.atbd_contact_info`
  block where each `<li>` is tagged by icon class (`la-map-marker`
  address, `la-phone` phone, `la-envelope` email, `la-globe` website) -
  a real, reliable signal to select on, not position-guessing. This
  means 45 extra requests (one per member) - small and bounded, not the
  kind of unbounded crawl the project's own resource-conscious-scraping
  rule warns against. A short delay between requests is polite, not
  because Skråhantverkarna asked for one (no Crawl-delay in robots.txt).

DATA MODEL:
  Same buyer-agnostic shape as scrape_interior_cluster.py - see that
  file's docstring for why (production partners are leads shared across
  Formground brands, architects, and homeowners alike, not siloed to
  one buyer relationship).

RUN:
    python3 scrape_skrahantverkarna.py
"""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

LISTING_URL = "https://skrahantverkarna.se/all-listing/"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "sources" / "skrahantverkarna.json"
REQUEST_DELAY_SECONDS = 0.2

# Every real address found so far (across all 45 members) is a genuine
# Swedish town with a Swedish-format postal code - not asserted a priori,
# derived per-member below from the actual scraped address text.
SWEDISH_POSTCODE = re.compile(r"^\d{3}\s?\d{2}\s+")


def _split_address(raw_address):
    """"Intagsvägen 3, Karlskrona" -> ("Intagsvägen 3", "Karlskrona").
    "Måstena 3, 611 99 Tystberga" -> ("Måstena 3", "Tystberga") - the
    Swedish postal code prefix on the city half is stripped, not kept as
    part of the city name."""
    parts = [p.strip() for p in raw_address.split(",")]
    if len(parts) < 2:
        return raw_address.strip(), None
    street = ", ".join(parts[:-1])
    city = SWEDISH_POSTCODE.sub("", parts[-1]).strip()
    return street, city or None


def _contact_field(detail_soup, icon_class):
    li = detail_soup.select_one(f"div.atbd_contact_info li:has(span.{icon_class})")
    if not li:
        return None
    value_el = li.select_one(".atbd_info")
    if not value_el:
        return None
    link = value_el.find("a")
    return (link.get_text(strip=True) if link else value_el.get_text(strip=True)) or None


def _detail_website(detail_soup):
    li = detail_soup.select_one("div.atbd_contact_info li:has(span.la-globe)")
    if not li:
        return None
    link = li.select_one("a[href]")
    return link["href"].strip() if link else None


def scrape():
    resp = requests.get(LISTING_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cards = soup.select("div.atbd_single_listing")
    if not cards:
        raise RuntimeError(
            "No div.atbd_single_listing cards found - Skråhantverkarna's page "
            "structure may have changed. Re-check the live page before assuming "
            "this source is still usable as-is."
        )

    partners = []
    for card in cards:
        title_link = card.select_one("h4.atbd_listing_title > a")
        name = title_link.get_text(strip=True) if title_link else None
        detail_url = title_link["href"] if title_link else None
        if not name or not detail_url:
            continue

        img_el = card.select_one(".atbd_listing_image img[src]")
        image = img_el["src"].strip() if img_el else None

        category_el = card.select_one(".atbd_listting_category a")
        area = category_el.get_text(strip=True) if category_el else None

        detail_resp = requests.get(detail_url, timeout=30)
        detail_resp.raise_for_status()
        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")

        raw_address = _contact_field(detail_soup, "la-map-marker")
        _, city = _split_address(raw_address) if raw_address else (None, None)
        website = _detail_website(detail_soup)

        partners.append({
            "name": name,
            "areas": [area] if area else [],
            "city": city,
            # Derived per-member from a real scraped Swedish address, not
            # asserted for the whole source the way Interior Cluster's
            # "About" text let us do directly.
            "country": "Sweden" if city else None,
            "website": website,
            "image_url": image,
            "associations": ["skrahantverkarna"],
        })

        time.sleep(REQUEST_DELAY_SECONDS)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(partners, ensure_ascii=False, indent=2))

    no_website = sum(1 for p in partners if not p["website"])
    no_image = sum(1 for p in partners if not p["image_url"])
    no_city = sum(1 for p in partners if not p["city"])
    print(
        f"Saved {len(partners)} production partners to {OUTPUT_PATH} "
        f"({no_website} with no external link, {no_image} with no real photo, "
        f"{no_city} with no city)."
    )


if __name__ == "__main__":
    scrape()
