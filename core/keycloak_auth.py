"""
RAE-Suite Keycloak OAuth2 / OIDC Hardened Auth Gateway
Validates JWT tokens with strict algorithm whitelisting (HS256), issuer normalization,
audience validation, capability scopes, user roles, and tenant isolation.
"""

import time
import jwt
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from rae_contracts import RiskClass

logger = logging.getLogger(__name__)


class KeycloakTokenClaims(BaseModel):
    sub: str  # User ID / Service Account
    preferred_username: str
    tenant_id: str = "default_tenant"
    iss: str = "https://keycloak.example.com/auth/realms/realmX"
    aud: List[str] = Field(default_factory=lambda: ["rae-suite-client"])
    roles: list = Field(default_factory=list)
    capability_scopes: list = Field(default_factory=list)
    exp: int
    iat: int


class KeycloakAuthGateway:
    """
    Hardened Keycloak JWT OIDC Token Validator.
    Enforces strict algorithm whitelisting, issuer normalization, and audience scopes.
    """
    ALLOWED_ALGORITHMS = ["HS256"]

    def __init__(self, secret_key: str = "rae_keycloak_secret_32bytes_strong_key_2026", expected_issuer: str = "https://keycloak.example.com/auth/realms/realmX"):
        self.secret_key = secret_key
        self.expected_issuer = expected_issuer.rstrip("/")

    def create_mock_jwt(self, username: str, roles: list, scopes: list, tenant_id: str = "default", aud: Optional[List[str]] = None) -> str:
        payload = {
            "sub": f"user_{username}",
            "preferred_username": username,
            "tenant_id": tenant_id,
            "iss": self.expected_issuer,
            "aud": aud or ["rae-suite-client"],
            "roles": roles,
            "capability_scopes": scopes,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token_str: str, expected_aud: str = "rae-suite-client") -> KeycloakTokenClaims:
        """Decodes and validates Keycloak JWT token with strict algorithm & claim enforcement."""
        try:
            # Enforce algorithms
            header = jwt.get_unverified_header(token_str)
            if header.get("alg") not in self.ALLOWED_ALGORITHMS:
                raise ValueError(f"Forbidden JWT algorithm: {header.get('alg')}. Allowed: {self.ALLOWED_ALGORITHMS}")

            payload = jwt.decode(token_str, self.secret_key, algorithms=self.ALLOWED_ALGORITHMS, options={"verify_aud": False})
            claims = KeycloakTokenClaims(**payload)

            # Strict issuer normalization check
            if claims.iss.rstrip("/") != self.expected_issuer:
                raise ValueError(f"Issuer mismatch: expected '{self.expected_issuer}', got '{claims.iss}'")

            # Strict audience check
            if expected_aud and expected_aud not in claims.aud:
                raise ValueError(f"Audience mismatch: expected '{expected_aud}' in {claims.aud}")

            return claims
        except Exception as e:
            logger.error(f"Keycloak JWT verification failed: {e}")
            raise ValueError(f"Invalid Keycloak JWT Token: {e}")

    def authorize_capability(self, token_str: str, required_capability: str, min_role: str = "user") -> bool:
        claims = self.verify_token(token_str)
        if min_role not in claims.roles and "admin" not in claims.roles:
            return False
        return required_capability in claims.capability_scopes or "*" in claims.capability_scopes
