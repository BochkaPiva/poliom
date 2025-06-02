#!/usr/bin/env python3
"""
Тестовая программа для проверки функционала кнопки файлов
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

# Имитация временного хранилища файлов
files_storage = {}

def cleanup_old_files():
    """Очистка старых файлов из хранилища (старше 1 часа)"""
    current_time = time.time()
    keys_to_remove = []
    
    for key, data in files_storage.items():
        if current_time - data.get('timestamp', 0) > 3600:  # 1 час
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del files_storage[key]
    
    if keys_to_remove:
        print(f"Очищено {len(keys_to_remove)} устаревших записей файлов")

def test_files_storage():
    """Тест функционала хранения файлов"""
    print("🧪 ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА ФАЙЛОВ")
    print("=" * 50)
    
    # Имитируем сохранение файлов
    test_files = [
        {
            'title': 'Правила внутреннего трудового распорядка',
            'file_path': '/docs/rules.pdf',
            'document_id': 1,
            'similarity': 0.85
        },
        {
            'title': 'Положение об оплате труда',
            'file_path': '/docs/salary.pdf', 
            'document_id': 2,
            'similarity': 0.72
        }
    ]
    
    message_id = "12345"
    
    # Сохраняем файлы
    files_storage[message_id] = {
        'files': test_files,
        'timestamp': time.time()
    }
    
    print(f"✅ Файлы сохранены для сообщения {message_id}")
    print(f"   Количество файлов: {len(test_files)}")
    for i, file_info in enumerate(test_files, 1):
        print(f"   {i}. {file_info['title']} (релевантность: {file_info['similarity']:.1%})")
    
    # Имитируем получение файлов
    print("\n🔍 Получение файлов из хранилища:")
    files_data = files_storage.get(message_id, {})
    files = files_data.get('files', [])
    
    if files:
        print("✅ Файлы найдены")
        
        # Формируем текст как в боте
        files_text = "📎 **Файлы-источники:**\n\n"
        
        for i, file_info in enumerate(files, 1):
            title = file_info.get('title', 'Документ')
            similarity = file_info.get('similarity', 0)
            files_text += f"{i}. **{title}**\n"
            files_text += f"   📊 Релевантность: {similarity:.1%}\n"
            
            file_path = file_info.get('file_path')
            if file_path:
                filename = os.path.basename(file_path)
                files_text += f"   📄 Файл: {filename}\n"
            
            files_text += "\n"
        
        files_text += "💡 **Примечание:** Эти документы содержат информацию, на основе которой был сформирован ответ.\n"
        files_text += "Для получения полных текстов документов обратитесь к HR-отделу."
        
        print("📋 Сформированный текст ответа:")
        print(files_text)
        
        # Очищаем файлы из хранилища
        if message_id in files_storage:
            del files_storage[message_id]
            print(f"🗑️ Файлы для сообщения {message_id} удалены из хранилища")
    else:
        print("❌ Файлы не найдены")
    
    print("\n" + "=" * 50)
    print("✅ Тест завершен")

if __name__ == "__main__":
    test_files_storage() 