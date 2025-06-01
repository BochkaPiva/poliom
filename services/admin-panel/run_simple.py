#!/usr/bin/env python3
"""
Простой скрипт для локального запуска админ-панели
"""

import os
import sys
from pathlib import Path

# Добавляем путь к shared модулям
current_dir = Path(__file__).parent
shared_path = current_dir.parent / "shared"
sys.path.insert(0, str(shared_path))

# Загружаем переменные окружения из .env
from dotenv import load_dotenv
load_dotenv('.env')

# Устанавливаем PYTHONPATH
os.environ['PYTHONPATH'] = str(shared_path)

print("🚀 Запуск админ-панели...")
print(f"📁 Shared path: {shared_path}")
print(f"🔗 Database URL: {os.getenv('DATABASE_URL', 'не задан')}")
print("=" * 50)

# Сначала проверим импорты
try:
    print("📦 Проверяю импорты...")
    from main import app
    print("✅ Импорты успешны!")
    
    # Запускаем сервер
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,  # Без автоперезагрузки
        log_level="info"
    )
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc() 