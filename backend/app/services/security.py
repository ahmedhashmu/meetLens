"""Supabase ke login token (JWT) ko verify karta hai.

Login aur signup frontend par Supabase karta hai. Frontend har request ke saath
`Authorization: Bearer <access_token>` bhejta hai, aur backend yahan check karta
hai ke token asli Supabase ka hai aur expire nahi hua.
"""
from dataclasses import dataclass
from functools import lru_cache

import jwt

from app.config import settings

AUDIENCE = "authenticated"


@dataclass
class TokenUser:
    id: str
    email: str | None


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    base = settings.SUPABASE_URL.rstrip("/")
    return jwt.PyJWKClient(f"{base}/auth/v1/.well-known/jwks.json", cache_keys=True)


def decode_access_token(token: str) -> TokenUser | None:
    """Token valid ho to user wapas karta hai, warna None."""
    try:
        if settings.SUPABASE_JWT_SECRET:
            # Purane Supabase projects (aur tests) — shared secret, HS256
            payload = jwt.decode(
                token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience=AUDIENCE
            )
        elif settings.SUPABASE_URL:
            # Naye projects — public key (ES256 / RS256) Supabase se aati hai
            key = _jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, key.key, algorithms=["ES256", "RS256"], audience=AUDIENCE
            )
        else:
            return None
    except (jwt.PyJWTError, jwt.PyJWKClientError):
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None
    return TokenUser(id=user_id, email=payload.get("email"))
