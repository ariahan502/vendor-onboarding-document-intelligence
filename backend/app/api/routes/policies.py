from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import CurrentActor, require_roles
from app.db.session import get_db
from app.schemas.packages import PolicyRuleListResponse
from app.services.policy_service import list_policy_rules

router = APIRouter()


@router.get("/", response_model=PolicyRuleListResponse)
def list_policies(
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_roles("admin")),
) -> PolicyRuleListResponse:
    """Show the active policy catalogue; edits require versioned evaluation work."""
    return PolicyRuleListResponse(rules=list_policy_rules(db))
