"""Service for managing investigation runs."""

import hashlib
from datetime import UTC, datetime

from alavista.core.models import Evidence, Run, Step, StepExecution
from alavista.core.run_store import RunStore


class RunService:
    """
    Manages investigation runs - creating plans and executing steps.

    For Phase 12 MVP, this provides a basic run management framework.
    Future phases will add intelligent planning and autonomous execution.
    """

    def __init__(self, run_store: RunStore):
        """Initialize with a run store."""
        self.run_store = run_store

    def create_run(
        self,
        task: str,
        persona_id: str,
        corpus_id: str | None = None,
        plan: list[Step] | None = None,
    ) -> Run:
        """
        Create a new investigation run.

        Args:
            task: The user's question or investigation goal
            persona_id: ID of the persona conducting the investigation
            corpus_id: Optional primary corpus to investigate
            plan: Optional pre-defined plan of steps. If None, generates a basic plan.

        Returns:
            Created Run object
        """
        # Generate run ID from task + timestamp
        run_id = hashlib.sha256(
            f"{task}:{datetime.now(UTC).isoformat()}".encode()
        ).hexdigest()[:16]

        # Generate basic plan if not provided
        if plan is None:
            plan = self._generate_basic_plan(task, corpus_id)

        # Initialize step executions as pending
        steps = [
            StepExecution(step_index=idx, status="pending")
            for idx in range(len(plan))
        ]

        run = Run(
            id=run_id,
            status="created",
            task=task,
            persona_id=persona_id,
            corpus_id=corpus_id,
            plan=plan,
            steps=steps,
            evidence=[],
        )

        return self.run_store.create_run(run)

    def get_run(self, run_id: str) -> Run | None:
        """Get a run by ID."""
        return self.run_store.get_run(run_id)

    def list_runs(self, persona_id: str | None = None, limit: int = 100) -> list[Run]:
        """List runs, optionally filtered by persona."""
        return self.run_store.list_runs(persona_id=persona_id, limit=limit)

    def cancel_run(self, run_id: str) -> Run:
        """Cancel a running investigation."""
        run = self.run_store.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        run.status = "cancelled"
        return self.run_store.update_run(run)

    def execute_step(
        self, run_id: str, step_index: int, result: dict | None = None
    ) -> Run:
        """
        Execute a single step in the run (manual execution for MVP).

        Args:
            run_id: ID of the run
            step_index: Index of the step to execute
            result: Result data from step execution

        Returns:
            Updated Run object
        """
        run = self.run_store.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        if step_index >= len(run.steps):
            raise ValueError(f"Step index {step_index} out of range")

        # Update step execution
        step_exec = run.steps[step_index]
        if step_exec.status == "pending":
            step_exec.status = "running"
            step_exec.started_at = datetime.now(UTC)

        if result:
            step_exec.status = "completed"
            step_exec.completed_at = datetime.now(UTC)
            step_exec.result = result

            # Extract evidence from result if available
            if "hits" in result:
                for hit in result["hits"][:5]:  # Take top 5
                    evidence = Evidence(
                        document_id=hit.get("document_id", "unknown"),
                        chunk_id=hit.get("chunk_id"),
                        excerpt=hit.get("excerpt", ""),
                        score=hit.get("score", 0.0),
                        source_step=step_index,
                        metadata=hit.get("metadata", {}),
                    )
                    run.evidence.append(evidence)

        # Update run status
        if all(s.status in ["completed", "error"] for s in run.steps):
            run.status = "completed"
        elif any(s.status == "running" for s in run.steps):
            run.status = "running"

        return self.run_store.update_run(run)

    def _generate_basic_plan(self, task: str, corpus_id: str | None) -> list[Step]:
        """
        Generate a basic investigation plan.

        For MVP, this creates a simple single-step search plan.
        Future phases will use LLM-based planning.
        """
        steps = []

        if corpus_id:
            # Basic search step
            steps.append(
                Step(
                    action="search",
                    target=corpus_id,
                    parameters={"query": task, "mode": "hybrid", "k": 20},
                )
            )

        return steps
