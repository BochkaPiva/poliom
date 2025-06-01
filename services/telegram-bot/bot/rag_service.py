"""
Асинхронный сервис для работы с RAG системой
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Добавляем путь к shared модулям (исправлено для Docker)
sys.path.append('/app/shared')

from utils.simple_rag import SimpleRAG
from utils.llm_client import SimpleLLMClient
from models.document import Document, DocumentChunk
from .database import get_db_session

logger = logging.getLogger(__name__)

class RAGService:
    """
    Асинхронный сервис для работы с RAG системой
    Адаптер между синхронной RAG системой и асинхронным ботом
    """
    
    def __init__(self, gigachat_api_key: str):
        self.gigachat_api_key = gigachat_api_key
        self.rag_system = None
        self.initialized = False
    
    async def initialize(self):
        """Инициализация RAG системы"""
        if self.initialized:
            return
        
        try:
            logger.info("🔄 Инициализируем RAG систему...")
            
            # Получаем синхронную сессию БД
            db_session = next(get_db_session())
            
            # Создаем RAG систему в отдельном потоке
            loop = asyncio.get_event_loop()
            self.rag_system = await loop.run_in_executor(
                None, 
                self._create_rag_system, 
                db_session
            )
            
            self.initialized = True
            logger.info("✅ RAG система инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации RAG системы: {e}")
            raise
    
    def _create_rag_system(self, db_session):
        """Создание RAG системы (синхронно)"""
        return SimpleRAG(db_session, self.gigachat_api_key)
    
    async def answer_question(self, question: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Асинхронный ответ на вопрос пользователя
        
        Args:
            question: Вопрос пользователя
            user_id: ID пользователя Telegram
            
        Returns:
            Dict с ответом и метаданными
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Выполняем поиск ответа в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.rag_system.answer_question,
                question,
                user_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения ответа: {e}")
            return {
                'answer': 'Произошла ошибка при обработке вашего вопроса.',
                'sources': [],
                'success': False,
                'error': str(e),
                'tokens_used': 0
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка работоспособности RAG системы
        
        Returns:
            Dict со статусом компонентов
        """
        if not self.initialized:
            try:
                await self.initialize()
            except Exception as e:
                return {
                    'overall': False,
                    'llm': False,
                    'embeddings': False,
                    'database': False,
                    'documents_count': None,
                    'error': str(e)
                }
        
        try:
            # Проверяем статус в отдельном потоке
            loop = asyncio.get_event_loop()
            status = await loop.run_in_executor(
                None,
                self.rag_system.health_check
            )
            
            # Получаем количество документов
            documents_count = await self._get_documents_count()
            
            overall_status = all([
                status['embeddings_model'],
                status['llm_client'],
                status['database']
            ])
            
            return {
                'overall': overall_status,
                'llm': status['llm_client'],
                'embeddings': status['embeddings_model'],
                'database': status['database'],
                'documents_count': documents_count
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки статуса: {e}")
            return {
                'overall': False,
                'llm': False,
                'embeddings': False,
                'database': False,
                'documents_count': None,
                'error': str(e)
            }
    
    async def _get_documents_count(self) -> Optional[int]:
        """Получение количества документов в базе"""
        try:
            loop = asyncio.get_event_loop()
            count = await loop.run_in_executor(
                None,
                self._count_documents_sync
            )
            return count
        except Exception as e:
            logger.error(f"Ошибка подсчета документов: {e}")
            return None
    
    def _count_documents_sync(self) -> int:
        """Синхронный подсчет документов"""
        try:
            db_session = next(get_db_session())
            count = db_session.query(Document).filter(
                Document.status == 'completed'
            ).count()
            return count
        except Exception as e:
            logger.error(f"Ошибка подсчета документов: {e}")
            return 0
    
    async def search_documents(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Поиск документов по запросу
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            
        Returns:
            Dict с результатами поиска
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                None,
                self.rag_system.search_relevant_chunks,
                query,
                limit
            )
            
            # Группируем чанки по документам
            documents = {}
            for chunk in chunks:
                doc_id = chunk.document_id
                if doc_id not in documents:
                    # Получаем информацию о документе
                    doc_info = await self._get_document_info(doc_id)
                    if doc_info:
                        documents[doc_id] = {
                            'title': doc_info['title'],
                            'chunks': []
                        }
                
                if doc_id in documents:
                    documents[doc_id]['chunks'].append({
                        'content': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                        'chunk_index': chunk.chunk_index
                    })
            
            return {
                'success': True,
                'documents': list(documents.values()),
                'total_found': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Ошибка поиска документов: {e}")
            return {
                'success': False,
                'documents': [],
                'total_found': 0,
                'error': str(e)
            }
    
    async def _get_document_info(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о документе"""
        try:
            loop = asyncio.get_event_loop()
            doc_info = await loop.run_in_executor(
                None,
                self._get_document_info_sync,
                document_id
            )
            return doc_info
        except Exception as e:
            logger.error(f"Ошибка получения информации о документе {document_id}: {e}")
            return None
    
    def _get_document_info_sync(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Синхронное получение информации о документе"""
        try:
            db_session = next(get_db_session())
            document = db_session.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if document:
                return {
                    'id': document.id,
                    'title': document.title,
                    'file_type': document.file_type,
                    'created_at': document.created_at
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения документа {document_id}: {e}")
            return None 