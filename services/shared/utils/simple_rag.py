# services/shared/utils/simple_rag.py

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models.document import Document, DocumentChunk
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
        Инициализация простой RAG системы
        
        Args:
            db_session: Сессия базы данных
            gigachat_api_key: API ключ для GigaChat
        """
        self.db = db_session
        self.llm_client = SimpleLLMClient(gigachat_api_key)
        
        # Загружаем локальную модель эмбеддингов (один раз)
        logger.info("Загружаем модель эмбеддингов...")
        self.embeddings_model = SentenceTransformer('ai-forever/sbert_large_nlu_ru')
        logger.info("Модель эмбеддингов загружена!")
        
    def create_embedding(self, text: str) -> List[float]:
        """Создание эмбеддинга для текста"""
        try:
            embedding = self.embeddings_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддинга: {str(e)}")
            return []
    
    def search_relevant_chunks(self, 
                              question: str, 
                              limit: int = 5,
                              similarity_threshold: float = 0.7) -> List[DocumentChunk]:
        """
        Поиск релевантных чанков документов
        
        Args:
            question: Вопрос пользователя
            limit: Максимальное количество чанков
            similarity_threshold: Порог схожести
            
        Returns:
            List[DocumentChunk]: Список релевантных чанков
        """
        try:
            # Создаем эмбеддинг для вопроса
            question_embedding = self.create_embedding(question)
            if not question_embedding:
                return []
            
            # Поиск похожих чанков через pgvector
            query = text("""
                SELECT id, document_id, content, chunk_index, 
                       1 - (embedding <=> :question_embedding) as similarity
                FROM document_chunks 
                WHERE 1 - (embedding <=> :question_embedding) > :threshold
                ORDER BY embedding <=> :question_embedding
                LIMIT :limit
            """)
            
            result = self.db.execute(query, {
                'question_embedding': question_embedding,
                'threshold': similarity_threshold,
                'limit': limit
            })
            
            chunk_ids = [row[0] for row in result]
            
            # Получаем полные объекты чанков
            chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.id.in_(chunk_ids)
            ).all()
            
            logger.info(f"Найдено {len(chunks)} релевантных чанков для вопроса: {question[:50]}...")
            return chunks
            
        except Exception as e:
            logger.error(f"Ошибка поиска чанков: {str(e)}")
            return []
    
    def format_context(self, chunks: List[DocumentChunk]) -> str:
        """Форматирование контекста из найденных чанков"""
        if not chunks:
            return "Информация не найдена."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            # Получаем название документа
            document = self.db.query(Document).filter(
                Document.id == chunk.document_id
            ).first()
            
            doc_title = document.title if document else "Неизвестный документ"
            
            context_parts.append(
                f"[Источник {i}: {doc_title}]\n{chunk.content}\n"
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
            logger.info(f"Обрабатываем вопрос: {question[:100]}...")
            
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
                document = self.db.query(Document).filter(
                    Document.id == chunk.document_id
                ).first()
                
                if document:
                    sources.append({
                        'title': document.title,
                        'chunk_index': chunk.chunk_index,
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
            logger.error(f"Ошибка в answer_question: {str(e)}")
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
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка логирования запроса: {str(e)}")
    
    def health_check(self) -> Dict[str, bool]:
        """Проверка работоспособности всех компонентов"""
        return {
            'embeddings_model': self.embeddings_model is not None,
            'llm_client': self.llm_client.health_check(),
            'database': self._check_database()
        }
    
    def _check_database(self) -> bool:
        """Проверка подключения к базе данных"""
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False 