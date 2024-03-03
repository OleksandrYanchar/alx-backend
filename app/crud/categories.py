from    crud.base import CRUDBase
from schemas.categories import CreateCategorySchema, UpdateCategorySchema
from models.posts import Category, SubCategory


CRUDCategory = CRUDBase[Category, CreateCategorySchema, UpdateCategorySchema]
crud_category = CRUDCategory(Category)


CRUDSubCategory = CRUDBase[SubCategory, CreateCategorySchema, UpdateCategorySchema]
crud_subcategory = CRUDSubCategory(SubCategory)