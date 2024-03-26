from celery import Celery
from celery.schedules import crontab
import sys
print(sys.path)

from configs.db import REDIS_PORT, REDIS_HOST
celery_app = Celery(
                    'tasks',
                    broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
                    backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
            )

# Optional configuration, for example timezone
celery_app.conf.update(timezone="UTC")

# In your Celery app initialization module, ensure task discovery is correctly set up
celery_app.autodiscover_tasks(['tasks'], force=True)


celery_app.conf.beat_schedule = {
    "generate_daily_report": {
        "task": "tasks.tasks.generate_daily_report",
        "schedule": crontab(hour=8, minute=0), 
    },
}