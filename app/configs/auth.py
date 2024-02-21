from dotenv import load_dotenv
import os

load_dotenv()

SECRET = os.getenv("SECRET")

ACCESS_TOKEN_EXPIRE_MINUTES = 30