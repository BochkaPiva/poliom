"""
Celery приложение для обработки документов
"""

import os
from celery import Celery

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env.local')

# Настройки Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Создаем Celery приложение
app = Celery(
    'admin_panel',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks']
)

# Настройки Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

if __name__ == '__main__':
    app.start() 