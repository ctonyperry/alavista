"""SQLite-based storage for investigation runs."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from alavista.core.models import Evidence, Run, Step, StepExecution


class RunStore:
    """Stores and retrieves investigation runs in SQLite."""

    def __init__(self, db_path: Path):
        """Initialize the run store with a database path."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create runs table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    task TEXT NOT NULL,
                    persona_id TEXT NOT NULL,
                    corpus_id TEXT,
                    plan_json TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_persona ON runs(persona_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)")
            conn.commit()

    def create_run(self, run: Run) -> Run:
        """Create a new run."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO runs (id, status, task, persona_id, corpus_id, plan_json, steps_json, evidence_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.status,
                    run.task,
                    run.persona_id,
                    run.corpus_id,
                    json.dumps([step.model_dump(mode='json') for step in run.plan]),
                    json.dumps([step.model_dump(mode='json') for step in run.steps]),
                    json.dumps([ev.model_dump(mode='json') for ev in run.evidence]),
                    run.created_at.isoformat(),
                    run.updated_at.isoformat(),
                ),
            )
            conn.commit()
        return run

    def get_run(self, run_id: str) -> Run | None:
        """Get a run by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                return None
            return self._row_to_run(row)

    def list_runs(self, persona_id: str | None = None, limit: int = 100) -> list[Run]:
        """List runs, optionally filtered by persona."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if persona_id:
                rows = conn.execute(
                    "SELECT * FROM runs WHERE persona_id = ? ORDER BY created_at DESC LIMIT ?",
                    (persona_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [self._row_to_run(row) for row in rows]

    def update_run(self, run: Run) -> Run:
        """Update an existing run."""
        run.updated_at = datetime.now(UTC)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = ?, plan_json = ?, steps_json = ?, evidence_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    run.status,
                    json.dumps([step.model_dump(mode='json') for step in run.plan]),
                    json.dumps([step.model_dump(mode='json') for step in run.steps]),
                    json.dumps([ev.model_dump(mode='json') for ev in run.evidence]),
                    run.updated_at.isoformat(),
                    run.id,
                ),
            )
            conn.commit()
        return run

    def _row_to_run(self, row: sqlite3.Row) -> Run:
        """Convert database row to Run model."""
        return Run(
            id=row["id"],
            status=row["status"],
            task=row["task"],
            persona_id=row["persona_id"],
            corpus_id=row["corpus_id"],
            plan=[Step(**step) for step in json.loads(row["plan_json"])],
            steps=[StepExecution(**step) for step in json.loads(row["steps_json"])],
            evidence=[Evidence(**ev) for ev in json.loads(row["evidence_json"])],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
