#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота
"""

import os
import sys
import subprocess
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def check_env_file():
    """Проверка наличия .env файла"""
    if not os.path.exists('.env'):
        logger.error("❌ Файл .env не найден!")
        logger.info("📝 Скопируйте .env.example в .env и заполните необходимые переменные:")
        logger.info("   cp .env.example .env")
        return False
    return True

def check_required_env_vars():
    """Проверка обязательных переменных окружения"""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GIGACHAT_API_KEY',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        return False
    
    return True

def install_dependencies():
    """Установка зависимостей"""
    logger.info("📦 Установка зависимостей...")
    
    try:
        # Устанавливаем зависимости для бота
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            "services/telegram-bot/requirements.txt"
        ], check=True)
        
        logger.info("✅ Зависимости установлены")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Ошибка установки зависимостей: {e}")
        return False

def start_bot():
    """Запуск бота"""
    logger.info("🚀 Запуск Telegram бота...")
    
    # Переходим в директорию бота
    bot_dir = "services/telegram-bot"
    
    try:
        # Запускаем бота
        subprocess.run([
            sys.executable, "main.py"
        ], cwd=bot_dir, check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
        return True

def main():
    """Главная функция"""
    logger.info("🤖 Запуск корпоративного RAG-бота")
    
    # Проверяем .env файл
    if not check_env_file():
        return 1
    
    # Проверяем переменные окружения
    if not check_required_env_vars():
        return 1
    
    # Устанавливаем зависимости
    if not install_dependencies():
        return 1
    
    # Запускаем бота
    start_bot()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 