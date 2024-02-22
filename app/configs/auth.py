from dotenv import load_dotenv
import os

load_dotenv()

SECRET = os.getenv("SECRET")
REFRESH_SECRET = os.getenv('REFRESH_SECRET')
ALGORITHM = os.getenv('ALGORITHM')

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 60 * 24 * 7 # 7 days