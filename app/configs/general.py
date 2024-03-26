import logging
from dotenv import load_dotenv
import os

load_dotenv()

STATIC_FILES_PATH = os.getenv('STATIC_FILES_PATH') 
MEDIA_FILES_PATH = STATIC_FILES_PATH + 'media/'

AVATARS_DIR = f'{MEDIA_FILES_PATH}avatars/'
POSTS_PICTURES_DIR = f'{MEDIA_FILES_PATH}posts/'

ADMINS_EMAILS: str = os.getenv('ADMINS_EMAILS')

ADMINS_EMAILS: str = os.getenv('ADMINS_EMAILS', '')

admins_emails: list[str] = [
    email.strip() for email in ADMINS_EMAILS.split(",") if email.strip()
]

def setup_logger(STATIC_FILES_PATH):
    LOG_FILENAME = os.getenv('LOG_FILENAME', 'app.log')
    LOG_FILE = f'{STATIC_FILES_PATH}/{LOG_FILENAME}'

    log_format = "%(asctime)s %(levelname)-8s %(message)s  file: %(pathname)s  %(funcName)s line %(lineno)d"
    date_format = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(filename=LOG_FILE,
                            level=logging.ERROR, format=log_format, datefmt=date_format)
    
    # Example logging messages
    logging.debug("A DEBUG Message")
    logging.info("An INFO")
    logging.warning("A WARNING")
    logging.error("An ERROR")
    logging.critical("A message of CRITICAL severity")
