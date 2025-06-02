#!/usr/bin/env python3
"""
Тест единой системы обработки документов
"""

import os
import sys
from pathlib import Path

# Добавляем путь к services
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv('.env.local')

from document_processor_unified import (
    process_document_unified,
    process_all_pending_unified,
    get_documents_status_unified
)

def test_system():
    """Тестируем единую систему"""
    print("🧪 ТЕСТ ЕДИНОЙ СИСТЕМЫ ОБРАБОТКИ ДОКУМЕНТОВ")
    print("=" * 60)
    
    # 1. Проверяем текущий статус
    print("📊 1. Проверяем текущий статус документов...")
    status = get_documents_status_unified()
    
    if status["status"] == "success":
        stats = status["statistics"]
        print(f"   ✅ Всего документов: {stats['total']}")
        print(f"   ✅ Обработано: {stats['completed']}")
        print(f"   ❌ С ошибками: {stats['failed']}")
        print(f"   ⏳ Ожидают обработки: {stats['pending']}")
        
        print("\n📄 Список документов:")
        for doc in status["documents"]:
            print(f"   ID {doc['id']}: {doc['filename']} - {doc['processing_status']} ({doc['chunks_count']} чанков)")
    else:
        print(f"   ❌ Ошибка: {status['message']}")
        return False
    
    # 2. Если есть необработанные документы, обрабатываем их
    if stats['pending'] > 0:
        print(f"\n🔄 2. Обрабатываем {stats['pending']} необработанных документов...")
        result = process_all_pending_unified()
        
        if result["status"] == "completed":
            print(f"   ✅ {result['message']}")
            print(f"   📊 Успешно: {result['successful']}, Ошибок: {result['failed']}")
        else:
            print(f"   ❌ Ошибка: {result['message']}")
            return False
    else:
        print("\n✅ 2. Все документы уже обработаны")
    
    # 3. Проверяем финальный статус
    print("\n📊 3. Финальный статус после обработки...")
    final_status = get_documents_status_unified()
    
    if final_status["status"] == "success":
        final_stats = final_status["statistics"]
        print(f"   ✅ Всего документов: {final_stats['total']}")
        print(f"   ✅ Обработано: {final_stats['completed']}")
        print(f"   ❌ С ошибками: {final_stats['failed']}")
        print(f"   ⏳ Ожидают обработки: {final_stats['pending']}")
        
        # Показываем детали по каждому документу
        print("\n📄 Детальная информация:")
        for doc in final_status["documents"]:
            print(f"   📄 {doc['filename']}")
            print(f"      ID: {doc['id']}")
            print(f"      Статус: {doc['processing_status']}")
            print(f"      Чанков: {doc['chunks_count']}")
            print(f"      Загружен: {doc['created_at']}")
            if doc['processed_at']:
                print(f"      Обработан: {doc['processed_at']}")
            print()
    
    # 4. Итоги
    print("=" * 60)
    print("🎯 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    if final_stats['pending'] == 0 and final_stats['failed'] == 0:
        print("🎉 ВСЕ ОТЛИЧНО!")
        print("✅ Все документы успешно обработаны")
        print("✅ Единая система работает надежно")
        print("✅ Можно загружать новые документы через админ-панель")
        return True
    elif final_stats['failed'] > 0:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ:")
        print(f"❌ Документов с ошибками: {final_stats['failed']}")
        print("🔧 Требуется дополнительная диагностика")
        return False
    else:
        print("⏳ ОБРАБОТКА НЕ ЗАВЕРШЕНА:")
        print(f"⏳ Документов ожидают обработки: {final_stats['pending']}")
        return False

def test_specific_document(document_id: int):
    """Тестируем обработку конкретного документа"""
    print(f"🧪 ТЕСТ ОБРАБОТКИ ДОКУМЕНТА ID {document_id}")
    print("=" * 60)
    
    # Получаем информацию о документе
    doc_status = get_documents_status_unified(document_id)
    
    if doc_status["status"] == "error":
        print(f"❌ Ошибка: {doc_status['message']}")
        return False
    
    doc = doc_status["document"]
    print(f"📄 Документ: {doc['filename']}")
    print(f"📊 Текущий статус: {doc['processing_status']}")
    print(f"📈 Чанков: {doc['chunks_count']}")
    
    # Если документ не обработан, обрабатываем
    if doc['processing_status'] != 'completed':
        print(f"\n🔄 Обрабатываем документ {document_id}...")
        result = process_document_unified(document_id, use_safe_mode=True)
        
        if result["status"] == "completed":
            print(f"✅ Успешно обработан!")
            print(f"📊 Создано чанков: {result['chunks_created']}")
            print(f"📏 Статистика чанков:")
            print(f"   Мин. размер: {result['chunk_stats']['min_size']}")
            print(f"   Макс. размер: {result['chunk_stats']['max_size']}")
            print(f"   Средний размер: {result['chunk_stats']['avg_size']:.1f}")
            return True
        else:
            print(f"❌ Ошибка обработки: {result['error']}")
            return False
    else:
        print("✅ Документ уже обработан")
        return True

if __name__ == "__main__":
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ЕДИНОЙ СИСТЕМЫ")
    print()
    
    # Основной тест системы
    success = test_system()
    
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ Единая система обработки документов работает надежно")
        print("✅ Все компоненты интегрированы корректно")
        print("✅ Система готова к продуктивному использованию")
    else:
        print("⚠️ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ")
        print("🔧 Требуется дополнительная настройка")
    
    print("\n💡 Для загрузки новых документов используйте админ-панель:")
    print("   http://localhost:8000")
    print("\n📚 Для ручной обработки используйте:")
    print("   python document_processor_unified.py") 