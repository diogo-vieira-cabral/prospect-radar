import re
import logging

log = logging.getLogger(__name__)


def calculate_score(text: str, scoring_config: dict) -> tuple[int, dict, list]:
    """
    Scores an ad using the full scoring config.

    Implements:
    - Per-category scoring with caps
    - Redundancy buffer: first match = full value, repeats = 15% face value
    - Co-occurrence bonuses (capped at config total)
    - Returns score, breakdown by category, and matched keywords list

    Parameters
    ----------
    text : str
        Combined text from title + page content
    scoring_config : dict
        Full scoring section from config.yml

    Returns
    -------
    tuple:
        total_score : int
        breakdown : dict  — { category_name: points_scored }
        keywords_matched : list — [ "keyword(+points)", ... ]
    """
    if not text or not scoring_config:
        return 0, {}, []

    text_lower = text.lower()
    categories = scoring_config.get("categories", {})
    redundancy_buffer = scoring_config.get("redundancy_buffer", 0.15)
    cooccurrence_config = scoring_config.get("cooccurrence_bonuses", {})

    total_score = 0
    breakdown = {}
    keywords_matched = []
    all_matched_keywords = set()  # Used for co-occurrence checks

    # ── Per-category scoring ───────────────────────────────────────────────────
    for category_name, category_data in categories.items():
        cap = category_data.get("cap", 999)
        keywords = category_data.get("keywords", {})

        category_score = 0
        category_matched = []
        keyword_hit_count = {}  # Tracks how many times a keyword concept fires

        for keyword, points in keywords.items():
            keyword_lower = keyword.lower()
            pattern = r"\b" + re.escape(keyword_lower) + r"\b"

            matches = re.findall(pattern, text_lower)
            if not matches:
                continue

            hit_count = keyword_hit_count.get(keyword_lower, 0)

            if hit_count == 0:
                # First match — full value
                awarded = points
            else:
                # Repeat — redundancy buffer only
                awarded = round(points * redundancy_buffer)

            keyword_hit_count[keyword_lower] = hit_count + 1
            category_score += awarded
            category_matched.append(f"{keyword}(+{awarded})")
            all_matched_keywords.add(keyword_lower)

        # Apply category cap
        category_score = min(category_score, cap)
        breakdown[category_name] = category_score
        total_score += category_score
        keywords_matched.extend(category_matched)

        if category_matched:
            log.debug(
                f"[{category_name}] {', '.join(category_matched)} → "
                f"capped at {category_score}/{cap}"
            )

    # ── Co-occurrence bonuses ──────────────────────────────────────────────────
    bonus_cap = cooccurrence_config.get("cap", 8)
    pairs = cooccurrence_config.get("pairs", [])
    total_bonus = 0

    for pair in pairs:
        if total_bonus >= bonus_cap:
            break

        pair_keywords = [k.lower() for k in pair.get("keywords", [])]
        bonus = pair.get("bonus", 0)

        if all(k in all_matched_keywords for k in pair_keywords):
            awarded_bonus = min(bonus, bonus_cap - total_bonus)
            total_bonus += awarded_bonus
            total_score += awarded_bonus
            breakdown["cooccurrence_bonuses"] = (
                breakdown.get("cooccurrence_bonuses", 0) + awarded_bonus
            )
            keywords_matched.append(
                f"cooccurrence({'+'.join(pair_keywords)})(+{awarded_bonus})"
            )
            log.debug(
                f"Co-occurrence bonus: {pair_keywords} → +{awarded_bonus}"
            )

    log.debug(f"Total score: {total_score} | Breakdown: {breakdown}")
    return total_score, breakdown, keywords_matched
