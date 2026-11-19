# EV Spare-Parts Import Prioritization — Ethiopian Market


This repository provides an empirical, reproducible commercial advisory framework to determine the **Top 5 electric vehicle (EV) replacement parts categories** an automotive importer should prioritize for initial stocking in Ethiopia.

---

## 1. Business Problem Understanding & Commercial Scope

1. **Severe Capital & Foreign Currency Scarcity**: Following the ETB currency float, foreign exchange (USD/CNY) is highly constrained. Importing slow-moving inventory or incorrect fitments freezes hard currency and risks catastrophic business failure.
2. **Absence of Official Granular Registration Data**: The Ethiopian Ministry of Transport and regional transport bureaus do not publish registration statistics or aftermarket transaction volumes disaggregated by specific EV model or trim.
3. **Cross-Trim Engineering Variances**: Chinese EV manufacturers frequently introduce running engineering changes across production months and trim levels without altering marketing badges, creating significant compatibility risks.

**The Strategic Objective:** Provide a defensible, empirical decision-support framework to determine the **Top 5 replacement part categories** (out of 10 candidate categories) an importer should prioritize for initial stocking in Ethiopia, backed 100% by verifiable empirical evidence with **zero invented or synthetic data**.

---

### 1.1 Core Strategic Questions Addressed
| Commercial Question | Analytical Approach & Evidence Source | Reference Location |
|---|---|---|
| **Which EV models form the primary target fleet?** | Market visibility across Ethiopian classifieds (`jiji.com.et`), structured dealer platforms (`adey-market.com`), and authorized importer catalogues (`ev.gezat.et`) — treated strictly as operational visibility proxies, not official sales. | Section 7 & `data/processed/scoring/vehicle_selection.csv` |
| **Which parts deliver the highest procurement return?** | Multi-criteria 5-factor scoring model (Demand, Compatibility, Scarcity, Practicality, Confidence) combined with a hard compatibility knock-out gate. | Sections 8–10 & `reports/top5_recommendation.csv` |
| **How resilient and credible is the evidence base?** | Strict source tiering (A/B/C), multi-source cross-verification, empirical missingness audits, foreign exchange float tracking, and 2,000 Dirichlet Monte Carlo simulations. | Sections 3–5, 10–11 & `db/ev_parts.db` |

---

### 1.2 The Five Commercial Decision Lenses
Every replacement part candidate is evaluated across five objective business dimensions:

| Factor | Weight | Importer's Commercial Question | Empirical Evidence Type | Strategic Rationale |
|---|:---:|---|---|---|
| **Demand** | **30%** | *Will customers need this part repeatedly?* | Engineering wear baseline standard + US DOT NHTSA failure signal where available | Prioritizes fast inventory turnover and predictable working capital replenishment. |
| **Compatibility** | **25%** | *Can I be sure it fits the vehicle?* | Verified OEM electronic parts catalogues, cross-reference interchange part numbers | A part that physically does not fit is a 100% financial write-off under foreign exchange constraints. |
| **Scarcity** | **20%** | *Is it hard to find locally in Addis Ababa today?* | Targeted search logs on Ethiopian marketplaces (**0 results seen is verified scarcity**) | Unlocks pricing power, healthy commercial margins, and captured market share. |
| **Practicality** | **15%** | *Can I source, ship, and store it efficiently?* | Logistics feasibility standard (cubic bulk, transit fragility, shelf-life, paint-matching) | Bulky, fragile items (bumpers, sheet metal) destroy container unit economics and freight margins. |
| **Confidence** | **10%** | *How much should I trust the numbers above?* | Source credibility tiering (Tier A = 100, Tier B = 70, Tier C = 40) | Protects decision-makers against uncorroborated claims and single-source bias. |

---

### 1.3 Golden Operational Rules
Throughout the codebase and data pipelines, four non-negotiable evidentiary rules are enforced:
1. **Separation of Policy and Observation**: Every analyst assumption, weight vector, and scoring threshold is declared in the configuration block and labeled `ASSUMPTION`. All downstream calculations reflect pure observation.
2. **Explicit Uncertainty (No Silent Imputation)**: Missing values are never filled with synthetic averages. They remain `NaN` and are tracked with explicit status codes (`observed`, `imputed_from_source_log`, `price_on_request`, `not_found`).
3. **Marketplace Listings as Visibility Proxies**: Classified ads represent observable dealer asking supply and fleet visibility, not finalized registration statistics.
4. **Full Evidentiary Lineage**: Every claim, listing, and catalogue row traces back to an active source URL, publisher tier, and access date.

---

## 2. Repository Structure
```
ev-parts-prioritization/
├── README.md                                # Project overview, execution guide & findings
├── requirements.txt                         # Minimal production dependencies
├── docs/
│   ├── commercial_scope_and_methodology.md  # Detailed commercial scope, criteria & workflow
│   └── data_dictionary.md                   # Column specifications and quality status codes
├── data/
│   ├── raw/                                 # 100% Immutable empirical evidence
│   │   ├── sources_log.csv                  # Source register: working URLs, tiers (A/B/C), access dates
│   │   ├── vehicle_listings_raw.csv         # 252 live vehicle ads (Jiji, Adey Market, Gezat Motors)
│   │   ├── parts_catalog_raw.csv            # 50 verified OEM catalogue fitment records
│   │   ├── local_search_log_raw.csv         # 30 targeted local parts searches across Addis Ababa
│   │   ├── local_parts_listings_raw.csv     # 70 active merchant spare-part listings
│   │   ├── nhtsa_records_raw.csv            # 1,130 US DOT NHTSA safety complaint & recall records
│   │   └── scraped_json/                    # Raw API and crawler response caches
│   │       ├── adey/                        # Adey Market vehicle payloads
│   │       ├── gezat/                       # Gezat Motors inventory payloads
│   │       ├── jiji/                        # Jiji marketplace ad payloads
│   │       └── nhtsa/                       # US DOT NHTSA complaints/recalls
│   ├── external/
│   │   └── fx_rates.csv                     # Official NBE floating exchange rates (ETB/USD, ETB/CNY)
│   └── processed/                           # Standardized outputs categorized by stage
│       ├── cleaned/                         # Clean domain tables for relational DB ingestion
│       │   ├── vehicle_listings_clean.csv
│       │   ├── parts_catalog_clean.csv
│       │   ├── local_part_listings_clean.csv
│       │   ├── search_log_clean.csv
│       │   └── failure_evidence_clean.csv
│       ├── scoring/                         # Analytical scores & decision matrices
│       │   ├── vehicle_selection.csv        # Fleet visibility ranking (Yuan Up, ID.4, Seagull)
│       │   ├── factor_scores_by_vehicle_part.csv # 5-factor scoring per vehicle-part
│       │   ├── final_ranking.csv            # Composite priority scores (10 categories)
│       │   ├── sensitivity_scenarios.csv    # Strategic weighting scenarios
│       │   ├── sensitivity_ranks_by_scenario.csv # Scenario-based rank stability
│       │   └── sensitivity_monte_carlo.csv  # 2,000 Dirichlet Monte Carlo draws
│       └── audit/                           # Data quality, coverage & lineage logs
│           ├── data_issue_log.csv           # 382 logged cleaning decisions
│           ├── raw_missingness_profile.csv  # Pre-cleaning completeness audit
│           └── source_log_with_usage.csv    # Source citation and audit trace
├── db/
│   ├── schema.sql                           # Relational schema (SQLite / PostgreSQL portable)
│   └── ev_parts.db                          # Fully validated relational database (0 FK violations)
├── notebooks/
│   └── 01_ev_parts_prioritization.ipynb     # Executive analysis notebook
├── src/
│   ├── run_pipeline.py                      # Master pipeline: cleaning, DB build, scoring & chart rendering
│   └── scrapers/                            # Modular data extraction and scraping suite
│       ├── fetch_jiji.py                    # Automated scraper for Jiji Ethiopia vehicles & parts
│       ├── fetch_adey.py                    # Automated scraper for Adey Market EV listings
│       ├── fetch_gezat.py                   # Automated scraper for Gezat Motors catalogue
│       └── fetch_nhtsa.py                   # Automated client for US DOT NHTSA safety API
└── reports/
    ├── top5_recommendation.csv              # Prioritized Top 5 categories with stability metrics
    ├── auto_limitations.md                  # Comprehensive empirical and regulatory risk assessment
    └── figures/                             # 6 High-resolution executive presentation charts
        ├── 01_raw_missingness.png           # Raw field completeness profile
        ├── 02_vehicle_selection.png         # Fleet market visibility scores
        ├── 03_missing_evidence_map.png      # Multi-vehicle evidence coverage grid
        ├── 04_score_decomposition.png       # Factor score breakdown across 10 categories
        ├── 05_monte_carlo_stability.png     # Monte Carlo Top-5 inclusion probabilities
        └── 06_opportunity_vs_ease.png       # Strategic opportunity vs. implementation ease quadrant
```

---

## 3. End-to-End Execution Guide
The pipeline is designed to be fully reproducible and executes in seconds using standard Python 3:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the automated data scrapers (optional: re-fetches live evidence)
python src/scrapers/fetch_jiji.py
python src/scrapers/fetch_adey.py
python src/scrapers/fetch_gezat.py
python src/scrapers/fetch_nhtsa.py --make TOYOTA --model bZ4X --years 2023 2024 2025
python src/scrapers/fetch_nhtsa.py --make VOLKSWAGEN --model ID.4 --years 2021 2022 2023 2024 2025

# 3. Execute master data cleaning, database build, scoring & chart generation
python src/run_pipeline.py

# 4. Open and run the executive analysis notebook
jupyter notebook notebooks/01_ev_parts_prioritization.ipynb
```

---

## 4. Key Analytical Findings & Top 5 Recommendations

Based on multi-criteria factor scoring (Demand 30%, Compatibility 25%, Scarcity 20%, Practicality 15%, Confidence 10%) weighted across the top 3 visible EV models (**BYD Yuan Up, Volkswagen ID.4, BYD Seagull**):

| Rank | Part Category | Priority Score | Monte Carlo Top-5 Prob | Stability Class | Commercial Strategic Justification |
|:---:|---|:---:|:---:|:---:|---|
| **1** | **Wiper blades** | **92.00** | 100.0% | **Robust** | High routine demand driven by high UV exposure and dust abrasion; rapid turnover; low shipping weight and easy warehouse storage. |
| **2** | **Cabin-air filters** | **87.00** | 100.0% | **Robust** | Critical consumable requiring replacement every 5,000–10,000 km due to Addis Ababa dust levels; zero compatibility failure risk. |
| **3** | **Brake pads** | **82.00** | 100.0% | **Robust** | Primary mechanical wear component; severe stop-and-go Addis traffic combined with hilly topography wears friction material despite regenerative braking. |
| **4** | **Brake discs (rotors)** | **72.00** | 98.7% | **Robust** | Replaced every 2 pad cycles; acute local market shortage in Addis Ababa; high commercial margin potential. |
| **5** | **Side mirrors** | **65.75** | 71.4% | **Probable** | High collision and parking damage frequency in congested urban corridors; moderate supply constraints. |

*Runner-Up / Phase 2 Category:* **Shock absorbers** (Score: 65.00, Top-5 Prob: 64.9%) — High wear from road surface conditions and heavy EV curb weights, recommended for subsequent procurement tranches once initial supply channels are established.

---

## 5. Architectural Principles & Quality Assurance
- **100% Genuine, Verifiable Evidence**: No synthetic rows, mock URLs, or fabricated part numbers. Every record links to a live, working HTTP/HTTPS domain.
- **Relational Integrity**: Foreign-key enforced SQLite database (`db/ev_parts.db`) with zero constraint violations.
- **Explicit Missingness Handling**: Missing values are never silently imputed; fields retain explicit status codes (`observed`, `converted_fx`, `price_on_request`, `not_found`).
- **Compatibility Knock-Out Gate**: Components with unverified fitment (< 40) are eliminated from consideration before ranking.
- **Sensitivity Robustness**: The top 3 consumable categories (Wipers, Cabin Filters, Brake Pads) achieved a **100.0% inclusion probability across 2,000 randomized Monte Carlo Dirichlet weight variations**.
