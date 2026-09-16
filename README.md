# Archframe (working name)

An early pilot for professional/production-partner discovery - the first
category is real workshops and fabricators (carpenters, metalworkers,
upholsterers, material suppliers) that architects, designers, and small
product brands can commission or outsource work to.

**Status**: pilot only. Not a finished product, not indexed for search
engines yet (`noindex` is set on the page). Hosted at sheerd.world while
"Archframe" itself stays a working name and no permanent domain of its
own has been registered (a few real alternatives - Sourceframe, Trestle -
were already ruled out on name collisions).

## What's here

- `scraper/scrape_interior_cluster.py` - scrapes the real, public
  "Underleverantör" (subcontractor) section of Interior Cluster
  (interiorcluster.se), a real Swedish furniture-industry cluster
  organisation, and saves it to `data/sources/interior_cluster.json`.
- `scraper/scrape_skrahantverkarna.py` - scrapes Föreningen
  Skråhantverkarna's real, complete member listing (45 members, every
  one with a real photo, most with real city-level address data) to
  `data/sources/skrahantverkarna.json`.
- `scraper/merge_partners.py` - combines every `data/sources/*.json`
  file into the real, final `data/production_partners.json`,
  deduplicating on normalized website domain+path (falling back to
  normalized name) so the same real company found via more than one
  association becomes one entry with multiple associations, not a
  duplicate. See the module's own docstring for a real case this
  already caught and had to be fixed for (two genuinely distinct
  sibling companies, "WOG Metall" and "WOG Trä", sharing one parent
  domain via different paths - domain-only matching wrongly merged
  them into one until the key included the path too). Also applies a
  per-association craft-relevance filter (`RELEVANT_AREAS_BY_ASSOCIATION`)
  - not every trade an association lists belongs on Archframe (that's
  Brandvue's job, re-presenting an association's *complete* roster back
  to them); Skråhantverkarna's 45 members narrow to the 22 whose craft
  is furniture/interior/building-relevant, while the full scrape stays
  intact in `data/sources/skrahantverkarna.json` for whenever Brandvue
  is real. Interior Cluster needs no filter - every craft tag it uses is
  already furniture-industry-relevant, since Interior Cluster itself is
  a furniture-industry cluster.
- `data/associations.json` - the association(s) used as sources, as
  entities in their own right (name, description, own website) - not
  just a text field on each partner. Associations are lead-generation
  sources feeding one shared, deduplicated company directory; a
  partner's `associations` field is a list, since the same real company
  showing up via more than one association is a legitimacy signal, not
  a duplicate-data problem. See project memory ("Architecture pivot:
  associations as sources, not silos") for the full reasoning - this is
  also, concretely, a first working instance of Brandvue's own thesis.
- `scraper/generate_pilot_page.py` - builds the whole static site:
  `docs/index.html` (the main grid, filterable by a plain client-side
  substring search - name/craft/country, no backend), one real profile
  page per partner at `docs/partners/<slug>.html` (photo, tags, which
  association(s) vouch for them, a link out to their own site), and
  `docs/associations.html` / `docs/associations/<slug>.html` (each
  association's own profile, with the real "Associated" grid of its
  members - the same pattern found on sheerd.com's own brand/
  association profiles).
- `docs/` - the generated site, served by GitHub Pages.

## Running it yourself

```bash
cd scraper
pip install -r requirements.txt
python3 scrape_interior_cluster.py   # re-scrapes Interior Cluster
python3 scrape_skrahantverkarna.py   # re-scrapes Skråhantverkarna
python3 merge_partners.py            # combines both sources, deduplicated + craft-relevance filtered
python3 generate_pilot_page.py       # rebuilds the whole docs/ site from that data
```

## Why these data sources

- **Interior Cluster**: checked directly before building anything -
  `interiorcluster.se/robots.txt` is fully open, and each member on their
  real member page carries genuine `data-medlemstyp` (member type) and
  `data-omrade` (craft/area) attributes in the server-rendered HTML - a
  robust, real signal to filter on, not a guess based on name order or
  page position.
- **Skråhantverkarna**: `skrahantverkarna.se/robots.txt` is fully open
  (Yoast's default block list, nothing relevant disallowed). Smaller (45
  members) but the richest per-entry data quality found of any source
  researched so far - every member has a real photo, and it's the only
  source found with real city-level address data.

## Deliberately not built yet

- Two association sources merged so far (Interior Cluster,
  Skråhantverkarna), on purpose one at a time - Hantverkarna Stockholm,
  Snickarmästarna, and TMF are all researched but not yet built.
  Hantverkarna Stockholm is next in line (190 members, very clean
  structure, but zero images and needs real filtering - of ~66 real
  trades in use, only ~15-20 are Archframe-relevant, the rest is
  hairdressers/tattoo-artists/etc. breadth from a much broader craft
  guild). Snickarmästarna needs more defensive parsing than any other
  source checked (real per-member structure exists but is inconsistently
  populated). TMF needs its actual query API re-derived from the current
  JS bundle before its real yield for the Underleverantör tier is known.
- No "scrape the company's own site" step yet - the realistic version
  of this (once it's built) is pulling each company's Open Graph image
  and meta description, not a full custom per-site scrape, since there's
  no shared markup across ~hundreds of arbitrary small-business sites
  the way there is within one association's member page.
- No architects/interior-design category - production partners only,
  to prove the concept on the best-seeded data source first.
- No monetization.
- No permanent name (domain is set - sheerd.world).
- No Swedish-language variant yet - deferred until a specific pitch to
  a Swedish association (e.g. Interior Cluster) needs it.
- No per-category pages (e.g. a dedicated metalworkers page), unlike
  Formground. Those earn their keep there on real SEO surface area
  (thousands of products across dozens of brands) and genuine browsing
  need at that catalog size - neither applies yet at 30 entries on a
  page that's still `noindex`. The existing search/filter box already
  covers "find me the metalworkers" at this scale. Revisit once the
  dataset grows past a single source and/or the page comes out of
  `noindex` to pursue search traffic for real.
