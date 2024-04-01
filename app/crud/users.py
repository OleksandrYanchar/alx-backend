from crud.base import CRUDBase
from models.users import Users
from schemas.users import UserCreateInSchema, UserPasswordChangeSchema

CRUDUser = CRUDBase[Users, UserCreateInSchema, UserPasswordChangeSchema]
crud_user = CRUDUser(Users)
