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
  organisation, and saves it to `data/production_partners.json`.
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
python3 scrape_interior_cluster.py   # re-scrapes the real, live source
python3 generate_pilot_page.py       # rebuilds the whole docs/ site from that data
```

## Why this data source

Checked directly before building anything: `interiorcluster.se/robots.txt`
is fully open, and each member on their real member page carries genuine
`data-medlemstyp` (member type) and `data-omrade` (craft/area) attributes
in the server-rendered HTML - a robust, real signal to filter on, not a
guess based on name order or page position.

## Deliberately not built yet

- Only one association source (Interior Cluster) for now, on purpose -
  the associations/profile-pages architecture above is being proven on
  one clean source before Hantverkarna Stockholm, Skråhantverkarna,
  Snickarmästarna, and TMF (all researched, none yet built) get merged
  into the same shared directory. Merging them will need a real
  dedup step (normalized website domain as the primary key) once a
  company can plausibly appear via more than one source.
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
