"""
Модуль для работы с базой данных в Telegram боте
"""

import logging
import os
import sys
from pathlib import Path
from typing import Generator
import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Добавляем путь к shared модулям (исправлено для Docker)
sys.path.append('/app/shared')

from models.database import Base
from models.user import User
from models.admin import Admin
from models.document import Document, DocumentChunk
from models.query_log import QueryLog
from models.menu import MenuSection, MenuItem

logger = logging.getLogger(__name__)

# Глобальные переменные для подключения к БД
engine = None
SessionLocal = None

def init_database():
    """Инициализация подключения к базе данных"""
    global engine, SessionLocal
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL не найден в переменных окружения")
    
    try:
        # Создаем движок базы данных
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False  # Установите True для отладки SQL запросов
        )
        
        # Создаем фабрику сессий
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        logger.info("✅ Подключение к базе данных установлено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        raise

async def init_db():
    """Асинхронная инициализация базы данных"""
    try:
        # Инициализируем подключение
        init_database()
        
        # Создаем таблицы, если их нет
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ База данных инициализирована")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise

def get_db_session() -> Generator[Session, None, None]:
    """
    Получение сессии базы данных
    
    Yields:
        Session: Сессия SQLAlchemy
    """
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Ошибка в сессии БД: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None) -> User:
    """
    Получение или создание пользователя
    
    Args:
        telegram_id: ID пользователя в Telegram
        username: Username пользователя
        full_name: Полное имя пользователя
        
    Returns:
        User: Объект пользователя
    """
    db = next(get_db_session())
    
    try:
        # Ищем существующего пользователя
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if user:
            # Обновляем информацию, если она изменилась
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                updated = True
            
            if updated:
                db.commit()
                logger.info(f"Обновлена информация пользователя {telegram_id}")
            
            return user
        
        # Создаем нового пользователя
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Создан новый пользователь: {telegram_id} ({username})")
        return new_user
        
    except Exception as e:
        logger.error(f"Ошибка при работе с пользователем {telegram_id}: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def log_user_query(user_id: int, query_text: str, response_text: str, 
                   chunks_used: int = 0, model_used: str = "GigaChat") -> bool:
    """
    Логирование запроса пользователя
    
    Args:
        user_id: ID пользователя
        query_text: Текст запроса
        response_text: Текст ответа
        chunks_used: Количество использованных чанков
        model_used: Используемая модель
        
    Returns:
        bool: Успешность операции
    """
    db = next(get_db_session())
    
    try:
        log_entry = QueryLog(
            user_id=user_id,
            query_text=query_text,
            response_text=response_text,
            chunks_used=chunks_used,
            model_used=model_used
        )
        
        db.add(log_entry)
        db.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка логирования запроса: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_user_stats(telegram_id: int) -> dict:
    """
    Получение статистики пользователя
    
    Args:
        telegram_id: ID пользователя в Telegram
        
    Returns:
        dict: Статистика пользователя
    """
    db = next(get_db_session())
    
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return {'error': 'Пользователь не найден'}
        
        # Подсчитываем количество запросов
        query_count = db.query(QueryLog).filter(QueryLog.user_id == user.id).count()
        
        # Получаем последний запрос
        last_query = db.query(QueryLog).filter(
            QueryLog.user_id == user.id
        ).order_by(QueryLog.created_at.desc()).first()
        
        return {
            'user_id': user.id,
            'telegram_id': user.telegram_id,
            'username': user.username,
            'full_name': user.full_name,
            'is_active': user.is_active,
            'created_at': user.created_at,
            'query_count': query_count,
            'last_query_at': last_query.created_at if last_query else None
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики пользователя {telegram_id}: {e}")
        return {'error': str(e)}
    finally:
        db.close()

def check_database_health() -> bool:
    """
    Проверка работоспособности базы данных
    
    Returns:
        bool: True если БД работает
    """
    try:
        db = next(get_db_session())
        # Простой запрос для проверки подключения
        db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки БД: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def get_documents_count() -> int:
    """
    Получение количества документов в базе
    
    Returns:
        int: Количество документов
    """
    try:
        db = next(get_db_session())
        count = db.query(Document).filter(Document.status == 'completed').count()
        return count
    except Exception as e:
        logger.error(f"Ошибка подсчета документов: {e}")
        return 0
    finally:
        if 'db' in locals():
            db.close() 