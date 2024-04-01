from sqlalchemy import Boolean, Date, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from db.db import Base
from datetime import date


class Users(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=True)
    email: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    joined_at: Mapped[date] = mapped_column(Date, nullable=False, default=date.today())
    is_activated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    viped_at: Mapped[date] = mapped_column(Date, nullable=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    image: Mapped[str] = mapped_column(String, nullable=False, default="media/avatars/no_avatar.jpg")
    comments = relationship("BugReportComment", back_populates="user")
