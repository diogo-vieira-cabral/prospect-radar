# prospect-radar

A weighted signal detection pipeline that monitors Portuguese job boards in near real time, used as a prospecting tool to identify companies with operational pain before they hire.

---

## What it does

- Scrapes job board listings by category or keyword (currently OLX Portugal)
- Gates ads at scrape time — discards noise before loading the full ad
- Scores each ad using a configurable weighted ruleset with per-category caps
- Rewards high-value keyword combinations via co-occurrence bonuses
- Tracks seen URLs across runs — no duplicate processing
- Outputs to CSV with enrichment and outreach columns pre-structured
- Fires Telegram alerts for high-signal ads above threshold

---

## Architecture — three tiers

**Tier 1 — Scraper gate**
Checks title before loading the full ad. If no qualifying keyword is present, the ad is discarded immediately — no full page load, no scoring. Fast and cheap.

**Tier 2 — Scoring engine**
Runs on full ad text. Weighted keyword rules across categories with per-category caps to prevent score inflation from a single strong category.
Repeated keywords within a category score at diminishing value (redundancy buffer).
Co-occurrence bonuses reward high-value keyword combinations.

**Tier 3 — Company enrichment** *(planned)*
Looks up the company name on public registries (Racius/Einforma). Confirmed registered = score bonus. Unverifiable or ghost company = penalty. Penalisation, not hard filtering. Feeds contact-finding stage.

---

## Scraper modes

Configured in `config.yml` (gitignored — copy from `config.example.yml`):

```yaml
search:
  mode: category   # or: keyword

  categories:
    - administrativo-e-secretariado
    - it-e-telecomunicacoes
    - comercial

  keywords:        # used in keyword mode only
    - analista dados
    - automação
```

`category` mode scrapes OLX category pages — broader catch, scoring filters the noise.
`keyword` mode uses OLX search — narrower, useful for targeted terms or testing.
Scoring runs identically in both modes.

---

## Scoring

Scoring config lives entirely in `config.yml` and is not included in this repository.
`config.example.yml` shows the full structure with placeholder values.

Key mechanics:
- Keywords are grouped into named categories, each with a point cap
- First match = full value; repeated keywords = 15% face value (redundancy buffer)
- Co-occurrence bonuses fire when specific keyword pairs appear together
- `min_score` sets the floor for CSV output
- `telegram_threshold` fires an immediate alert for high-signal ads

---

## Alerts

Telegram notification fires when a scored ad exceeds `telegram_threshold`.
High-signal ads surface within minutes of posting.
*(Telegram integration is in the pipeline — currently logs at INFO level.)*

---

## Project structure

```text
prospect-radar/
│
├── data/                    # output leads — gitignored
│   ├── jobs.csv             # scored and filtered listings
│   └── seen_urls.json       # deduplication tracker
│
├── logs/
│   └── monitor.log          # runtime logs
│
├── config.example.yml       # full config structure with placeholder values
├── config.yml               # your scoring rules — gitignored, never committed
│
├── main.py                  # entry point and run loop
├── scraper.py               # OLX fetch, Tier 1 gate, company name extraction
├── scorer.py                # Tier 2 scoring engine
├── csv_repair.py            # utility — recover rows from corrupted CSV output
│
├── requirements.txt
└── README.md
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp config.example.yml config.yml
# edit config.yml — add your scoring keywords and thresholds
```

---

## Usage

```bash
python main.py
```

Results append to `data/jobs.csv`. Logs write to `logs/monitor.log`.

---

## Roadmap

- [ ] Tier 3 enrichment — Racius/Einforma legitimacy lookup + score delta
- [ ] Contact finding — website scrape + LinkedIn Google fallback
- [ ] Telegram alert integration
- [ ] Expand to additional sources (Indeed PT, Net-Empregos)
- [ ] SQLite migration (currently CSV, sufficient to ~500 records per source)

---

## Notes

- Only collects public listing data — no personal data stored
- Respects site load with randomised request delays and user-agent rotation
- Enrichment uses free public lookups only
- Scoring logic is not included in this repository — `config.example.yml` shows structure only
