from typing import Optional
from pydantic import BaseModel

# TokenPayload Schema
# This schema is used for the actual payload in both the access and refresh tokens.
# It could be the same for simplification, or you might differentiate payloads
# if needed for access vs. refresh token purposes.
class TokenPayloadSchema(BaseModel):
    user_id: str
    username: Optional[str] = None
    is_activated: Optional[bool] = None
    is_staff: Optional[bool] = None


# Token Schema
# This schema represents the response for token issuance (login) and refresh operations.
# It includes both the access token and the refresh token.
class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequestSchema(BaseModel):
    token: str
