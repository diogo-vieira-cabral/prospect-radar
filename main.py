import yaml
import time
import random
import logging
from pathlib import Path

from scraper import search_olx

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/monitor.log"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ── Ensure folders exist ───────────────────────────────────────────────────────
Path("data").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# ── Load config ────────────────────────────────────────────────────────────────
with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

mode = config["search"].get("mode", "keyword")

if mode == "category":
    search_targets = config["search"]["categories"]
else:
    search_targets = config["search"]["keywords"]

# Flatten scoring categories into a single rules dict for the scorer
# scorer.py receives: { keyword: points, ... }
scoring_rules = {}
for category_name, category_data in config["scoring"]["categories"].items():
    for keyword, points in category_data["keywords"].items():
        # If keyword appears in multiple categories, take the highest value
        if keyword not in scoring_rules or scoring_rules[keyword] < points:
            scoring_rules[keyword] = points

scoring_config = config["scoring"]  # Full config passed for caps + bonuses
alert_score = config["alerts"]["min_score"]
telegram_threshold = config["alerts"]["telegram_threshold"]

tier1_keywords = config["tier1"]["gate_keywords"]


# ── Interval helper ────────────────────────────────────────────────────────────
def get_interval_seconds() -> int:
    """
    Returns sleep interval in seconds.
    If config says 'random', picks a value between 18-35 minutes.
    Otherwise uses the configured integer directly.
    """
    interval = config["schedule"]["interval_minutes"]
    if interval == "random":
        return random.randint(18, 35) * 60
    return int(interval) * 60


# ── Export results ─────────────────────────────────────────────────────────────
def save_results(df):
    if df.empty:
        log.info("No new listings found this cycle.")
        return

    output_path = Path("data/jobs.csv")
    write_header = not output_path.exists()

    import csv
    df.to_csv(
        output_path,
        mode="a",
        index=False,
        header=write_header,
        encoding="utf-8",
        quoting=csv.QUOTE_ALL,   # Wrap every field in quotes — prevents comma splits
    )

    log.info(f"Saved {len(df)} new listing(s) to {output_path}")


# ── Main loop ──────────────────────────────────────────────────────────────────
def run():
    cycle = 0

    while True:
        cycle += 1
        log.info(f"=== Cycle {cycle} started — mode: {mode} ===")

        try:
            df = search_olx(
                targets=search_targets,
                mode=mode,
                scoring_rules=scoring_rules,
                scoring_config=scoring_config,
                tier1_keywords=tier1_keywords,
                alert_score=alert_score,
                telegram_threshold=telegram_threshold,
                pages_per_category=config["schedule"].get("pages_per_category", 4),
            )
            save_results(df)

        except Exception as e:
            log.error(f"Cycle {cycle} failed: {e}", exc_info=True)

        interval = get_interval_seconds()
        log.info(f"=== Cycle {cycle} complete. Sleeping {interval // 60}m ===\n")
        time.sleep(interval)


if __name__ == "__main__":
    run()
