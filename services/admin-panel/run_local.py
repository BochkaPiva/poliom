#!/usr/bin/env python3
"""
Скрипт для локального запуска админ-панели без Docker
"""

import os
import sys
from pathlib import Path

# Добавляем путь к shared модулям
current_dir = Path(__file__).parent
shared_path = current_dir.parent / "shared"
sys.path.insert(0, str(shared_path))

# Загружаем переменные окружения из .env.local
from dotenv import load_dotenv
load_dotenv('.env.local')

# Устанавливаем PYTHONPATH
os.environ['PYTHONPATH'] = str(shared_path)

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Запуск админ-панели в режиме разработки...")
    print(f"📁 Shared path: {shared_path}")
    print(f"🔗 Database URL: {os.getenv('DATABASE_URL', 'не задан')}")
    print(f"🔗 Redis URL: {os.getenv('REDIS_URL', 'не задан')}")
    print("=" * 50)
    
    # Запускаем сервер
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Автоперезагрузка при изменении файлов
        log_level="info"
    ) 