from crud.base import CRUDBase
from models.posts import Post, PostImage
from schemas.posts import PostCreateInSchema, PostImageUpdate, PostUpdateSchema

CRUDPost = CRUDBase[Post, PostCreateInSchema, PostUpdateSchema]
crud_post = CRUDPost(Post)

CRUDPostImage = CRUDBase[PostImage, PostImageUpdate, PostImageUpdate]
crud_postimage = CRUDPost(PostImage)
