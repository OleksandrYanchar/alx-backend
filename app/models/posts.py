from sqlalchemy import event
from sqlalchemy import String, UUID, ForeignKey, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from db.db import Base
from datetime import datetime
import re


class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 
    
    title: Mapped[str] = mapped_column(String(64),unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(128),unique=True, nullable=False)


class SubCategory(Base):
    __tablename__ = "subcategories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) 

    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)

    title: Mapped[str] = mapped_column(String(64),unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(128),unique=True, nullable=False)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), 
    primary_key=True, 
    default=uuid.uuid4)
    
    owner: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))  
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    
    sub_category_id: Mapped[int] = mapped_column(ForeignKey('subcategories.id', ondelete='CASCADE'), nullable=False)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(128),nullable=False)
    price : Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=True)
    is_vip: Mapped[bool] = mapped_column(nullable=False, default=False)


class PostImage(Base):
    __tablename__ = "postimages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post: Mapped[uuid.UUID] = mapped_column(ForeignKey('posts.id', ondelete='CASCADE'))
    image: Mapped[str] = mapped_column(nullable=False)
    
def generate_slug(target, value, oldvalue, initiator):
    if value and (oldvalue is None or value != oldvalue):
        # Basic slug generation: replace spaces with dashes and convert to lowercase
        # You can enhance this function to make slugs more URL-friendly
        target.slug = re.sub(r'[\s]+', '-', value).lower()

# Listen for changes to the 'title' field on Post instances
event.listen(Post.title, 'set', generate_slug, retval=False)