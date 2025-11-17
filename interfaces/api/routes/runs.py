"""Runs routes (stub for Phase 12 UI)."""

from fastapi import APIRouter

router = APIRouter(tags=["runs"])


@router.get("/runs")
def list_runs():
    """
    List investigation runs (stub).

    This is a placeholder endpoint for Phase 12 UI.
    Full investigation run tracking will be implemented in a future phase.
    """
    return []


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    """
    Get a specific investigation run (stub).

    This is a placeholder endpoint for Phase 12 UI.
    Full investigation run tracking will be implemented in a future phase.
    """
    return {
        "id": run_id,
        "status": "not_implemented",
        "message": "Investigation run tracking not yet implemented"
    }
