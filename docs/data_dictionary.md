# Data Dictionary — EV Spare-Parts Prioritization

This data dictionary defines schemas, types, valid values, and directory locations for all raw, reference, cleaned, scored, and audit datasets in the project.

---

## 1. Raw Datasets (`data/raw/`)

All raw evidence files are immutable and preserved in UTF-8 encoding. Empty fields represent unavailable observations (never imputed with `0`, `N/A`, or `-`).

### `sources_log.csv` (Audit Register of Information Sources)
| Column | Type | Description | Valid Values / Examples |
|---|---|---|---|
| `source_id` | TEXT (PK) | Unique identifier for evidence source | `S01`, `S02`, ..., `S10` |
| `source_name` | TEXT | Common name of the platform or registry | `"Jiji.et vehicles"`, `"NHTSA API"` |
| `url` | TEXT | URL of source endpoint or landing page | Full HTTP/HTTPS URL |
| `source_type` | TEXT | Institutional classification of source | `marketplace`, `distributor`, `catalogue`, `regulator` |
| `publisher_identity` | TEXT | Operating entity or publisher name | Named corporation, merchant, or government body |
| `reliability_tier` | TEXT | Credibility grading tier | `A` (authoritative/OEM), `B` (commercial distributor), `C` (unverified peer-to-peer) |
| `market_scope` | TEXT | Geographic jurisdiction | `Ethiopia`, `Regional`, `Global`, `US` |
| `accessed_on` | DATE | Date evidence was collected | `YYYY-MM-DD` |
| `caveat` | TEXT | Evidentiary constraints or sampling limits | Qualitative limitation notes |

### `vehicle_listings_raw.csv` (Classified & Dealer Vehicle Ads)
Columns: `record_id`, `source_id`, `listing_url`, `collected_on`, `raw_title`, `make_raw`, `model_raw`, `year_raw`, `price_raw`, `currency_raw`, `mileage_raw`, `condition_raw`, `location_raw`, `seller_raw`, `posted_date_raw`, `notes`.

### `parts_catalog_raw.csv` (OEM Catalogue & Supplier Fitment Records)
Columns: `record_id`, `source_id`, `source_url`, `collected_on`, `vehicle_raw`, `part_raw`, `oem_part_number_raw`, `description_raw`, `price_raw`, `currency_raw`, `availability_raw`, `fitment_raw`, `notes`.

### `local_search_log_raw.csv` (Targeted Addis Ababa Marketplace Searches)
Columns: `record_id`, `source_id`, `vehicle_raw`, `part_raw`, `query_text`, `performed_on`, `n_results_seen`.
*Note: `n_results_seen = 0` represents an observed absence of local supply (scarcity evidence).*

### `local_parts_listings_raw.csv` (Active Local Merchant Spare-Part Ads)
Columns: `record_id`, `source_id`, `listing_url`, `collected_on`, `raw_title`, `vehicle_raw`, `part_raw`, `price_raw`, `currency_raw`, `condition_raw`, `location_raw`, `seller_raw`.

### `nhtsa_records_raw.csv` (US DOT NHTSA Safety Defects & Recalls)
Columns: `record_type`, `external_record_id`, `make`, `model`, `model_year`, `component_raw`, `summary_text`, `collected_on`, `request_url`.
*Populated via `src/scrapers/fetch_nhtsa.py`.*

### Scraped JSON Caches (`data/raw/scraped_json/`)
* `adey/`: Raw crawler response payloads for Adey Market EV listings.
* `gezat/`: Raw crawler response payloads for Gezat Motors catalogue items.
* `jiji/`: Raw API JSON records for Jiji Ethiopia vehicles and parts.
* `nhtsa/`: Untouched API response JSONs for safety complaints and recalls.

---

## 2. External Reference Data (`data/external/`)

### `fx_rates.csv` (Foreign Exchange Conversion Benchmarks)
| Column | Type | Description |
|---|---|---|
| `rate_date` | DATE | Effective date of NBE exchange quotation (`YYYY-MM-DD`) |
| `currency` | TEXT | ISO currency code (`USD`, `CNY`) |
| `etb_per_unit` | REAL | ETB per foreign currency unit (commercial mid-rate) |
| `source_url` | TEXT | Official citation URL (National Bank of Ethiopia) |

---

## 3. Cleaned Tables (`data/processed/cleaned/`)

Cleaned, standardized domain tables loaded directly into the SQLite relational database (`db/ev_parts.db`).

* **`vehicle_listings_clean.csv`**: Deduplicated and standardized vehicle listings (`listing_id`, `source_id`, `vehicle_id`, `listing_url`, `collected_on`, `date_status`, `raw_title`, `model_year`, `price_etb`, `price_status`, `mileage_km`, `condition`, `location`, `is_duplicate`, `duplicate_of`, `outlier_flag`).
* **`parts_catalog_clean.csv`**: Verified catalogue fitment records (`evidence_id`, `source_id`, `vehicle_id`, `part_id`, `oem_part_number`, `description`, `fitment_status`, `price_usd`, `price_etb`, `price_status`, `availability`, `raw_text`).
* **`local_part_listings_clean.csv`**: Standardized local merchant spare part advertisements (`listing_id`, `source_id`, `vehicle_id`, `part_id`, `listing_url`, `collected_on`, `raw_title`, `price_etb`, `price_status`, `condition`, `location`, `is_duplicate`, `duplicate_of`).
* **`search_log_clean.csv`**: Standardized local market search logs (`search_id`, `source_id`, `vehicle_id`, `part_id`, `query_text`, `performed_on`, `n_results_seen`).
* **`failure_evidence_clean.csv`**: Harmonized failure and recall proxies (`evidence_id`, `source_id`, `vehicle_id`, `model_year`, `record_type`, `external_record_id`, `component_raw`, `part_id`, `mapping_confidence`, `mapping_weight`, `collected_on`, `summary_text`).

---

## 4. Scoring & Decision Tables (`data/processed/scoring/`)

* **`vehicle_selection.csv`**: Market visibility score and target fleet selection status across candidate vehicles (`vehicle_id`, `make`, `model`, `segment`, `n_unique_listings`, `n_sources`, `distributor_presence`, `selection_score`, `selected_flag`).
* **`factor_scores_by_vehicle_part.csv`**: 5-factor scoring (0–100) per vehicle–part combination across Demand, Scarcity, Compatibility, Practicality, and Confidence.
* **`final_ranking.csv`**: Overall prioritized ranking across all 10 part categories (`part_id`, `part_name`, `final_score`, `weight_coverage`, `rank`).
* **`sensitivity_scenarios.csv`**: Re-ranked scores under 5 strategic weighting profiles (baseline, slide_example, equal_weights, demand_heavy, scarcity_heavy).
* **`sensitivity_ranks_by_scenario.csv`**: Cross-scenario rank stability matrix (part name by scenario column).
* **`sensitivity_monte_carlo.csv`**: Monte Carlo simulation stability results across 2,000 Dirichlet weight draws (`part_id`, `part_name`, `p_top5`, `stability`).

---

## 5. Audit & Lineage Logs (`data/processed/audit/`)

* **`data_issue_log.csv`**: Exhaustive audit log of all data cleaning interventions (`issue_id`, `table_name`, `record_id`, `field_name`, `issue_type`, `treatment`, `detail`).
* **`raw_missingness_profile.csv`**: Pre-cleaning completeness audit showing column-level missingness counts and percentages.
* **`source_log_with_usage.csv`**: Source register enhanced with empirical citation metrics (`usage_count`, `tables_cited`).

---

## 6. Executive Reports (`reports/`)

* **`top5_recommendation.csv`**: Executive summary table containing the top 5 recommended part categories, scores, Monte Carlo stability ratings, and strategic commercial rationales.
* **`auto_limitations.md`**: Strategic risk analysis detailing evidentiary caveats and regulatory considerations.
* **`figures/`**: 6 High-resolution executive presentation charts (`01_raw_missingness.png` through `06_opportunity_vs_ease.png`).

---

## 7. Categorical Status Codes

| Field | Allowed Values | Definition |
|---|---|---|
| `price_status` | `observed` | Stated in listing or directly calculated via official exchange rate |
| | `price_on_request` | Merchant requires inquiry (typical for B2B distributors) |
| | `missing` | No price information supplied in listing |
| `date_status` | `observed` | Specific ad publication date available |
| | `imputed_from_source_log`| Imputed based on scrape execution date |
| `fitment_status` | `confirmed_oem` | Part number or OEM cross-reference explicitly matches model |
| | `catalogue_fit` | Manufacturer electronic catalogue lists compatibility |
| | `unverified` | Generic or platform-inferred listing requiring VIN check |
| | `not_found` | Searched in catalogue but fitment confirmed absent |
| `mapping_confidence` | `direct` | Direct component match to part category (weight = 1.0) |
| | `indirect` | System-level defect proxy (weight = 0.5) |
| | `unmapped` | Component unrelated to target replacement categories |
| `stability` | `robust` | Top-5 inclusion probability ≥ 80% across 2,000 Dirichlet draws |
| | `probable` | Top-5 inclusion probability between 50% and 80% |
| | `sensitive` | Top-5 inclusion probability < 50% |
