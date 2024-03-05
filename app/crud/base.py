from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import func
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]) -> None:
        self._model = model

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = dict(obj_in)
        db_obj = self._model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        return db_obj

    async def get(self, session: AsyncSession, *args, **kwargs) -> Optional[ModelType]:
        result = await session.execute(
            select(self._model).filter(*args).filter_by(**kwargs)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *args, offset: int = 0, limit: int = 100, **kwargs
    ) -> List[ModelType]:
        result = await db.execute(
            select(self._model)
            .filter(*args)
            .filter_by(**kwargs)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(
        self,
        db: AsyncSession,
        *,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        db_obj: Optional[ModelType] = None,
        **kwargs
    ) -> Optional[ModelType]:
        db_obj = db_obj or await self.get(db, **kwargs)
        if db_obj is not None:
            obj_data = db_obj.dict()
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            db.add(db_obj)
            await db.commit()
        return db_obj

    async def delete(
        self, db: AsyncSession, *args, db_obj: Optional[ModelType] = None, **kwargs
    ) -> ModelType:
        db_obj = db_obj or await self.get(db, *args, **kwargs)
        await db.delete(db_obj)
        await db.commit()
        return db_obj


    async def get_multi_filtered(
        self,
        db: AsyncSession,
        *args,
        offset: int = 0,
        limit: int = 100,
        created_start_date: Optional[datetime] = None,
        created_end_date: Optional[datetime] = None,
        is_vip: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        created_at_field_name: str = 'created_at',
        vip_field_name: str = 'is_vip', 
        price_field_name: str = 'price',
        **kwargs
    ) -> List[ModelType]:
        # Build the base query with all conditions but without offset and limit
        query = select(self._model).filter(*args)

        # Apply filters based on provided parameters
        if created_start_date:
            query = query.filter(getattr(self._model, created_at_field_name) >= created_start_date)
        if created_end_date:
            query = query.filter(getattr(self._model, created_at_field_name) <= created_end_date)
        if is_vip is not None:
            query = query.filter(getattr(self._model, vip_field_name) == is_vip)
        if min_price is not None:
            query = query.filter(getattr(self._model, price_field_name) >= min_price)
        if max_price is not None:
            query = query.filter(getattr(self._model, price_field_name) <= max_price)

        # If additional filters are provided via kwargs (ensure they match column names)
        if kwargs:
            query = query.filter_by(**kwargs)

        # Calculate total count before applying offset and limit
        total_count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await db.execute(total_count_query)
        total = total_count_result.scalar_one()

        # Now apply offset and limit to the original query for pagination
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        posts = result.scalars().all()

        return posts, total