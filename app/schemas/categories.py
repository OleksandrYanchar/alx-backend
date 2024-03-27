from pydantic import BaseModel


class CreateCategorySchema(BaseModel):

    title: str

    class Config:
        from_attributes = True


class UpdateCategorySchema(BaseModel):

    title: str

    class Config:
        from_attributes = True


class CategoryInfoSchema(BaseModel):

    id: int
    title: str
    slug: str

    class Config:
        from_attributes = True


class CreateSubCategorySchema(BaseModel):

    category: str

    title: str

    class Config:
        from_attributes = True


class SubCategoryInfoSchema(BaseModel):

    id: int
    title: str
    slug: str

    class Config:
        from_attributes = True


class SubCategoryCrateInfoSchema(BaseModel):

    id: int
    title: str
    category: str
    slug: str

    class Config:
        from_attributes = True
