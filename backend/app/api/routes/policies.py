from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentActor, require_roles
from app.db.session import get_db
from app.models.decisioning import PolicyRule, PolicyRuleRevision
from app.models.evaluation import EvaluationCase, EvaluationRun
from app.schemas.packages import (
    PolicyRevisionActivationResponse,
    PolicyRevisionCreateRequest,
    PolicyRevisionEvaluationResponse,
    PolicyRevisionEvaluateRequest,
    PolicyRevisionListResponse,
    PolicyRevisionResponse,
    PolicyRevisionSummary,
    PolicyRuleListResponse,
)
from app.services.audit_service import record_audit_event
from app.services.policy_service import list_policy_rules

router = APIRouter()
MINIMUM_EVALUATION_SCORE = Decimal("0.9500")


@router.get("/", response_model=PolicyRuleListResponse)
def list_policies(
    db: Session = Depends(get_db),
    _: CurrentActor = Depends(require_roles("admin")),
) -> PolicyRuleListResponse:
    """Show the active policy catalogue; edits require versioned evaluation work."""
    return PolicyRuleListResponse(rules=list_policy_rules(db))


@router.post("/{rule_id}/revisions", response_model=PolicyRevisionResponse, status_code=status.HTTP_201_CREATED)
def create_policy_revision(rule_id: str, payload: PolicyRevisionCreateRequest, db: Session = Depends(get_db), actor: CurrentActor = Depends(require_roles("admin"))) -> PolicyRevisionResponse:
    rule = db.get(PolicyRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy rule was not found.")
    revision = PolicyRuleRevision(revision_id=f"revision_{uuid4().hex[:12]}", rule_id=rule_id, proposed_expression=payload.proposed_expression.strip(), proposed_severity=payload.proposed_severity.strip().lower(), change_reason=payload.change_reason.strip(), proposed_by=actor.actor_id, status="draft")
    db.add(revision)
    db.commit()
    record_audit_event(db, actor_id=actor.actor_id, actor_role=actor.role, action="policy.revision_created", package_id=None, resource_type="policy_rule_revision", resource_id=revision.revision_id, event_metadata={"rule_id": rule_id})
    return PolicyRevisionResponse(revision_id=revision.revision_id, rule_id=rule_id, status=revision.status)


@router.get("/{rule_id}/revisions", response_model=PolicyRevisionListResponse)
def list_policy_revisions(rule_id: str, db: Session = Depends(get_db), _: CurrentActor = Depends(require_roles("admin"))) -> PolicyRevisionListResponse:
    if db.get(PolicyRule, rule_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy rule was not found.")
    revisions = db.scalars(select(PolicyRuleRevision).where(PolicyRuleRevision.rule_id == rule_id).order_by(PolicyRuleRevision.created_at.desc())).all()
    return PolicyRevisionListResponse(revisions=[_revision_summary(revision) for revision in revisions])


@router.post("/{rule_id}/revisions/{revision_id}/evaluate", response_model=PolicyRevisionEvaluationResponse)
def evaluate_policy_revision(rule_id: str, revision_id: str, payload: PolicyRevisionEvaluateRequest, db: Session = Depends(get_db), actor: CurrentActor = Depends(require_roles("admin"))) -> PolicyRevisionEvaluationResponse:
    revision = _get_revision(db, rule_id, revision_id)
    if revision.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft revisions can be evaluated.")
    now = datetime.now(timezone.utc)
    case = EvaluationCase(eval_case_id=f"eval_case_{uuid4().hex[:12]}", package_id=None, case_name=payload.case_name.strip(), case_slice=payload.case_slice.strip() if payload.case_slice else "policy_revision", expected_fields=None, expected_findings=None, expected_decision=None)
    scores = [Decimal(str(value)) for value in (payload.extraction_score, payload.finding_score, payload.routing_score, payload.reviewer_agreement_score)]
    passed = all(score >= MINIMUM_EVALUATION_SCORE for score in scores)
    run = EvaluationRun(eval_run_id=f"eval_run_{uuid4().hex[:12]}", eval_case_id=case.eval_case_id, run_label=f"policy-revision:{revision.revision_id}", rule_version=f"candidate:{revision.revision_id}", extraction_score=scores[0], finding_score=scores[1], routing_score=scores[2], reviewer_agreement_score=scores[3], run_started_at=now, run_completed_at=now, notes=payload.notes.strip() if payload.notes else None)
    db.add_all([case, run])
    revision.evaluation_run_id = run.eval_run_id
    revision.status = "evaluated" if passed else "rejected"
    db.commit()
    record_audit_event(db, actor_id=actor.actor_id, actor_role=actor.role, action="policy.revision_evaluated", package_id=None, resource_type="policy_rule_revision", resource_id=revision.revision_id, event_metadata={"evaluation_run_id": run.eval_run_id, "passed": passed})
    return PolicyRevisionEvaluationResponse(revision_id=revision.revision_id, rule_id=rule_id, status=revision.status, evaluation_run_id=run.eval_run_id, passed=passed)


@router.post("/{rule_id}/revisions/{revision_id}/activate", response_model=PolicyRevisionActivationResponse)
def activate_policy_revision(rule_id: str, revision_id: str, db: Session = Depends(get_db), actor: CurrentActor = Depends(require_roles("admin"))) -> PolicyRevisionActivationResponse:
    revision = _get_revision(db, rule_id, revision_id)
    if revision.status != "evaluated" or not revision.evaluation_run_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only a passing evaluated revision can be activated.")
    rule = db.get(PolicyRule, rule_id)
    assert rule is not None
    rule.condition_expression = revision.proposed_expression
    rule.severity = revision.proposed_severity
    rule.rule_version = _next_rule_version(rule.rule_version)
    revision.status = "active"
    db.commit()
    record_audit_event(db, actor_id=actor.actor_id, actor_role=actor.role, action="policy.revision_activated", package_id=None, resource_type="policy_rule_revision", resource_id=revision.revision_id, event_metadata={"rule_id": rule_id, "rule_version": rule.rule_version})
    return PolicyRevisionActivationResponse(revision_id=revision.revision_id, rule_id=rule_id, status=revision.status, rule_version=rule.rule_version)


def _get_revision(db: Session, rule_id: str, revision_id: str) -> PolicyRuleRevision:
    revision = db.get(PolicyRuleRevision, revision_id)
    if revision is None or revision.rule_id != rule_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy revision was not found.")
    return revision


def _revision_summary(revision: PolicyRuleRevision) -> PolicyRevisionSummary:
    return PolicyRevisionSummary(revision_id=revision.revision_id, rule_id=revision.rule_id, status=revision.status, proposed_expression=revision.proposed_expression, proposed_severity=revision.proposed_severity, change_reason=revision.change_reason, proposed_by=revision.proposed_by, evaluation_run_id=revision.evaluation_run_id, created_at=revision.created_at)


def _next_rule_version(current: str) -> str:
    prefix, separator, number = current.rpartition("v")
    if separator and number.isdigit():
        return f"{prefix}v{int(number) + 1}"
    return f"{current}-v2"
