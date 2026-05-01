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

CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    query_id        TEXT NOT NULL REFERENCES queries(query_id),
    engine          TEXT NOT NULL,
    model_version   TEXT NOT NULL,
    run_number      INTEGER NOT NULL,
    month           TEXT NOT NULL,
    prompt_sent     TEXT NOT NULL,
    response_text   TEXT NOT NULL,
    input_tokens    INTEGER NOT NULL,
    output_tokens   INTEGER NOT NULL,
    cost_usd        REAL NOT NULL,
    ran_at          TEXT NOT NULL,
    error           TEXT,
    UNIQUE(query_id, engine, run_number, month)
);

CREATE TABLE IF NOT EXISTS citations (
    citation_id     TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    url             TEXT NOT NULL,
    title           TEXT,
    position        INTEGER NOT NULL,
    domain          TEXT NOT NULL,
    cited_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS costs (
    cost_id         TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs(run_id),
    engine          TEXT NOT NULL,
    month           TEXT NOT NULL,
    cost_usd        REAL NOT NULL,
    recorded_at     TEXT NOT NULL
);
