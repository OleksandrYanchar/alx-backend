from dotenv import load_dotenv
import os

load_dotenv()

STATIC_FILES_PATH = os.getenv('STATIC_FILES_PATH') 
MEDIA_FILES_PATH = STATIC_FILES_PATH + 'media/'
