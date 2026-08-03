from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import CurrentActor, require_roles
from app.db.session import get_db
from app.models.evaluation import EvaluationRun

router = APIRouter()


@router.get("/summary")
def evaluation_summary(
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_roles("admin")),
) -> dict[str, float | int | None]:
    """Return aggregate quality metrics without exposing document contents."""
    row = db.execute(
        select(
            func.count(EvaluationRun.eval_run_id),
            func.avg(EvaluationRun.extraction_score),
            func.avg(EvaluationRun.finding_score),
            func.avg(EvaluationRun.routing_score),
            func.avg(EvaluationRun.reviewer_agreement_score),
        )
    ).one()
    return {
        "run_count": row[0],
        "average_extraction_score": float(row[1]) if row[1] is not None else None,
        "average_finding_score": float(row[2]) if row[2] is not None else None,
        "average_routing_score": float(row[3]) if row[3] is not None else None,
        "average_reviewer_agreement_score": float(row[4]) if row[4] is not None else None,
    }
