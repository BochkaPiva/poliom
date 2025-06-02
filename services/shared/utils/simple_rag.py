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
    
    def search_relevant_chunks(self, question: str, limit: int = 15) -> List[Dict]:
        """
        Поиск релевантных чанков для ответа на вопрос
        
        Args:
            question: Вопрос пользователя
            limit: Максимальное количество чанков для возврата (уменьшено для лучшего качества)
        
        Returns:
            List[Dict]: Список релевантных чанков с метаданными
        """
        try:
            # 1. Создаем эмбеддинг для вопроса
            question_embedding = self.create_embedding(question)
            self.logger.info(f"Создан эмбеддинг для вопроса, размерность: {len(question_embedding)}")
            
            # 2. Выполняем векторный поиск
            self.logger.info("Пытаемся выполнить векторный поиск...")
            
            # Используем pgvector для поиска похожих эмбеддингов
            query = text("""
                SELECT dc.id, dc.document_id, dc.chunk_index, dc.content,
                       1 - (dc.embedding <=> :embedding) as similarity,
                       dc.content_length
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.processing_status = 'completed'
                  AND dc.embedding IS NOT NULL
                  AND dc.content_length > 100
                ORDER BY dc.embedding <=> :embedding
                LIMIT :limit
            """)
            
            result = self.db_session.execute(query, {
                'embedding': str(question_embedding),
                'limit': limit * 3  # Берем больше для фильтрации
            })
            
            vector_chunks = []
            for row in result:
                if row.similarity > 0.55:  # Повышаем порог схожести для лучшего качества
                    vector_chunks.append({
                        'id': row.id,
                        'document_id': row.document_id,
                        'chunk_index': row.chunk_index,
                        'content': row.content,
                        'similarity': row.similarity,
                        'search_type': 'vector',
                        'content_length': row.content_length
                    })
            
            self.logger.info(f"Векторный поиск завершен, найдено {len(vector_chunks)} чанков")
            
            # 3. Дополняем текстовым поиском только если векторный поиск дал мало результатов
            text_chunks = []
            
            if len(vector_chunks) < limit // 2:  # Если найдено меньше половины от лимита
                # Извлекаем ключевые слова из вопроса
                keywords = self._extract_keywords(question)
                
                if keywords:
                    self.logger.info(f"Выполняем текстовый поиск по ключевым словам: {keywords}")
                    
                    # Строим запрос для текстового поиска
                    conditions = []
                    params = {}
                    
                    for i, keyword in enumerate(keywords):
                        param_name = f'keyword_{i}'
                        conditions.append(f"dc.content ILIKE :{param_name}")
                        params[param_name] = f'%{keyword}%'
                    
                    text_query = text(f"""
                        SELECT DISTINCT dc.id, dc.document_id, dc.chunk_index, dc.content,
                               0.7 as similarity, dc.content_length
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE d.processing_status = 'completed'
                          AND dc.content_length > 100
                          AND ({' OR '.join(conditions)})
                        LIMIT :limit
                    """)
                    
                    params['limit'] = limit
                    text_result = self.db_session.execute(text_query, params)
                    
                    for row in text_result:
                        # Проверяем, что этот чанк еще не найден векторным поиском
                        if not any(chunk['id'] == row.id for chunk in vector_chunks):
                            text_chunks.append({
                                'id': row.id,
                                'document_id': row.document_id,
                                'chunk_index': row.chunk_index,
                                'content': row.content,
                                'similarity': row.similarity,
                                'search_type': 'text',
                                'content_length': row.content_length
                            })
                    
                    self.logger.info(f"Текстовый поиск завершен, найдено {len(text_chunks)} дополнительных чанков")
            
            # 4. Объединяем результаты и сортируем по релевантности
            all_chunks = vector_chunks + text_chunks
            
            # Сортируем по схожести (убывание)
            all_chunks.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Ограничиваем количество результатов
            final_chunks = all_chunks[:limit]
            
            if not final_chunks:
                self.logger.info("Векторный и текстовый поиск не дали результатов, используем fallback")
                return self._fallback_search(question, limit)
            
            return final_chunks
            
        except Exception as e:
            self.logger.error(f"Ошибка в search_relevant_chunks: {str(e)}")
            return self._fallback_search(question, limit)
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Извлечение ключевых слов из вопроса"""
        # Расширенный словарь синонимов для лучшего поиска
        synonyms = {
            'аванс': ['аванс', 'авансовая', 'авансовый', 'первая часть', 'первая половина', 'предоплата'],
            'зарплата': ['зарплата', 'заработная плата', 'оплата труда', 'вознаграждение', 'зп'],
            'выплата': ['выплата', 'выплачивается', 'перечисление', 'начисление', 'выдача'],
            'дата': ['дата', 'число', 'срок', 'время', 'когда', 'день'],
            'размер': ['размер', 'сумма', 'процент', 'сколько', 'величина'],
            'отпуск': ['отпуск', 'отпускные', 'отдых', 'каникулы'],
            'больничный': ['больничный', 'болезнь', 'нетрудоспособность', 'лист нетрудоспособности'],
            'премия': ['премия', 'бонус', 'поощрение', 'надбавка'],
            'договор': ['договор', 'контракт', 'соглашение', 'трудовой договор'],
            'увольнение': ['увольнение', 'расторжение', 'прекращение', 'уход'],
            'график': ['график', 'расписание', 'режим', 'время работы'],
            'документы': ['документы', 'справки', 'бумаги', 'формы']
        }
        
        question_lower = question.lower()
        keywords = set()
        
        # Ищем прямые совпадения с синонимами
        for base_word, word_list in synonyms.items():
            for word in word_list:
                if word in question_lower:
                    keywords.update([base_word])  # Добавляем базовое слово
                    keywords.add(word)  # И само найденное слово
                    break
        
        # Добавляем числа (даты, проценты)
        import re
        numbers = re.findall(r'\b\d{1,2}\b', question)
        for num in numbers:
            keywords.add(num)
        
        # Добавляем важные слова длиннее 3 символов
        words = re.findall(r'\b[а-яё]{4,}\b', question_lower)
        stop_words = {'когда', 'какой', 'какая', 'какие', 'сколько', 'почему', 'зачем', 'откуда', 'куда'}
        for word in words:
            if word not in stop_words:
                keywords.add(word)
        
        return list(keywords)[:10]  # Ограничиваем количество ключевых слов
    
    def _fallback_search(self, question: str, limit: int) -> List[Dict]:
        """Резервный поиск при отсутствии результатов"""
        try:
            self.logger.info("Используем текстовый поиск как fallback")
            
            # Простой текстовый поиск по содержимому
            query = text("""
                SELECT dc.id, dc.document_id, dc.chunk_index, dc.content,
                       0.5 as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.processing_status = 'completed'
                  AND (dc.content ILIKE :search_term1 
                       OR dc.content ILIKE :search_term2
                       OR dc.content ILIKE :search_term3)
                LIMIT :limit
            """)
            
            # Извлекаем основные слова из вопроса
            words = question.lower().split()
            search_terms = [f'%{word}%' for word in words if len(word) > 2][:3]
            
            if not search_terms:
                return []
            
            params = {
                'search_term1': search_terms[0] if len(search_terms) > 0 else '%',
                'search_term2': search_terms[1] if len(search_terms) > 1 else search_terms[0],
                'search_term3': search_terms[2] if len(search_terms) > 2 else search_terms[0],
                'limit': limit
            }
            
            result = self.db_session.execute(query, params)
            
            chunks = []
            for row in result:
                chunks.append({
                    'id': row.id,
                    'document_id': row.document_id,
                    'chunk_index': row.chunk_index,
                    'content': row.content,
                    'similarity': row.similarity,
                    'search_type': 'fallback'
                })
            
            self.logger.info(f"Текстовый поиск завершен, найдено {len(chunks)} чанков")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Ошибка в fallback поиске: {str(e)}")
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
            
            # ОТЛАДКА: Выводим контекст в лог
            self.logger.info(f"🔍 КОНТЕКСТ ДЛЯ LLM (длина: {len(context)} символов):")
            self.logger.info("="*80)
            self.logger.info(context[:1000] + "..." if len(context) > 1000 else context)
            self.logger.info("="*80)
            
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
            
            # 4. Формируем источники с дедупликацией
            sources = []
            seen_documents = set()
            
            for chunk in relevant_chunks:
                document = self.db_session.query(Document).filter(
                    Document.id == chunk['document_id']
                ).first()
                
                if document and document.title not in seen_documents:
                    sources.append({
                        'title': document.title,
                        'chunk_index': chunk['chunk_index'],
                        'document_id': document.id
                    })
                    seen_documents.add(document.title)
            
            # 5. Постобработка ответа для улучшения форматирования
            formatted_answer = self._post_process_answer(llm_response.text)

            # 6. Логируем запрос (опционально)
            if user_id:
                self._log_query(user_id, question, formatted_answer, len(relevant_chunks))

            return {
                'answer': formatted_answer,
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
    
    def _post_process_answer(self, answer: str) -> str:
        """
        Постобработка ответа для правильного форматирования
        
        Args:
            answer: Исходный ответ от LLM
            
        Returns:
            str: Обработанный ответ
        """
        # Экранируем все специальные символы для Telegram MarkdownV2
        # Список символов, которые нужно экранировать: _ * [ ] ( ) ~ ` > # + - = | { } . !
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in escape_chars:
            answer = answer.replace(char, f'\\{char}')
        
        # Убираем лишние пробелы и переносы
        answer = answer.strip()
        
        # Убираем возможные дублирующиеся фразы
        lines = answer.split('\n')
        unique_lines = []
        seen_lines = set()
        
        for line in lines:
            line_clean = line.strip().lower()
            if line_clean and line_clean not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(line_clean)
        
        return '\n'.join(unique_lines)
    
    def _log_query(self, user_id: int, question: str, answer: str, chunks_count: int):
        """Логирование запроса пользователя"""
        try:
            from shared.models.query_log import QueryLog
            
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