# Archframe (working name)

An early pilot for professional/production-partner discovery - the first
category is real workshops and fabricators (carpenters, metalworkers,
upholsterers, material suppliers) that architects, designers, and small
product brands can commission or outsource work to.

**Status**: pilot only. Not a finished product, not indexed for search
engines yet (`noindex` is set on the page), no permanent name or domain -
temporarily hosted at Sheerd.com while "Archframe" itself stays a working
name (a few real alternatives - Sourceframe, Trestle - were already ruled
out on name collisions).

## What's here

- `scraper/scrape_interior_cluster.py` - scrapes the real, public
  "Underleverantör" (subcontractor) section of Interior Cluster
  (interiorcluster.se), a real Swedish furniture-industry cluster
  organisation, and saves it to `data/production_partners.json`.
- `scraper/generate_pilot_page.py` - builds `docs/index.html`, a static
  page with a plain client-side substring filter (name/craft/country,
  no backend, no query parsing).
- `docs/` - the generated site, served by GitHub Pages.

## Running it yourself

```bash
cd scraper
pip install -r requirements.txt
python3 scrape_interior_cluster.py   # re-scrapes the real, live source
python3 generate_pilot_page.py       # rebuilds docs/index.html from that data
```

## Why this data source

Checked directly before building anything: `interiorcluster.se/robots.txt`
is fully open, and each member on their real member page carries genuine
`data-medlemstyp` (member type) and `data-omrade` (craft/area) attributes
in the server-rendered HTML - a robust, real signal to filter on, not a
guess based on name order or page position.

## Deliberately not built yet

- No architects/interior-design category - production partners only,
  to prove the concept on the best-seeded data source first.
- No monetization.
- No permanent name (domain is set - sheerd.world).
- No Swedish-language variant yet - deferred until a specific pitch to
  a Swedish association (e.g. Interior Cluster) needs it.
