#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт запуска Telegram-бота POLIOM
Обновленная версия с FAQ и умным поиском
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Добавляем пути к модулям
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

# Загружаем переменные окружения
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Загружены переменные окружения из {env_path}")
else:
    print(f"⚠️ Файл .env не найден по пути {env_path}")

# Проверяем наличие необходимых переменных
required_vars = ['TELEGRAM_BOT_TOKEN', 'GIGACHAT_API_KEY', 'DATABASE_URL']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
    print("Проверьте файл .env")
    sys.exit(1)

print("✅ Все необходимые переменные окружения найдены")

# Импортируем и запускаем бота
try:
    from bot.main import main
    
    if __name__ == "__main__":
        print("🚀 Запуск POLIOM Telegram Bot...")
        main()
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Проверьте структуру проекта и зависимости")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка запуска бота: {e}")
    sys.exit(1) 