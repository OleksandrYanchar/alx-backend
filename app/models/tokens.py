from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from datetime import datetime
from db.db import Base  # Assuming this is the base declarative class


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    blacklisted_on: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<BlacklistedToken token={self.token}>"
