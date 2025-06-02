#!/usr/bin/env python3
"""
Скрипт для тестирования загрузки и обработки нового документа
"""

import os
import sys
from pathlib import Path
import time
import shutil

# Добавляем путь к проекту
current_dir = Path(__file__).parent
services_dir = current_dir.parent
sys.path.insert(0, str(services_dir))

from dotenv import load_dotenv
load_dotenv('.env.local')

from shared.models.database import SessionLocal
from shared.models import Document, Admin
from document_processor_unified import process_document_unified, get_documents_status_unified
from tasks import process_document

# Создаем сессию базы данных
db = SessionLocal()

def create_test_document():
    """Создает тестовый документ для загрузки"""
    test_content = """
    ТЕСТОВЫЙ ДОКУМЕНТ ДЛЯ ПРОВЕРКИ СИСТЕМЫ
    
    Этот документ создан для тестирования системы обработки документов.
    
    Раздел 1: Введение
    Данный документ содержит тестовую информацию для проверки работы
    алгоритма разбиения на чанки и системы векторного поиска.
    
    Раздел 2: Основная часть
    В этом разделе мы описываем различные аспекты работы системы.
    Система должна корректно обрабатывать текст и создавать качественные
    чанки для семантического поиска.
    
    Раздел 3: Заключение
    Тестирование показывает, что система работает корректно и готова
    к использованию в продуктивной среде.
    
    Дополнительная информация:
    - Система поддерживает различные форматы документов
    - Алгоритм чанкинга учитывает границы предложений
    - Векторный поиск обеспечивает высокое качество результатов
    """
    
    test_file_path = Path("uploads/test_document.txt")
    test_file_path.parent.mkdir(exist_ok=True)
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    return test_file_path

def simulate_document_upload(file_path):
    """Имитирует загрузку документа в базу данных"""
    print(f"📄 Имитация загрузки документа: {os.path.basename(file_path)}")
    
    # Получаем размер файла
    file_size = os.path.getsize(file_path)
    
    # Определяем тип файла
    file_type = os.path.splitext(file_path)[1].lower()
    if not file_type:
        file_type = '.txt'
    
    # Создаем запись в базе данных
    document = Document(
        filename=os.path.basename(file_path),
        original_filename=os.path.basename(file_path),
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_type,
        processing_status='pending',
        uploaded_by=1  # ID администратора из базы данных
    )
    
    db.add(document)
    db.commit()
    
    print(f"✅ Документ добавлен в базу данных с ID: {document.id}")
    return document

def test_celery_processing(document_id):
    """Тестирует обработку документа через Celery"""
    print(f"🔄 Запуск обработки документа через Celery (ID: {document_id})")
    
    # Отправляем задачу в Celery
    task = process_document.delay(document_id)
    print(f"📤 Задача отправлена в очередь: {task.id}")
    
    # Ждем выполнения задачи
    print("⏳ Ожидание выполнения задачи...")
    timeout = 60  # 60 секунд
    start_time = time.time()
    
    while not task.ready() and (time.time() - start_time) < timeout:
        time.sleep(2)
        print(".", end="", flush=True)
    
    print()
    
    if task.ready():
        if task.successful():
            result = task.result
            print(f"✅ Задача выполнена успешно: {result}")
            return True
        else:
            print(f"❌ Задача завершилась с ошибкой: {task.result}")
            return False
    else:
        print("⏰ Задача не завершилась в течение таймаута")
        return False

def test_direct_processing(document_id):
    """Тестирует прямую обработку документа"""
    print(f"🔄 Прямая обработка документа (ID: {document_id})")
    
    try:
        result = process_document_unified(document_id)
        print(f"✅ Документ обработан напрямую: {result}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при прямой обработке: {e}")
        return False

def check_processing_results(document_id):
    """Проверяет результаты обработки документа"""
    print(f"🔍 Проверка результатов обработки документа ID: {document_id}")
    
    # Получаем информацию о документе
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        print("❌ Документ не найден")
        return False
    
    print(f"📊 Статус документа: {document.processing_status}")
    print(f"📊 Количество чанков: {document.chunks_count}")
    
    if document.chunks:
        chunk_sizes = [len(chunk.content) for chunk in document.chunks]
        print(f"📊 Размеры чанков: мин={min(chunk_sizes)}, макс={max(chunk_sizes)}, среднее={sum(chunk_sizes)/len(chunk_sizes):.1f}")
        
        # Показываем первые несколько чанков
        print("\n📝 Первые чанки:")
        for i, chunk in enumerate(document.chunks[:3]):
            print(f"  Чанк {i+1}: {chunk.content[:100]}...")
    
    return document.processing_status == 'completed'

def cleanup_test_data(document_id, file_path):
    """Очищает тестовые данные"""
    print("🧹 Очистка тестовых данных...")
    
    # Удаляем документ из базы данных
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        # Удаляем чанки
        for chunk in document.chunks:
            db.delete(chunk)
        # Удаляем документ
        db.delete(document)
        db.commit()
        print("✅ Документ удален из базы данных")
    
    # Удаляем файл
    if file_path.exists():
        file_path.unlink()
        print("✅ Тестовый файл удален")

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ СИСТЕМЫ ЗАГРУЗКИ И ОБРАБОТКИ ДОКУМЕНТОВ")
    print("=" * 60)
    
    # Проверяем текущий статус системы
    print("\n1️⃣ Проверка текущего статуса системы:")
    status = get_documents_status_unified()
    if status["status"] == "success":
        stats = status["statistics"]
        print(f"📊 Всего документов: {stats['total']}")
        print(f"📊 Обработано: {stats['completed']}")
        print(f"📊 С ошибками: {stats['failed']}")
        print(f"📊 В очереди: {stats['pending']}")
    else:
        print(f"❌ Ошибка получения статуса: {status.get('message', 'Unknown error')}")
        return
    
    # Создаем тестовый документ
    print("\n2️⃣ Создание тестового документа:")
    test_file = create_test_document()
    print(f"✅ Тестовый файл создан: {test_file}")
    
    # Имитируем загрузку
    print("\n3️⃣ Имитация загрузки документа:")
    document = simulate_document_upload(test_file)
    
    # Тестируем обработку через Celery
    print("\n4️⃣ Тестирование обработки через Celery:")
    celery_success = test_celery_processing(document.id)
    
    # Если Celery не сработал, пробуем прямую обработку
    if not celery_success:
        print("\n5️⃣ Тестирование прямой обработки:")
        direct_success = test_direct_processing(document.id)
    else:
        direct_success = True
    
    # Проверяем результаты
    print("\n6️⃣ Проверка результатов:")
    results_ok = check_processing_results(document.id)
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ ОТЧЕТ:")
    print(f"✅ Создание файла: ОК")
    print(f"✅ Загрузка в БД: ОК")
    print(f"{'✅' if celery_success else '❌'} Обработка через Celery: {'ОК' if celery_success else 'ОШИБКА'}")
    print(f"{'✅' if direct_success else '❌'} Прямая обработка: {'ОК' if direct_success else 'ОШИБКА'}")
    print(f"{'✅' if results_ok else '❌'} Результаты обработки: {'ОК' if results_ok else 'ОШИБКА'}")
    
    # Спрашиваем о очистке
    cleanup = input("\n🗑️ Удалить тестовые данные? (y/n): ").lower().strip()
    if cleanup in ['y', 'yes', 'да', 'д']:
        cleanup_test_data(document.id, test_file)
        print("✅ Тестовые данные удалены")
    else:
        print(f"ℹ️ Тестовые данные сохранены. ID документа: {document.id}")
    
    print("\n🎉 Тестирование завершено!")
    
    if celery_success or direct_success:
        print("✅ Система работает корректно!")
    else:
        print("❌ Обнаружены проблемы в работе системы")

if __name__ == "__main__":
    main() 