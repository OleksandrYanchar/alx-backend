from crud.base import CRUDBase
from models.posts import Post 
from schemas.posts import PostCreateInSchema, PostUpdateSchema

CRUDPost = CRUDBase[Post, PostCreateInSchema, PostUpdateSchema]
crud_post = CRUDPost(Post)

