CREATE TABLE IF NOT EXISTS queries (
    query_id        TEXT PRIMARY KEY,
    topic           TEXT NOT NULL,
    prompt_text     TEXT NOT NULL,
    is_variant      INTEGER NOT NULL DEFAULT 0,
    variant_of      TEXT,
    zone            TEXT NOT NULL DEFAULT '',
    query_type      TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL
);

-- The UNIQUE constraint is enforced as a partial index (WHERE quarantined = 0) so that
-- a quarantined row and a fresh replacement row can coexist for the same slot.
-- New databases get the partial index directly; existing databases are migrated by
-- scripts/migrate_v2.py which recreates this table.
CREATE TABLE IF NOT EXISTS runs (
    run_id              TEXT PRIMARY KEY,
    query_id            TEXT NOT NULL REFERENCES queries(query_id),
    engine              TEXT NOT NULL,
    model_version       TEXT NOT NULL,
    run_number          INTEGER NOT NULL,
    month               TEXT NOT NULL,
    prompt_sent         TEXT NOT NULL,
    response_text       TEXT NOT NULL,
    input_tokens        INTEGER NOT NULL,
    output_tokens       INTEGER NOT NULL,
    cost_usd            REAL NOT NULL,
    ran_at              TEXT NOT NULL,
    error               TEXT,
    extraction_version  TEXT NOT NULL DEFAULT 'v1',
    citations_extracted INTEGER NOT NULL DEFAULT 0,
    quarantined         INTEGER NOT NULL DEFAULT 0,
    quarantine_reason   TEXT
);

-- Partial unique index: only one active (non-quarantined) run per slot.
CREATE UNIQUE INDEX IF NOT EXISTS idx_runs_active
    ON runs(query_id, engine, run_number, month) WHERE quarantined = 0;

CREATE TABLE IF NOT EXISTS citations (
    citation_id             TEXT PRIMARY KEY,
    run_id                  TEXT NOT NULL REFERENCES runs(run_id),
    url                     TEXT NOT NULL,
    title                   TEXT,
    position                INTEGER NOT NULL,
    domain                  TEXT NOT NULL,
    cited_at                TEXT NOT NULL,
    domain_v2               TEXT,
    normalization_version   TEXT NOT NULL DEFAULT 'v1'
);

CREATE TABLE IF NOT EXISTS costs (
    cost_id         TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    engine          TEXT NOT NULL,
    month           TEXT NOT NULL,
    cost_usd        REAL NOT NULL,
    recorded_at     TEXT NOT NULL
);

-- All report and pipeline queries should use this view so quarantined rows are
-- automatically excluded without requiring every query to repeat the filter.
CREATE VIEW IF NOT EXISTS runs_active AS
    SELECT * FROM runs WHERE quarantined = 0;
