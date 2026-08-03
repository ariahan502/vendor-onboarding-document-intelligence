"""Read-only policy catalogue for reviewer and admin governance."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decisioning import PolicyRule
from app.schemas.packages import PolicyRuleSummary


DEFAULT_RULES = (
    ("required_documents", "Required onboarding documents", "high", "contract, w9, and insurance certificate must be present"),
    ("legal_name_match", "Cross-document legal name match", "medium", "contract and W-9 legal names must normalize to the same value"),
    ("tax_id_present", "W-9 tax ID extraction", "medium", "uploaded W-9 must contain a recognizable EIN or SSN"),
    ("scanned_document_review", "Scanned document review", "medium", "PDFs without a text layer require OCR or human review"),
)


def list_policy_rules(db: Session) -> list[PolicyRuleSummary]:
    rules = list(db.scalars(select(PolicyRule).order_by(PolicyRule.rule_code)).all())
    if not rules:
        rules = [
            PolicyRule(
                rule_id=f"policy_{code}", rule_name=name, rule_code=code,
                rule_description=expression, severity=severity, decision_impact="needs_review",
                condition_expression=expression, rule_version="policy-v1", is_active=True,
            )
            for code, name, severity, expression in DEFAULT_RULES
        ]
        db.add_all(rules)
        db.commit()
    return [
        PolicyRuleSummary(
            rule_id=rule.rule_id, rule_code=rule.rule_code, rule_name=rule.rule_name,
            description=rule.rule_description, severity=rule.severity,
            decision_impact=rule.decision_impact, rule_version=rule.rule_version,
            is_active=rule.is_active,
        )
        for rule in rules
    ]
