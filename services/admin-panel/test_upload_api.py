#!/usr/bin/env python3
"""
Тест загрузки документа через API админ-панели
"""

import os
import sys
import time
import requests
from pathlib import Path

# Добавляем путь к services
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env.local')

from sqlalchemy.orm import sessionmaker
from shared.models.database import engine
from shared.models import Document, Admin

# Создаем сессию базы данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_admin_id():
    """Получаем ID первого администратора"""
    db = SessionLocal()
    try:
        admin = db.query(Admin).first()
        if admin:
            return admin.id
        else:
            print("❌ Администратор не найден в базе данных")
            return None
    finally:
        db.close()

def test_document_upload():
    """Тестируем загрузку документа"""
    print("🧪 Тестирование загрузки документа через API\n")
    
    # Получаем ID администратора
    admin_id = get_admin_id()
    if not admin_id:
        return False
    
    print(f"👤 Используем администратора ID: {admin_id}")
    
    # Путь к тестовому документу
    test_file = Path("test_document.txt")
    if not test_file.exists():
        print(f"❌ Тестовый файл не найден: {test_file}")
        return False
    
    print(f"📄 Тестовый файл: {test_file}")
    
    # URL админ-панели
    base_url = "http://localhost:8001"
    upload_url = f"{base_url}/documents/upload"
    
    # Данные для загрузки
    files = {
        'file': ('test_document.txt', open(test_file, 'rb'), 'text/plain')
    }
    
    data = {
        'title': 'Тестовый документ для проверки чанкинга',
        'description': 'Документ для тестирования улучшенного алгоритма разбиения на чанки',
        'admin_id': admin_id
    }
    
    try:
        print("📤 Отправляем запрос на загрузку...")
        
        # Отправляем запрос
        response = requests.post(upload_url, files=files, data=data, allow_redirects=False)
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 303:  # Redirect после успешной загрузки
            print("✅ Документ успешно загружен!")
            return True
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к админ-панели")
        print("💡 Убедитесь, что админ-панель запущена на http://localhost:8001")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        files['file'][1].close()

def check_document_processing():
    """Проверяем обработку документа"""
    print("\n🔍 Проверяем обработку документа...")
    
    db = SessionLocal()
    try:
        # Получаем последний загруженный документ
        document = db.query(Document).order_by(Document.created_at.desc()).first()
        
        if not document:
            print("❌ Документы не найдены")
            return False
        
        print(f"📄 Последний документ: {document.title}")
        print(f"📊 Статус: {document.processing_status}")
        print(f"📈 Чанков: {document.chunks_count or 0}")
        
        # Ждем обработки
        max_wait = 60  # Максимум 60 секунд
        wait_time = 0
        
        while document.processing_status in ['pending', 'processing'] and wait_time < max_wait:
            print(f"⏳ Ожидаем обработки... ({wait_time}s)")
            time.sleep(5)
            wait_time += 5
            
            # Обновляем статус
            db.refresh(document)
        
        print(f"\n📊 Финальный статус: {document.processing_status}")
        print(f"📈 Количество чанков: {document.chunks_count or 0}")
        
        if document.processing_status == 'completed':
            print("✅ Документ успешно обработан!")
            return True
        elif document.processing_status == 'failed':
            print(f"❌ Ошибка обработки: {document.error_message}")
            return False
        else:
            print("⏳ Документ все еще обрабатывается")
            return False
            
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Тестирование загрузки и обработки документа\n")
    
    # Тестируем загрузку
    upload_success = test_document_upload()
    
    if upload_success:
        # Проверяем обработку
        processing_success = check_document_processing()
        
        if processing_success:
            print("\n🎉 Тест успешно завершен!")
            print("✅ Документ загружен и обработан с улучшенным алгоритмом чанкинга")
        else:
            print("\n⚠️ Документ загружен, но есть проблемы с обработкой")
    else:
        print("\n❌ Тест не пройден - ошибка загрузки")
    
    return upload_success and processing_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 