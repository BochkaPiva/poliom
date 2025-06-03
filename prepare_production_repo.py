#!/usr/bin/env python3
"""
Скрипт для подготовки чистого production репозитория POLIOM HR Assistant
Копирует только необходимые файлы, исключает тесты и документацию
"""

import os
import shutil
import fnmatch
from pathlib import Path

# Файлы и папки для ВКЛЮЧЕНИЯ в production
INCLUDE_FILES = [
    # Корневые файлы
    'README.md',
    'requirements.txt', 
    '.env.production',
    '.env.production.example',
    '.dockerignore',
    'docker-compose.prod.yml',
    'deploy.sh',
    '.gitignore',
]

# Директории для полного копирования (с фильтрацией)
INCLUDE_DIRS = [
    'services/telegram-bot/handlers',
    'services/telegram-bot/bot',
    'services/admin-panel/templates',
    'services/admin-panel/static',
    'services/shared/database',
    'services/shared/models', 
    'services/shared/utils',
    'services/shared/sql',
]

# Отдельные файлы в сервисах
INCLUDE_SERVICE_FILES = [
    'services/telegram-bot/Dockerfile',
    'services/telegram-bot/main.py',
    'services/telegram-bot/requirements.txt',
    'services/admin-panel/Dockerfile',
    'services/admin-panel/main.py',
    'services/admin-panel/requirements.txt',
    'services/admin-panel/celery_app.py',
    'services/admin-panel/tasks.py',
    'services/shared/requirements.txt',
]

# Паттерны для ИСКЛЮЧЕНИЯ
EXCLUDE_PATTERNS = [
    '*.md',  # Все .md файлы кроме README.md
    'test_*.py',
    '*test*.py',
    'debug_*.py',
    'check_*.py',
    'diagnose_*.py',
    'analyze_*.py',
    'fix_*.py',
    'process_*.py',
    'setup_*.py',
    '*_test.py',
    '*test.py',
    '*debug*.py',
    '*monitor*.py',
    '*_simple.py',
    '*_safe.py',
    'quick_*.py',
    'demo_*.py',
    'direct_*.py',
    '*.bat',
    '*.log',
    '.env.local',
    '.env.example',
    '.env.pgvector',
    '__pycache__',
    'venv',
    'uploads',
    'cache',
    'logs',
    '.git',
]

def should_exclude(filepath):
    """Проверяет, нужно ли исключить файл"""
    filename = os.path.basename(filepath)
    
    # Специальная обработка для README.md (не исключаем)
    if filename == 'README.md':
        return False
        
    # Проверяем паттерны исключения
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True
        if fnmatch.fnmatch(filepath, pattern):
            return True
    
    return False

def copy_file_if_needed(src, dst):
    """Копирует файл если он не исключен"""
    if should_exclude(src):
        print(f"❌ Исключен: {src}")
        return False
    
    # Создаем директорию если не существует
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    
    try:
        shutil.copy2(src, dst)
        print(f"✅ Скопирован: {src} -> {dst}")
        return True
    except Exception as e:
        print(f"❌ Ошибка копирования {src}: {e}")
        return False

def copy_directory_filtered(src_dir, dst_dir):
    """Копирует директорию с фильтрацией"""
    if not os.path.exists(src_dir):
        print(f"⚠️  Директория не найдена: {src_dir}")
        return
    
    for root, dirs, files in os.walk(src_dir):
        # Исключаем директории целиком
        dirs[:] = [d for d in dirs if not should_exclude(d)]
        
        for file in files:
            src_file = os.path.join(root, file)
            rel_path = os.path.relpath(src_file, src_dir)
            dst_file = os.path.join(dst_dir, rel_path)
            
            copy_file_if_needed(src_file, dst_file)

def main():
    """Основная функция подготовки production репозитория"""
    source_dir = "."
    target_dir = "poliom_production"
    
    print("🚀 Подготовка чистого production репозитория POLIOM HR Assistant")
    print(f"📁 Исходная директория: {source_dir}")
    print(f"📁 Целевая директория: {target_dir}")
    print()
    
    # Удаляем целевую директорию если существует
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
        print(f"🗑️  Удалена существующая директория: {target_dir}")
    
    # Создаем целевую директорию
    os.makedirs(target_dir, exist_ok=True)
    
    print("\n📋 Копирование корневых файлов:")
    # Копируем корневые файлы
    for file in INCLUDE_FILES:
        if os.path.exists(file):
            copy_file_if_needed(file, os.path.join(target_dir, file))
    
    print("\n📋 Копирование файлов сервисов:")
    # Копируем файлы сервисов
    for file in INCLUDE_SERVICE_FILES:
        if os.path.exists(file):
            copy_file_if_needed(file, os.path.join(target_dir, file))
    
    print("\n📋 Копирование директорий:")
    # Копируем директории с фильтрацией
    for dir_path in INCLUDE_DIRS:
        src_dir = dir_path
        dst_dir = os.path.join(target_dir, dir_path)
        print(f"\n📂 Обрабатываем директорию: {dir_path}")
        copy_directory_filtered(src_dir, dst_dir)
    
    print(f"\n✅ Подготовка завершена!")
    print(f"📁 Чистый production код находится в: {target_dir}")
    print(f"🔗 Теперь можно инициализировать Git и пушить в: https://github.com/BochkaPiva/poliom_production.git")
    
    # Показываем статистику
    total_files = 0
    for root, dirs, files in os.walk(target_dir):
        total_files += len(files)
    
    print(f"📊 Всего файлов в production: {total_files}")

if __name__ == "__main__":
    main() 