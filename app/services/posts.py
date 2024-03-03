import re
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from crud.categories import crud_category, crud_subcategory
from schemas.categories import CreateCategorySchema, CategoryInfoSchema, CreateSubCategorySchema, SubCategoryCrateInfoSchema


async def clean_title(title: str) -> str:
    title = title.strip().lower()
    title = re.sub(r'[^a-zA-Z\s]', '', title)
    return re.sub("\ +", " ", title)  


async def create_slug(title: str) -> str:
    # Ensure to call .lower() to convert the title to lowercase
    return title.strip().replace(' ', '-').lower()


async def create_category(
    category_data: CreateCategorySchema, 
    db: AsyncSession,
) -> CategoryInfoSchema:
    title = await clean_title(category_data.title)
    slug = await create_slug(title)
    
    if len(title) >64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A category name is too long, max:64, yours is:{len(title)}",
        )

    if len(slug) >128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A category slug is too long, max:128, yours is:{len(slug)}"
        )

    if await crud_category.get(db, title=title):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this title already exists.",
        )
    if await crud_category.get(db, slug=slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this slug already exists.",
        )
    # Prepare the data for category creation
    category_data = category_data.dict()
    category_data['title'] = title
    category_data['slug'] = slug
    
    # Create the new category and ensure it's returned as a model instance or dict
    new_category = await crud_category.create(db, obj_in=category_data)
    
    # Assuming new_category is an ORM model instance
    return CategoryInfoSchema(**new_category.dict())


async def create_subcategory(
    subcategory_data: CreateSubCategorySchema, 
    db: AsyncSession,
) -> SubCategoryCrateInfoSchema:
    title = await clean_title(subcategory_data.title)
    slug = await create_slug(title)
    category = await crud_category.get(db, title=subcategory_data.category)
    
    if len(title) >64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"title is too long, max:64, yours is:{len(title)}",
        )

    if len(slug) >128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"slug is too long, max:128, yours is:{len(slug)}"
        )
        
    if await crud_subcategory.get(db, title=title):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this title already exists.",
        )
    if await crud_subcategory.get(db, slug=slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="this slug already exists.",
        )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This category dosen't exists.",
        )

    subcategory_data_dict = subcategory_data.dict()
    subcategory_data_dict['title'] = title
    subcategory_data_dict['category_id'] = category.id  # Set the correct 'category_id'
    subcategory_data_dict['slug'] = slug

    # Remove the 'category' key which is not needed for creating the SubCategory object
    subcategory_data_dict.pop('category', None)

    # Create the new SubCategory using the 'subcategory_data_dict'
    new_subcategory = await crud_subcategory.create(db, obj_in=subcategory_data_dict)

    # Fetch the category name for including in the SubCategoryInfoSchema
    category_name = category.title

    # Create the SubCategoryInfoSchema, adding the category name
    subcategory_info_data = new_subcategory.dict()
    subcategory_info_data['category'] = category_name

    # Return the SubCategoryInfoSchema instance
    return SubCategoryCrateInfoSchema(**subcategory_info_data)