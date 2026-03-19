# DEVELOPMENT.md — prospect-radar

A record of key design decisions and the reasoning behind them.

---

## Why category scraping, not keyword search

**Decision:** scrape by OLX job category, not by keyword query.

**Reasoning:** keyword search in titles misses everything that scores high but uses different wording. A company posting "Apoio Administrativo — Gestão de Processos Internos" never appears in a keyword search for "automação" — but it's still a prospect. Category scraping pulls everything in the relevant universe and lets scoring decide what surfaces. Search keywords are too brittle and too narrow for a signal detection approach.

**Tradeoff:** broader catch = more volume to score and more tier 2 precision required to separate signal from noise.

---

## Why a three-tier architecture

**Decision:** Tier 1 gate → Tier 2 scoring → Tier 3 enrichment, run in sequence.

**Reasoning:** a single scoring pass on all ads is too slow and too noisy.   
(Tier 1) Discards obvious non-matches before any real processing happens — no full page load, no scoring. This keeps the scraper lean. 
(Tier 2) Full ad read, deeper scanning for scoring.
(Tier 3) Secondary, conditional pipeline, confirming companies legitimacy and adding basic information

---

## Why scoring uses category caps, not flat weights

**Decision:** each scoring category has a maximum it can contribute to the total score.

**Reasoning:** if there is an ad with several iterations of the same keyword or signal type, it should not add up linearly.

---

## Why repeated keywords score at 15% after the first hit

**Decision:** within a category, first keyword = full score, each additional match = 25% of face value.

**Reasoning:** repetition of related terms in an ad (e.g. "automatizar" and "automação" both appearing) is a soft urgency signal — it suggests the writer is emphasizing something. But it shouldn't artificially inflate the total. 15% captures the signal without gaming the score.

---



## Why penalize unregistered companies instead of filter them

**Decision:** "ghost" companies and unregistered entities receive a score penalty, not a hard exclusion.

**Reasoning:** hard filtering risks losing real prospects with messy or incomplete ad data. A penalty preserves them in the dataset at a lower score — they can still surface if other signals are strong enough, but they won't dominate. It also keeps the system auditable: you can see why something scored low rather than wondering why it disappeared.

---


## On scraper detection mitigation

**Approach:** randomized intervals (18-35 min), randomized request delays (4-12s per page), random category order per run, user-agent rotation.

**Reasoning:** OLX PT does not publish explicit scraping limits. The goal is not invisibility — it's to avoid looking like an automated tool running on a fixed schedule. Human browsing is irregular. The scraper should be too.
