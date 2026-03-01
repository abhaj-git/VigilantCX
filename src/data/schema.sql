-- SQLite schema for VigilantCX

CREATE TABLE IF NOT EXISTS transcripts (
    id TEXT PRIMARY KEY,
    persona_id TEXT NOT NULL,
    language TEXT NOT NULL,
    intended_risk_level TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    expected_findings TEXT NOT NULL,  -- JSON array of rule ids
    turns TEXT NOT NULL,              -- JSON array of {speaker, text, segment}
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id TEXT NOT NULL,
    score REAL NOT NULL,
    severity_band TEXT NOT NULL,
    has_critical INTEGER NOT NULL,
    run_at TEXT,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
);

CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    passed INTEGER NOT NULL,
    severity TEXT NOT NULL,
    reason TEXT NOT NULL,
    snippet TEXT,
    weight REAL,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
);

CREATE TABLE IF NOT EXISTS overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id TEXT NOT NULL,
    finding_id INTEGER,
    overridden_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT,
    expires_at TEXT,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
);

CREATE TABLE IF NOT EXISTS dpa_events (
    transcript_id TEXT NOT NULL,
    timestamp_sec REAL NOT NULL,
    screen_id TEXT NOT NULL,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
);
CREATE TABLE IF NOT EXISTS dpa_metrics (
    transcript_id TEXT PRIMARY KEY,
    call_duration_sec REAL NOT NULL,
    idle_sec REAL NOT NULL,
    idle_ratio REAL NOT NULL,
    max_dwell_sec REAL NOT NULL,
    dwell_by_screen TEXT NOT NULL,
    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
);

CREATE INDEX IF NOT EXISTS idx_findings_transcript ON findings(transcript_id);
CREATE INDEX IF NOT EXISTS idx_overrides_transcript ON overrides(transcript_id);
CREATE INDEX IF NOT EXISTS idx_dpa_events_transcript ON dpa_events(transcript_id);
