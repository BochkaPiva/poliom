# services/shared/utils/simple_rag.py

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text

# Исправляем импорт на абсолютный
try:
    from services.shared.models.document import Document, DocumentChunk
except ImportError:
    # Fallback для случая, если модуль не найден
    from models.document import Document, DocumentChunk

from .llm_client import SimpleLLMClient, LLMResponse

logger = logging.getLogger(__name__)

class SimpleRAG:
    """
    Максимально простая RAG система
    - Локальные эмбеддинги (бесплатно)
    - GigaChat для ответов (бесплатно)
    - Никаких сложностей!
    """
    
    def __init__(self, db_session: Session, gigachat_api_key: str):
        """
        Инициализация RAG системы
        
        Args:
            db_session: Сессия базы данных
            gigachat_api_key: API ключ для GigaChat
        """
        self.db_session = db_session
        self.llm_client = SimpleLLMClient(gigachat_api_key)
        self.similarity_threshold = 0.5  # Порог схожести для векторного поиска
        
        # Инициализируем логгер
        self.logger = logging.getLogger(__name__)
        
        # Загружаем модель эмбеддингов
        self.logger.info("Загружаем модель эмбеддингов...")
        self.embedding_model = SentenceTransformer('cointegrated/rubert-tiny2')
        self.logger.info("Модель эмбеддингов загружена!")
        
    def create_embedding(self, text: str) -> List[float]:
        """Создание эмбеддинга для текста"""
        try:
            embedding = self.embedding_model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Ошибка создания эмбеддинга: {e}")
            return []
    
    def search_relevant_chunks(self, question: str, limit: int = 5) -> List[Dict]:
        """Поиск релевантных чанков для вопроса"""
        try:
            self.logger.info(f"Обрабатываем вопрос: {question}...")
            
            # Создаем эмбеддинг для вопроса
            question_embedding = self.create_embedding(question)
            self.logger.info(f"Создан эмбеддинг для вопроса, размерность: {len(question_embedding)}")
            
            # Пытаемся выполнить векторный поиск
            try:
                self.logger.info("Пытаемся выполнить векторный поиск...")
                
                # Используем прямой SQL без параметров для vector
                embedding_str = '[' + ','.join(map(str, question_embedding)) + ']'
                
                vector_query = text(f"""
                    SELECT id, document_id, content, chunk_index,
                           1 - (embedding <=> '{embedding_str}'::vector) as similarity
                    FROM document_chunks
                    WHERE 1 - (embedding <=> '{embedding_str}'::vector) > :threshold
                    ORDER BY embedding <=> '{embedding_str}'::vector
                    LIMIT :limit
                """)
                
                result = self.db_session.execute(
                    vector_query,
                    {
                        'threshold': self.similarity_threshold,
                        'limit': limit
                    }
                )
                
                chunks = []
                for row in result:
                    chunks.append({
                        'id': row.id,
                        'document_id': row.document_id,
                        'content': row.content,
                        'chunk_index': row.chunk_index,
                        'similarity': float(row.similarity)
                    })
                
                if chunks:
                    self.logger.info(f"Векторный поиск завершен, найдено {len(chunks)} чанков")
                    return chunks
                else:
                    self.logger.info("Векторный поиск не дал результатов, переходим к текстовому поиску")
                    
            except Exception as e:
                self.logger.warning(f"Векторный поиск не удался: {e}, переходим к текстовому поиску")
                self.db_session.rollback()
            
            # Fallback к текстовому поиску
            self.logger.info("Используем текстовый поиск как fallback")
            
            # Простой текстовый поиск по содержимому
            text_query = text("""
                SELECT id, document_id, content, chunk_index
                FROM document_chunks
                WHERE content ILIKE :search_pattern
                ORDER BY char_length(content)
                LIMIT :limit
            """)
            
            search_pattern = f"%{question}%"
            result = self.db_session.execute(
                text_query,
                {'search_pattern': search_pattern, 'limit': limit}
            )
            
            chunks = []
            for row in result:
                chunks.append({
                    'id': row.id,
                    'document_id': row.document_id,
                    'content': row.content,
                    'chunk_index': row.chunk_index,
                    'similarity': 0.5  # Фиксированная схожесть для текстового поиска
                })
            
            self.logger.info(f"Текстовый поиск завершен, найдено {len(chunks)} чанков")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Ошибка при поиске чанков: {e}")
            self.db_session.rollback()
            return []
    
    def format_context(self, chunks: List[DocumentChunk]) -> str:
        """Форматирование контекста из найденных чанков"""
        if not chunks:
            return "Информация не найдена."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            # Получаем название документа
            document = self.db_session.query(Document).filter(
                Document.id == chunk['document_id']
            ).first()
            
            doc_title = document.title if document else "Неизвестный документ"
            
            context_parts.append(
                f"[Источник {i}: {doc_title}]\n{chunk['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    def answer_question(self, 
                       question: str,
                       user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Главная функция - ответ на вопрос пользователя
        
        Args:
            question: Вопрос пользователя
            user_id: ID пользователя (для логирования)
            
        Returns:
            Dict с ответом и метаданными
        """
        try:
            self.logger.info(f"Обрабатываем вопрос: {question[:100]}...")
            
            # 1. Ищем релевантные документы
            relevant_chunks = self.search_relevant_chunks(question)
            
            if not relevant_chunks:
                return {
                    'answer': 'К сожалению, я не нашел информации по вашему вопросу в корпоративной базе знаний. Попробуйте переформулировать вопрос или обратитесь к HR-отделу.',
                    'sources': [],
                    'success': True,
                    'tokens_used': 0
                }
            
            # 2. Формируем контекст
            context = self.format_context(relevant_chunks)
            
            # 3. Получаем ответ от LLM
            llm_response = self.llm_client.generate_answer(
                context=context,
                question=question
            )
            
            if not llm_response.success:
                return {
                    'answer': 'Извините, произошла ошибка при генерации ответа. Попробуйте позже.',
                    'sources': [],
                    'success': False,
                    'error': llm_response.error,
                    'tokens_used': 0
                }
            
            # 4. Формируем источники
            sources = []
            for chunk in relevant_chunks:
                document = self.db_session.query(Document).filter(
                    Document.id == chunk['document_id']
                ).first()
                
                if document:
                    sources.append({
                        'title': document.title,
                        'chunk_index': chunk['chunk_index'],
                        'document_id': document.id
                    })
            
            # 5. Логируем запрос (опционально)
            if user_id:
                self._log_query(user_id, question, llm_response.text, len(relevant_chunks))
            
            return {
                'answer': llm_response.text,
                'sources': sources,
                'success': True,
                'tokens_used': llm_response.tokens_used,
                'chunks_found': len(relevant_chunks)
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка в answer_question: {str(e)}")
            return {
                'answer': 'Произошла техническая ошибка. Обратитесь к администратору.',
                'sources': [],
                'success': False,
                'error': str(e),
                'tokens_used': 0
            }
    
    def _log_query(self, user_id: int, question: str, answer: str, chunks_count: int):
        """Логирование запроса пользователя"""
        try:
            from ..models.query_log import QueryLog
            
            log_entry = QueryLog(
                user_id=user_id,
                query_text=question,
                response_text=answer,
                chunks_used=chunks_count,
                model_used="GigaChat"
            )
            
            self.db_session.add(log_entry)
            self.db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Ошибка логирования запроса: {str(e)}")
    
    def health_check(self) -> Dict[str, bool]:
        """Проверка работоспособности всех компонентов"""
        return {
            'embeddings_model': self.embedding_model is not None,
            'llm_client': self.llm_client.health_check(),
            'database': self._check_database()
        }
    
    def _check_database(self) -> bool:
        """Проверка подключения к базе данных"""
        try:
            self.db_session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False 