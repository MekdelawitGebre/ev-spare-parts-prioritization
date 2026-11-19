# Commercial Scope & Analytical Methodology

## 1. Executive Summary & Commercial Objective
A commercial automotive enterprise intends to establish an import and distribution operation for **electric vehicle (EV) replacement parts in Ethiopia**. Given capital constraints and inventory carrying costs, the client cannot initially stock every spare part across all EV models operating in the country.

Because official vehicle registration registries and aftermarket sales transactions are not published by model in Ethiopia, procurement decisions must rely on rigorous empirical evidence:
- Turning imperfect, publicly verifiable data across Ethiopian digital marketplaces, distributor inventories, international parts catalogues, and regulatory defect databases into a **reproducible, prioritized procurement plan**.
- Recommending the **Top 5 initial EV spare-part categories** to import, backed by sensitivity analysis and audit logs.
- Upholding an evidence-first principle: *factual, verifiable empirical data outweighs speculation, and identifying where evidence is currently unavailable is a valid, auditable risk management outcome.*

---

## 2. Core Strategic Questions Addressed
| Commercial Question | Analytical Approach & Evidence Source | Reference Location |
|---|---|---|
| **Which EV models form the primary target fleet?** | Market visibility across Ethiopian classifieds (`jiji.com.et`), structured dealer platforms (`adey-market.com`), and authorized importer catalogues (`ev.gezat.et`) — treated strictly as visibility proxies, not official sales. | Notebook Section 7 & `vehicle_selection.csv` |
| **Which parts deliver the highest procurement return?** | Multi-criteria 5-factor scoring model (Demand, Compatibility, Scarcity, Practicality, Confidence) with a hard compatibility knock-out gate. | Notebook Sections 8–10 & `top5_recommendation.csv` |
| **How resilient and credible is the evidence base?** | Strict source tiering (A/B/C), multi-source cross-verification, empirical missingness audit, foreign exchange float tracking, and Monte Carlo stability testing. | Notebook Sections 3–5, 10–11 & SQLite DB |

---

## 3. Project Deliverables & System Architecture
| # | Commercial Deliverable | System / File Location |
|---|---|---|
| 1 | Raw Empirical Evidence | `data/raw/*.csv`, `data/raw/scraped_json/` |
| 2 | Cleaned & Standardized Datasets | `data/processed/cleaned/*_clean.csv` |
| 3 | Relational Operational Database | `db/ev_parts.db` (SQLite with enforced foreign keys) |
| 4 | Executive Analysis Notebook | `notebooks/01_ev_parts_prioritization.ipynb` |
| 5 | Master Audit Source Register | `data/raw/sources_log.csv` & `data/processed/audit/source_log_with_usage.csv` |
| 6 | Strategic Procurement Ranking | `reports/top5_recommendation.csv` |
| 7 | Regulatory & Market Limitations Audit | `reports/auto_limitations.md` |
| 8 | Executive Briefing Visualizations | `reports/figures/01_*.png` through `06_*.png` |

---

## 4. Prioritization & Evaluation Framework
To guarantee commercial robustness, the analytical framework evaluates:
1. **Scoring Methodology & Justification (25% weighting)**: Explicit mathematical formulation, defensible weight justifications, and empirical sensitivity proof demonstrating how shifting weights impact candidate rankings.
2. **Source Integrity & Evidentiary Quality (20% weighting)**: Minimum 2 independent sources per claim where available, tiered sources (A/B/C), mandatory working URLs, collection timestamps, and localized Ethiopian pricing evidence.
3. **Data Quality & Relational Schema (20% weighting)**: Transparent schema design, full logging of missing values, duplicate detection, and explicit FX conversions.
4. **Commercial Market Context (15% weighting)**: Clear understanding of Ethiopian import policies (fuel-vehicle ban, post-July 2024 Birr float), fleet selection rationale, and careful separation of listing counts from registration numbers.
5. **Recommendations & Strategic Risk Audit (10% weighting)**: Top 5 actionable import categories, explicit capital exposure controls, and unvarnished documentation of data gaps.
6. **Code Engineering & Reproducibility (10% weighting)**: Clean, modular, fully executable Python scripts (`src/`) and notebook capable of running top-to-bottom in seconds.

---

## 5. Strategic Prioritization Workflow
1. **Fleet Selection**: Evaluate candidate EV models against market visibility, dealer presence, multi-source coverage, and catalogue availability. Enforce brand diversity (>= 2 unique manufacturers).
2. **Factor Scoring (0–100 Scale)**: Compute Demand (30%), Compatibility (25%), Scarcity (20%), Practicality (15%), and Confidence (10%) for every selected vehicle × part category.
3. **No Synthetic Imputation**: Missing empirical attributes remain NaN; weights are dynamically re-normalized over observed factors, and weight coverage is explicitly logged.
4. **Compatibility Knock-Out Gate**: Any component with compatibility score < 40 is immediately disqualified (importing misfitting components is a catastrophic commercial loss).
5. **Fleet Weighting & Aggregate Ranking**: Weight vehicle scores by market visibility share, calculate aggregate part scores, and rank.
6. **Stress Testing**: Evaluate 4 strategic alternative weighting profiles, 2,000 Dirichlet Monte Carlo simulations, leave-one-vehicle-out checks, and opportunity-versus-ease quadrant mapping.
7. **Categorization**: Classify each part's recommendation stability as *robust* (>= 80% Top-5 probability), *probable* (50–80%), or *sensitive* (< 50%).

---

## 6. Executive Presentation Structure (7 Minutes)
1. **Commercial Context & Problem Definition (45s)**: Ethiopian EV import landscape, foreign currency availability, and inventory holding risks.
2. **Fleet Selection Rationale (60s)**: Why Toyota bZ4X, BYD Yuan Up, and VW ID.4 dominate visibility and distributor presence; addressing the "listings != sales" distinction.
3. **Evidence Architecture & Cleaning (60s)**: Source tiers, missingness profiling, duplicate filtering, and relational schema.
4. **Scoring Model & Knock-Out Gate (90s)**: Mathematical formulation, engineering baseline justifications, and fitment risk prevention.
5. **Top 5 Recommended Parts (60s)**: In-depth rationale for Cabin-Air Filters, Brake Pads, Brake Discs, Wiper Blades, and Shock Absorbers.
6. **Robustness & Sensitivity Analysis (60s)**: Monte Carlo results proving Top-5 stability under shifting capital priorities.
7. **Implementation Roadmap & Risk Mitigation (45s)**: Phased trial batch procurement, supplier contracting, and exchange rate hedge strategies.

