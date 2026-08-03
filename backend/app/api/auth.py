"""Small trusted-identity boundary for the MVP API.

Production deployments must put an authenticated gateway in front of this API and
configure it to supply the actor headers. Development retains a named local actor
so the demo remains usable without an identity provider.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import settings

VALID_ROLES = {"intake", "reviewer", "admin"}


@dataclass(frozen=True)
class CurrentActor:
    actor_id: str
    role: str


def get_current_actor(
    x_actor_id: Annotated[str | None, Header()] = None,
    x_actor_role: Annotated[str | None, Header()] = None,
) -> CurrentActor:
    actor_id = (x_actor_id or "").strip()
    role = (x_actor_role or "").strip().lower()
    if not actor_id and not settings.auth_required:
        actor_id = settings.development_actor_id
        role = settings.development_actor_role
    if not actor_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated actor headers are required.",
        )
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Actor role is not recognized.",
        )
    return CurrentActor(actor_id=actor_id, role=role)


def require_roles(*allowed_roles: str):
    def dependency(actor: CurrentActor = Depends(get_current_actor)) -> CurrentActor:
        if actor.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This action is not permitted for the current role.",
            )
        return actor

    return dependency
