"""SQLite store for transcripts, findings, overrides."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Assignment, Auditor, AuditRun, DPAEvent, DPAMetrics, Finding, Override, Transcript, TranscriptTurn

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
        try:
            conn.execute("ALTER TABLE assignments ADD COLUMN auditor_notes TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE assignments ADD COLUMN line_item_instructions TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        for stmt in (
            "CREATE TABLE IF NOT EXISTS dpa_events (transcript_id TEXT NOT NULL, timestamp_sec REAL NOT NULL, screen_id TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS dpa_metrics (transcript_id TEXT PRIMARY KEY, call_duration_sec REAL NOT NULL, idle_sec REAL NOT NULL, idle_ratio REAL NOT NULL, max_dwell_sec REAL NOT NULL, dwell_by_screen TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS auditors (id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT)",
            "CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY AUTOINCREMENT, transcript_id TEXT NOT NULL, auditor_id TEXT NOT NULL, assigned_date TEXT NOT NULL, assigned_at TEXT, completed_at TEXT, status TEXT NOT NULL DEFAULT 'pending', auditor_notes TEXT, line_item_instructions TEXT)",
        ):
            conn.execute(stmt)
        conn.commit()
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

    def delete_findings(self, transcript_id: str) -> None:
        conn = self._conn()
        try:
            conn.execute("DELETE FROM findings WHERE transcript_id = ?", (transcript_id,))
            conn.commit()
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

    def update_latest_audit_run(self, transcript_id: str, score: float, severity_band: str, has_critical: bool) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """UPDATE audit_runs SET score = ?, severity_band = ?, has_critical = ?
                   WHERE id = (SELECT id FROM audit_runs WHERE transcript_id = ? ORDER BY run_at DESC LIMIT 1)""",
                (score, severity_band, 1 if has_critical else 0, transcript_id),
            )
            conn.commit()
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

    def insert_dpa_events(self, transcript_id: str, events: list[tuple[float, str]]) -> None:
        """Insert DPA events: list of (timestamp_sec, screen_id). Replaces any existing for this transcript."""
        conn = self._conn()
        try:
            conn.execute("DELETE FROM dpa_events WHERE transcript_id = ?", (transcript_id,))
            for ts, screen_id in events:
                conn.execute(
                    "INSERT INTO dpa_events (transcript_id, timestamp_sec, screen_id) VALUES (?, ?, ?)",
                    (transcript_id, ts, screen_id),
                )
            conn.commit()
        finally:
            conn.close()

    def insert_dpa_metrics(self, m: "DPAMetrics") -> None:
        """Insert or replace DPA metrics for a transcript."""
        conn = self._conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO dpa_metrics (transcript_id, call_duration_sec, idle_sec, idle_ratio, max_dwell_sec, dwell_by_screen)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (m.transcript_id, m.call_duration_sec, m.idle_sec, m.idle_ratio, m.max_dwell_sec, json.dumps(m.dwell_by_screen)),
            )
            conn.commit()
        finally:
            conn.close()

    def get_dpa_events(self, transcript_id: str) -> list[tuple[float, str]]:
        """Return list of (timestamp_sec, screen_id) ordered by time."""
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            rows = conn.execute(
                "SELECT timestamp_sec, screen_id FROM dpa_events WHERE transcript_id = ? ORDER BY timestamp_sec",
                (transcript_id,),
            ).fetchall()
            return [(r["timestamp_sec"], r["screen_id"]) for r in rows]
        finally:
            conn.close()

    def get_dpa_metrics(self, transcript_id: str) -> Optional["DPAMetrics"]:
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            row = conn.execute("SELECT * FROM dpa_metrics WHERE transcript_id = ?", (transcript_id,)).fetchone()
            if not row:
                return None
            return DPAMetrics(
                transcript_id=row["transcript_id"],
                call_duration_sec=row["call_duration_sec"],
                idle_sec=row["idle_sec"],
                idle_ratio=row["idle_ratio"],
                max_dwell_sec=row["max_dwell_sec"],
                dwell_by_screen=json.loads(row["dwell_by_screen"]),
            )
        finally:
            conn.close()

    # --- Audit ops ---
    def list_auditors(self) -> list[Auditor]:
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            rows = conn.execute("SELECT id, name, role FROM auditors ORDER BY name").fetchall()
            return [Auditor(id=r["id"], name=r["name"], role=r.get("role")) for r in rows]
        finally:
            conn.close()

    def insert_auditor(self, a: Auditor) -> None:
        conn = self._conn()
        try:
            conn.execute("INSERT OR REPLACE INTO auditors (id, name, role) VALUES (?, ?, ?)", (a.id, a.name, a.role))
            conn.commit()
        finally:
            conn.close()

    def insert_assignments(self, assignments: list[Assignment]) -> None:
        conn = self._conn()
        try:
            now = datetime.utcnow().isoformat() + "Z"
            for a in assignments:
                conn.execute(
                    """INSERT INTO assignments (transcript_id, auditor_id, assigned_date, assigned_at, completed_at, status, auditor_notes, line_item_instructions)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (a.transcript_id, a.auditor_id, a.assigned_date, a.assigned_at or now, a.completed_at, a.status, getattr(a, "auditor_notes", None), json.dumps(getattr(a, "line_item_instructions", None)) if getattr(a, "line_item_instructions", None) else None),
                )
            conn.commit()
        finally:
            conn.close()

    def get_assignments_for_date(self, assigned_date: str) -> list[Assignment]:
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            rows = conn.execute(
                "SELECT id, transcript_id, auditor_id, assigned_date, assigned_at, completed_at, status, auditor_notes, line_item_instructions FROM assignments WHERE assigned_date = ? ORDER BY auditor_id, transcript_id",
                (assigned_date,),
            ).fetchall()
            return [
                Assignment(id=r["id"], transcript_id=r["transcript_id"], auditor_id=r["auditor_id"], assigned_date=r["assigned_date"], assigned_at=r["assigned_at"], completed_at=r["completed_at"], status=r["status"], auditor_notes=r.get("auditor_notes"), line_item_instructions=json.loads(r["line_item_instructions"]) if (r.get("line_item_instructions") and (r["line_item_instructions"] or "").strip()) else None)
                for r in rows
            ]
        finally:
            conn.close()

    def get_assignments_by_auditor(self, auditor_id: str, assigned_date: str) -> list[Assignment]:
        conn = self._conn()
        conn.row_factory = _dict_factory
        try:
            rows = conn.execute(
                "SELECT id, transcript_id, auditor_id, assigned_date, assigned_at, completed_at, status, auditor_notes, line_item_instructions FROM assignments WHERE auditor_id = ? AND assigned_date = ? ORDER BY status, transcript_id",
                (auditor_id, assigned_date),
            ).fetchall()
            return [
                Assignment(id=r["id"], transcript_id=r["transcript_id"], auditor_id=r["auditor_id"], assigned_date=r["assigned_date"], assigned_at=r["assigned_at"], completed_at=r["completed_at"], status=r["status"], auditor_notes=r.get("auditor_notes"), line_item_instructions=json.loads(r["line_item_instructions"]) if (r.get("line_item_instructions") and (r["line_item_instructions"] or "").strip()) else None)
                for r in rows
            ]
        finally:
            conn.close()

    def get_transcript_ids_assigned_on_date(self, assigned_date: str) -> set[str]:
        conn = self._conn()
        try:
            rows = conn.execute("SELECT transcript_id FROM assignments WHERE assigned_date = ?", (assigned_date,)).fetchall()
            return {r[0] for r in rows}
        finally:
            conn.close()

    def volume_completed_yesterday(self) -> int:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM assignments WHERE status = 'completed' AND date(completed_at) = date('now', '-1 day')"
            ).fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    def volume_completed_today(self) -> int:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM assignments WHERE status = 'completed' AND date(completed_at) = date('now')"
            ).fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    def update_assignment_line_item_instructions(self, assignment_id: int, instructions: dict) -> None:
        conn = self._conn()
        try:
            conn.execute("UPDATE assignments SET line_item_instructions = ? WHERE id = ?", (json.dumps(instructions) if instructions else None, assignment_id))
            conn.commit()
        finally:
            conn.close()

    def mark_assignment_completed(self, assignment_id: int, auditor_notes: Optional[str] = None) -> None:
        conn = self._conn()
        try:
            now = datetime.utcnow().isoformat() + "Z"
            conn.execute(
                "UPDATE assignments SET completed_at = ?, status = 'completed', auditor_notes = COALESCE(?, auditor_notes) WHERE id = ?",
                (now, (auditor_notes or "").strip() or None, assignment_id),
            )
            conn.commit()
        finally:
            conn.close()
