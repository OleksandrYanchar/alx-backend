from sqlalchemy.ext.asyncio import  create_async_engine
from sqlalchemy.orm import DeclarativeBase
from configs.db import DB_HOST,DB_NAME, DB_PASS, DB_PORT, DB_USER 

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL)




class Base(DeclarativeBase):
    pass
