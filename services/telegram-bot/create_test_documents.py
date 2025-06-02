#!/usr/bin/env python3
"""
Скрипт для создания тестовых документов с эмбеддингами
"""

import os
import sys
from pathlib import Path

# Добавляем пути для импортов
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "shared"))
sys.path.insert(0, str(project_root / "services" / "telegram-bot"))

from bot.config import config
from bot.database import get_db_session
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_documents():
    """Создание тестовых документов с эмбеддингами"""
    
    # Получаем сессию БД
    db_session = next(get_db_session())
    
    try:
        # Загружаем модель эмбеддингов
        logger.info("Загружаем модель эмбеддингов...")
        embeddings_model = SentenceTransformer('ai-forever/sbert_large_nlu_ru')
        logger.info("Модель эмбеддингов загружена!")
        
        # Тестовые документы
        test_documents = [
            {
                'title': 'Политика оплаты труда',
                'content': 'Заработная плата выплачивается два раза в месяц: аванс 15 числа, основная часть - до 5 числа следующего месяца. Размер аванса составляет 40% от оклада. Премии выплачиваются ежеквартально по результатам работы.',
                'filename': 'salary_policy.pdf'
            },
            {
                'title': 'Рабочее время и отпуска',
                'content': 'Рабочая неделя составляет 40 часов. Рабочий день с 9:00 до 18:00 с обеденным перерывом с 13:00 до 14:00. Ежегодный оплачиваемый отпуск составляет 28 календарных дней. Дополнительные выходные дни предоставляются за переработки.',
                'filename': 'work_schedule.pdf'
            },
            {
                'title': 'Дистанционная работа',
                'content': 'Сотрудники могут работать удаленно до 3 дней в неделю по согласованию с руководителем. Для удаленной работы необходимо подать заявление за неделю. Обязательно присутствие в офисе по понедельникам и пятницам для планерок.',
                'filename': 'remote_work.pdf'
            },
            {
                'title': 'Социальные льготы',
                'content': 'Компания предоставляет добровольное медицинское страхование, компенсацию спортивных занятий до 20000 рублей в год, корпоративное питание. Также действует программа обучения и развития сотрудников.',
                'filename': 'benefits.pdf'
            }
        ]
        
        # Создаем документы и чанки
        for doc_data in test_documents:
            logger.info(f"Создаем документ: {doc_data['title']}")
            
            # Создаем эмбеддинг для содержимого
            embedding = embeddings_model.encode(doc_data['content']).tolist()
            
            # Вставляем документ
            insert_doc_query = text("""
                INSERT INTO documents (title, content, filename, original_filename, file_path, file_size, file_type, processing_status, uploaded_by)
                VALUES (:title, :content, :filename, :original_filename, :file_path, :file_size, :file_type, :processing_status, :uploaded_by)
                RETURNING id;
            """)
            
            # Создаем админа если его нет
            admin_query = text("INSERT INTO admins (user_id, username, is_active) VALUES (1, 'system', true) ON CONFLICT (user_id) DO NOTHING;")
            db_session.execute(admin_query)
            db_session.commit()
            
            result = db_session.execute(insert_doc_query, {
                'title': doc_data['title'],
                'content': doc_data['content'],
                'filename': doc_data['filename'],
                'original_filename': doc_data['filename'],
                'file_path': f"/uploads/{doc_data['filename']}",
                'file_size': len(doc_data['content']),
                'file_type': 'pdf',
                'processing_status': 'completed',
                'uploaded_by': 1
            })
            
            document_id = result.fetchone()[0]
            logger.info(f"Документ создан с ID: {document_id}")
            
            # Создаем чанк с эмбеддингом
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            insert_chunk_query = text("""
                INSERT INTO document_chunks (document_id, content, chunk_index, embedding)
                VALUES (:document_id, :content, :chunk_index, :embedding::vector);
            """)
            
            db_session.execute(insert_chunk_query, {
                'document_id': document_id,
                'content': doc_data['content'],
                'chunk_index': 0,
                'embedding': embedding_str
            })
            
            logger.info(f"Чанк создан для документа {document_id}")
        
        db_session.commit()
        logger.info("✅ Все тестовые документы созданы успешно!")
        
        # Проверяем результат
        doc_count = db_session.execute(text("SELECT COUNT(*) FROM documents")).fetchone()[0]
        chunk_count = db_session.execute(text("SELECT COUNT(*) FROM document_chunks")).fetchone()[0]
        
        logger.info(f"📊 Создано документов: {doc_count}")
        logger.info(f"📊 Создано чанков: {chunk_count}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания тестовых документов: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()

if __name__ == "__main__":
    create_test_documents() 