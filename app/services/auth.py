from  datetime import datetime, timedelta
from passlib.context import CryptContext
from schemas.users import DataTokenSchema
from configs.auth import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET
from jose import JWTError, jwt
import jwt



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_pass):
    return pwd_context.verify(plain_password, hashed_pass)

async def verify_token_access(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET, algorithms=['HS256'])
        
        # Ensure this matches the key used in the JWT payload
        user_id: str = payload.get("id")  
        if user_id is None:
            raise credentials_exception
        # Assuming DataTokenSchema is defined elsewhere and correctly handles the 'id'
        token_data = DataTokenSchema(id=user_id)
    except JWTError as e:
        print(e)
        raise credentials_exception

    return token_data


async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Ensure the 'id' and 'joined_at' are properly converted to strings
    to_encode.update({"exp": expire, "id": str(data["id"]), "joined_at": data["joined_at"].isoformat()})
    
    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm='HS256')
    return encoded_jwt