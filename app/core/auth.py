from dataclasses import dataclass
from fastapi import HTTPException, Request, status
from jose import jwt
from jose.exceptions import JWTError
import httpx
from app.core.settings import Settings

@dataclass(frozen=True)
class Principal:
    user_id: str

class Authenticator:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.keys: dict | None = None
        self.client = httpx.AsyncClient(timeout=5.0)

    async def close(self):
        await self.client.aclose()

    async def authenticate(self, request: Request) -> Principal:
        if self.cfg.auth_mode == "dev" and self.cfg.environment != "production":
            return Principal(user_id=self.cfg.dev_user_id)
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
        token = auth[7:]
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256":
                raise ValueError("Unsupported JWT algorithm")
            if self.keys is None:
                response = await self.client.get(self.cfg.jwks_url)
                response.raise_for_status()
                self.keys = response.json()
            key = next((k for k in self.keys.get("keys", []) if k.get("kid") == header.get("kid")), None)
            if key is None:
                self.keys = None  # allows key rotation on next request
                raise ValueError("JWT key not found")
            claims = jwt.decode(token, key, algorithms=["RS256"], issuer=self.cfg.jwt_issuer, audience=self.cfg.jwt_audience)
            subject = claims.get("sub")
            if not subject:
                raise ValueError("Missing subject")
            return Principal(user_id=str(subject))
        except (JWTError, ValueError, KeyError, httpx.HTTPError):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid bearer token") from None
