"""SQLite store for transcripts, findings, overrides."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import AuditRun, Finding, Override, Transcript, TranscriptTurn

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "vigilantcx.db"


def _dict_factory(cursor, row):
    return {cursor.description[i][0]: row[i] for i in range(len(row))}


def get_store(db_path: Optional[Path] = None) -> "Store":
    path = db_path or DB_PATH
    return Store(path)


class Store:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        schema = (Path(__file__).resolve().parent / "schema.sql").read_text()
        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema)
        try:
            conn.execute("ALTER TABLE audit_runs ADD COLUMN outcome_summary TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        conn.close()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def insert_transcript(self, t: Transcript) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO transcripts (id, persona_id, language, intended_risk_level, scenario_id, expected_findings, turns, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    t.id,
                    t.persona_id,
                    t.language,
                    t.intended_risk_level,
                    t.scenario_id,
                    json.dumps(t.expected_findings),
                    json.dumps([
                        {"speaker": turn.speaker, "text": turn.text, "segment": turn.segment}
                        for turn in t.turns
                    ]),
                    t.created_at or datetime.utcnow().isoformat() + "Z",
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_transcript(self, transcript_id: str) -> Optional[Transcript]:
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            row = conn.execute("SELECT * FROM transcripts WHERE id = ?", (transcript_id,)).fetchone()
            if not row:
                return None
            turns = [
                TranscriptTurn(speaker=u["speaker"], text=u["text"], segment=u.get("segment"))
                for u in json.loads(row["turns"])
            ]
            return Transcript(
                id=row["id"],
                persona_id=row["persona_id"],
                language=row["language"],
                intended_risk_level=row["intended_risk_level"],
                scenario_id=row["scenario_id"],
                expected_findings=json.loads(row["expected_findings"]),
                turns=turns,
                created_at=row["created_at"],
            )
        finally:
            conn.close()

    def list_transcript_ids(self) -> list[str]:
        conn = self._conn()
        try:
            rows = conn.execute("SELECT id FROM transcripts ORDER BY created_at DESC").fetchall()
            return [r[0] for r in rows]
        finally:
            conn.close()

    def insert_findings(self, transcript_id: str, findings: list[Finding]) -> None:
        conn = self._conn()
        try:
            for f in findings:
                conn.execute(
                    """INSERT INTO findings (transcript_id, rule_id, passed, severity, reason, snippet, weight)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (transcript_id, f.rule_id, 1 if f.passed else 0, f.severity, f.reason, f.snippet, f.weight),
                )
            conn.commit()
        finally:
            conn.close()

    def insert_audit_run(self, run: AuditRun) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO audit_runs (transcript_id, score, severity_band, has_critical, run_at, outcome_summary)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (run.transcript_id, run.score, run.severity_band, 1 if run.has_critical else 0, run.run_at or datetime.utcnow().isoformat() + "Z", run.outcome_summary),
            )
            conn.commit()
        finally:
            conn.close()

    def get_findings(self, transcript_id: str) -> list[Finding]:
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            rows = conn.execute("SELECT * FROM findings WHERE transcript_id = ?", (transcript_id,)).fetchall()
            return [
                Finding(
                    id=r["id"],
                    transcript_id=r["transcript_id"],
                    rule_id=r["rule_id"],
                    passed=bool(r["passed"]),
                    severity=r["severity"],
                    reason=r["reason"],
                    snippet=r["snippet"],
                    weight=r["weight"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_latest_audit_run(self, transcript_id: str) -> Optional[AuditRun]:
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            row = conn.execute(
                "SELECT * FROM audit_runs WHERE transcript_id = ? ORDER BY run_at DESC LIMIT 1",
                (transcript_id,),
            ).fetchone()
            if not row:
                return None
            return AuditRun(
                id=row["id"],
                transcript_id=row["transcript_id"],
                score=row["score"],
                severity_band=row["severity_band"],
                has_critical=bool(row["has_critical"]),
                run_at=row["run_at"],
                outcome_summary=row.get("outcome_summary"),
            )
        finally:
            conn.close()

    def add_override(self, o: Override) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """INSERT INTO overrides (transcript_id, finding_id, overridden_by, reason, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (o.transcript_id, o.finding_id, o.overridden_by, o.reason, o.created_at or datetime.utcnow().isoformat() + "Z", o.expires_at),
            )
            conn.commit()
        finally:
            conn.close()

    def get_overrides_for_transcript(self, transcript_id: str) -> list[Override]:
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            rows = conn.execute("SELECT * FROM overrides WHERE transcript_id = ?", (transcript_id,)).fetchall()
            return [
                Override(
                    transcript_id=r["transcript_id"],
                    overridden_by=r["overridden_by"],
                    reason=r["reason"],
                    id=r["id"],
                    finding_id=r["finding_id"],
                    created_at=r["created_at"],
                    expires_at=r["expires_at"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_all_overridden_transcript_ids(self) -> set[str]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT DISTINCT transcript_id FROM overrides WHERE finding_id IS NULL"
            ).fetchall()
            return {r[0] for r in rows}
        finally:
            conn.close()

    def update_audit_run_outcome_summary(self, transcript_id: str, outcome_summary: Optional[str]) -> None:
        """Update the latest audit run for this transcript with an LLM outcome summary."""
        conn = self._conn()
        try:
            conn.execute(
                """UPDATE audit_runs SET outcome_summary = ? WHERE id = (
                    SELECT id FROM audit_runs WHERE transcript_id = ? ORDER BY run_at DESC LIMIT 1
                )""",
                (outcome_summary, transcript_id),
            )
            conn.commit()
        finally:
            conn.close()
