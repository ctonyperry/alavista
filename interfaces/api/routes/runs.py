"""Investigation runs routes."""

from fastapi import APIRouter, HTTPException

from alavista.core.container import Container
from alavista.core.models import Step
from interfaces.api.schemas import (
    CreateRunRequest,
    RunDetail,
    RunSummary,
    ExecuteStepRequest,
)

router = APIRouter(tags=["runs"])


@router.post("/runs", response_model=RunDetail)
def create_run(request: CreateRunRequest):
    """
    Create a new investigation run.

    The run will be created with a basic plan if not provided.
    """
    run_service = Container.get_run_service()

    # Convert plan if provided
    plan = None
    if request.plan:
        plan = [Step(**step_dict) for step_dict in request.plan]

    run = run_service.create_run(
        task=request.task,
        persona_id=request.persona_id,
        corpus_id=request.corpus_id,
        plan=plan,
    )

    return _run_to_detail(run)


@router.get("/runs", response_model=list[RunSummary])
def list_runs(persona_id: str | None = None, limit: int = 100):
    """
    List investigation runs.

    Optionally filter by persona_id.
    """
    run_service = Container.get_run_service()
    runs = run_service.list_runs(persona_id=persona_id, limit=limit)

    return [
        RunSummary(
            id=run.id,
            status=run.status,
            task=run.task,
            persona_id=run.persona_id,
            created_at=run.created_at,
            step_count=len(run.steps),
            evidence_count=len(run.evidence),
        )
        for run in runs
    ]


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str):
    """Get a specific investigation run."""
    run_service = Container.get_run_service()
    run = run_service.get_run(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return _run_to_detail(run)


@router.post("/runs/{run_id}/step", response_model=RunDetail)
def execute_step(run_id: str, request: ExecuteStepRequest):
    """
    Execute a step in the investigation run.

    For MVP, this is manual step execution with provided results.
    Future phases will add autonomous execution.
    """
    run_service = Container.get_run_service()

    try:
        run = run_service.execute_step(
            run_id=run_id,
            step_index=request.step_index,
            result=request.result,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _run_to_detail(run)


@router.post("/runs/{run_id}/cancel", response_model=RunDetail)
def cancel_run(run_id: str):
    """Cancel a running investigation."""
    run_service = Container.get_run_service()

    try:
        run = run_service.cancel_run(run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return _run_to_detail(run)


def _run_to_detail(run):
    """Convert Run model to RunDetail schema."""
    from alavista.core.models import Run

    return RunDetail(
        id=run.id,
        status=run.status,
        task=run.task,
        persona_id=run.persona_id,
        corpus_id=run.corpus_id,
        plan=[step.model_dump() for step in run.plan],
        steps=[step.model_dump() for step in run.steps],
        evidence=[ev.model_dump() for ev in run.evidence],
        created_at=run.created_at,
        updated_at=run.updated_at,
    )
