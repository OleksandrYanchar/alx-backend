from celery import Celery
from .db import REDIS_URL


celery = Celery(
    'worker',
    broker=f'{REDIS_URL}/0',
    backend=REDIS_URL,
)

