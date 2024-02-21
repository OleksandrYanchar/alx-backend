from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")

EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

EMAIL_HOST_USERNAME= os.getenv('EMAIL_HOST_USERNAME')