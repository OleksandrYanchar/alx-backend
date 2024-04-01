from typing import Optional, List
from sqlalchemy import DateTime, String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from models.users import Users
from db.db import Base
from datetime import datetime




class BugReport(Base):
    __tablename__ = "bugreports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str] = mapped_column(String)
    time_stamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    is_closed: Mapped[Boolean] = mapped_column(Boolean, default=False)
    is_vip: Mapped[Boolean] = mapped_column(Boolean, default=False)
    closed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    closed_by: Mapped["Users"] = relationship("Users", foreign_keys=[closed_by_id])
    comments: Mapped[List["BugReportComment"]] = relationship("BugReportComment", back_populates="bug_report")

class BugReportComment(Base):
    __tablename__ = "bugreportcomments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bug_report_id: Mapped[int] = mapped_column(ForeignKey('bugreports.id'), nullable=False)
    body: Mapped[str] = mapped_column(String)
    time_stamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now())
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    bug_report: Mapped["BugReport"] = relationship("BugReport", back_populates="comments")
    user: Mapped["Users"] = relationship("Users", back_populates="comments")