from celery import Celery
from celery.schedules import crontab

from configs.db import REDIS_PORT, REDIS_HOST

celery_app = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)

# Optional configuration, for example timezone
celery_app.conf.update(timezone="UTC")

# In your Celery app initialization module, ensure task discovery is correctly set up
celery_app.autodiscover_tasks(["tasks.admin"], force=True)
celery_app.autodiscover_tasks(["tasks.store"], force=True)


celery_app.conf.beat_schedule = {
    "generate_daily_report": {
        "task": "generate_report",
        "schedule": crontab(hour=8, minute=0),
    },
    "update_product_vip_every_12_hours": {
        "task": "update_post_vip_from_user_vip", 
        "schedule": crontab(hour="0,4,8,12,16,20"), 
    },
    "unvip_exited_users": {
        "task": "unvip_exited_users", 
        "schedule": crontab(hour="0"), 
    },
}

