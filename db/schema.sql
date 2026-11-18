PRAGMA foreign_keys = ON;

CREATE TABLE source (
    source_id           TEXT PRIMARY KEY,
    source_name         TEXT NOT NULL,
    url                 TEXT NOT NULL,
    source_type         TEXT NOT NULL CHECK (source_type IN
                          ('marketplace','distributor','catalogue','regulator','supplier','other')),
    publisher_identity  TEXT,                       -- who publishes it (manufacturer, dealer, anonymous seller...)
    reliability_tier    TEXT NOT NULL CHECK (reliability_tier IN ('A','B','C')),
    market_scope        TEXT NOT NULL CHECK (market_scope IN ('Ethiopia','Regional','Global','US')),
    accessed_on         DATE NOT NULL,
    caveat              TEXT
);

CREATE TABLE vehicle_model (
    vehicle_id          TEXT PRIMARY KEY,           -- e.g. BYD_SEAGULL
    make                TEXT NOT NULL,
    model               TEXT NOT NULL,
    segment             TEXT,
    selected_flag       INTEGER NOT NULL DEFAULT 0 CHECK (selected_flag IN (0,1)),
    selection_rationale TEXT
);

CREATE TABLE part_category (
    part_id                 TEXT PRIMARY KEY,
    part_name               TEXT NOT NULL UNIQUE,
    function_desc           TEXT,
    demand_class            TEXT NOT NULL CHECK (demand_class IN ('consumable','wear','collision')),
    replacement_freq_score  INTEGER NOT NULL CHECK (replacement_freq_score BETWEEN 1 AND 5), -- analyst judgement
    logistics_score         INTEGER NOT NULL CHECK (logistics_score BETWEEN 1 AND 5),        -- 5 = easy to ship/store
    rubric_rationale        TEXT NOT NULL
);

CREATE TABLE vehicle_listing (                      -- marketplace / distributor VISIBILITY evidence (not sales)
    listing_id      TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL REFERENCES source(source_id),
    vehicle_id      TEXT REFERENCES vehicle_model(vehicle_id),   -- NULL = not a candidate model
    listing_url     TEXT,
    collected_on    DATE NOT NULL,
    date_status     TEXT NOT NULL CHECK (date_status IN ('observed','imputed_from_source_log')),
    raw_title       TEXT,
    model_year      INTEGER,
    price_etb       REAL,
    price_status    TEXT NOT NULL CHECK (price_status IN
                      ('observed','converted_fx','price_on_request','missing','unparseable','fx_missing')),
    mileage_km      REAL,
    condition       TEXT CHECK (condition IN ('new','used','unknown')),
    location        TEXT,
    is_duplicate    INTEGER NOT NULL DEFAULT 0 CHECK (is_duplicate IN (0,1)),
    duplicate_of    TEXT,
    outlier_flag    INTEGER NOT NULL DEFAULT 0 CHECK (outlier_flag IN (0,1))
);

CREATE TABLE parts_catalog_evidence (               -- fitment / OEM number / supplier price
    evidence_id     TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL REFERENCES source(source_id),
    vehicle_id      TEXT NOT NULL REFERENCES vehicle_model(vehicle_id),
    part_id         TEXT NOT NULL REFERENCES part_category(part_id),
    collected_on    DATE NOT NULL,
    date_status     TEXT NOT NULL CHECK (date_status IN ('observed','imputed_from_source_log')),
    oem_part_number TEXT,                           -- normalised (upper-case, no spaces/dashes)
    fitment_status  TEXT NOT NULL CHECK (fitment_status IN
                      ('confirmed_oem','catalogue_fit','interchange_inferred','unverified','not_found')),
    price_usd       REAL,
    price_etb       REAL,
    price_status    TEXT NOT NULL CHECK (price_status IN
                      ('observed','converted_fx','price_on_request','missing','unparseable','fx_missing')),
    availability    TEXT,
    raw_text        TEXT
);

CREATE TABLE search_log (                           -- distinguishes "0 found" from "not searched"
    search_id       TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL REFERENCES source(source_id),
    vehicle_id      TEXT NOT NULL REFERENCES vehicle_model(vehicle_id),
    part_id         TEXT NOT NULL REFERENCES part_category(part_id),
    query_text      TEXT NOT NULL,
    performed_on    DATE NOT NULL,
    n_results_seen  INTEGER NOT NULL CHECK (n_results_seen >= 0)
);

CREATE TABLE local_part_listing (                   -- Ethiopian market supply evidence for parts
    listing_id      TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL REFERENCES source(source_id),
    vehicle_id      TEXT NOT NULL REFERENCES vehicle_model(vehicle_id),
    part_id         TEXT NOT NULL REFERENCES part_category(part_id),
    listing_url     TEXT,
    collected_on    DATE NOT NULL,
    raw_title       TEXT,
    price_etb       REAL,
    price_status    TEXT NOT NULL CHECK (price_status IN
                      ('observed','converted_fx','price_on_request','missing','unparseable','fx_missing')),
    condition       TEXT CHECK (condition IN ('new','used','unknown')),
    location        TEXT,
    is_duplicate    INTEGER NOT NULL DEFAULT 0 CHECK (is_duplicate IN (0,1)),
    duplicate_of    TEXT
);

CREATE TABLE failure_evidence (                     -- NHTSA complaints / recalls (US-market proxy)
    evidence_id         TEXT PRIMARY KEY,
    source_id           TEXT NOT NULL REFERENCES source(source_id),
    vehicle_id          TEXT NOT NULL REFERENCES vehicle_model(vehicle_id),
    model_year          INTEGER,
    record_type         TEXT NOT NULL CHECK (record_type IN ('complaint','recall')),
    external_record_id  TEXT,
    component_raw       TEXT,
    part_id             TEXT REFERENCES part_category(part_id),   -- NULL = component not mappable to a part
    mapping_confidence  TEXT NOT NULL CHECK (mapping_confidence IN ('direct','indirect','unmapped')),
    mapping_weight      REAL NOT NULL DEFAULT 1.0,                -- split weight when 1 component -> several parts
    collected_on        DATE NOT NULL,
    summary_text        TEXT
);

CREATE TABLE fx_rate (
    rate_date       DATE NOT NULL,
    currency        TEXT NOT NULL,
    etb_per_unit    REAL NOT NULL CHECK (etb_per_unit > 0),
    source_url      TEXT NOT NULL,
    PRIMARY KEY (rate_date, currency)
);

CREATE TABLE data_issue_log (                       -- every cleaning decision is recorded
    issue_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name      TEXT NOT NULL,
    record_id       TEXT,
    field_name      TEXT,
    issue_type      TEXT NOT NULL,
    treatment       TEXT NOT NULL,
    detail          TEXT
);

CREATE TABLE score_run (
    run_id          TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    weights_json    TEXT NOT NULL,
    vehicle_weights_json TEXT NOT NULL,
    notes           TEXT
);

CREATE TABLE part_score (                           -- factor scores per vehicle x part (0-100)
    run_id          TEXT NOT NULL REFERENCES score_run(run_id),
    vehicle_id      TEXT NOT NULL REFERENCES vehicle_model(vehicle_id),
    part_id         TEXT NOT NULL REFERENCES part_category(part_id),
    demand          REAL,
    scarcity        REAL,
    compatibility   REAL,
    practicality    REAL,
    confidence      REAL,
    total_score     REAL,
    weight_coverage REAL,
    PRIMARY KEY (run_id, vehicle_id, part_id)
);

CREATE TABLE part_rank (                            -- final ranking per run
    run_id          TEXT NOT NULL REFERENCES score_run(run_id),
    part_id         TEXT NOT NULL REFERENCES part_category(part_id),
    final_score     REAL NOT NULL,
    rank            INTEGER NOT NULL,
    weight_coverage REAL,
    PRIMARY KEY (run_id, part_id)
);

CREATE INDEX ix_vlisting_vehicle ON vehicle_listing(vehicle_id, is_duplicate);
CREATE INDEX ix_catalog_vp       ON parts_catalog_evidence(vehicle_id, part_id);
CREATE INDEX ix_local_vp         ON local_part_listing(vehicle_id, part_id);
CREATE INDEX ix_fail_vp          ON failure_evidence(vehicle_id, part_id);
