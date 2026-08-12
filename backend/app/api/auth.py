"""Microsoft Entra token boundary for the MVP API.

When authentication is required, the API validates Entra bearer tokens itself and
uses assigned application roles for authorization. Development retains a named
local actor so the demo remains usable without an identity provider.
"""

from dataclasses import dataclass
import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.config import settings

VALID_ROLES = {"intake", "reviewer", "admin"}
bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurrentActor:
    actor_id: str
    role: str


def get_current_actor(
    x_actor_id: Annotated[str | None, Header()] = None,
    x_actor_role: Annotated[str | None, Header()] = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentActor:
    if settings.auth_required:
        return _get_entra_actor(credentials)
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


def _get_entra_actor(credentials: HTTPAuthorizationCredentials | None) -> CurrentActor:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is required.")
    if not settings.entra_tenant_id or not settings.entra_api_audience:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Entra authentication is not configured.")
    try:
        keys = jwt.PyJWKClient(
            f"https://login.microsoftonline.com/{settings.entra_tenant_id}/discovery/v2.0/keys"
        )
        signing_key = keys.get_signing_key_from_jwt(credentials.credentials)
        audiences = [settings.entra_api_audience]
        if settings.entra_api_audience.startswith("api://"):
            audiences.append(settings.entra_api_audience.removeprefix("api://"))
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=audiences,
            issuer=f"https://login.microsoftonline.com/{settings.entra_tenant_id}/v2.0",
        )
    except jwt.PyJWTError as exc:
        logger.warning("Microsoft Entra access-token validation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is invalid.") from exc
    roles = claims.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]
    role = next((candidate.lower() for candidate in roles if candidate.lower() in VALID_ROLES), None)
    actor_id = str(claims.get("oid") or claims.get("sub") or "").strip()
    if not actor_id or not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A recognised Entra application role is required.")
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
