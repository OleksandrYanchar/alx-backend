from sqlalchemy import String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from db.db import Base
from datetime import datetime

class BugReport(Base):
    __tablename__ = "bugreports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 
    
    user: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))  

    title: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str] = mapped_column(String)
    time_stamp: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    is_closed: Mapped[Boolean] = mapped_column(Boolean, default=False)
    is_vip: Mapped[Boolean] = mapped_column(Boolean,default=False)