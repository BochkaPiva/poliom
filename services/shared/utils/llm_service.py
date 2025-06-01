#!/usr/bin/env python3
"""
Сервис для работы с LLM моделями (GigaChat)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from .llm_client import SimpleLLMClient

logger = logging.getLogger(__name__)

class LLMService:
    """Сервис для работы с языковыми моделями (GigaChat)"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.api_key = os.getenv('GIGACHAT_API_KEY')
        if not self.api_key:
            logger.warning("GIGACHAT_API_KEY не найден. LLM функции будут недоступны.")
            self.client = None
        else:
            self.client = SimpleLLMClient(self.api_key)
    
    def format_search_answer(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        Форматирует результаты поиска в связный ответ
        
        Args:
            query: Исходный запрос пользователя
            search_results: Список результатов поиска с полями:
                - content: текст фрагмента
                - similarity: оценка релевантности
                - document_name: название документа
                - chunk_index: номер фрагмента
        
        Returns:
            Отформатированный ответ
        """
        if not self.client:
            return self._format_simple_answer(query, search_results)
        
        try:
            # Подготавливаем контекст для GigaChat
            context_parts = []
            for i, result in enumerate(search_results[:3], 1):  # Берем топ-3 результата
                context_parts.append(
                    f"Фрагмент {i} (релевантность: {result['similarity']:.3f}):\n"
                    f"{result['content']}\n"
                )
            
            context = "\n".join(context_parts)
            
            # Формируем вопрос для GigaChat
            formatted_question = f"""Пользователь спрашивает: "{query}"

Требования к ответу:
1. Отвечай кратко и по существу
2. Используй конкретные цифры и проценты из документа
3. Если в документе есть условия или ограничения - обязательно их упомяни
4. Пиши простым языком, понятным сотруднику
5. Если информации недостаточно для полного ответа - так и скажи

Дай краткий, точный и понятный ответ на основе предоставленной информации."""

            # Отправляем запрос к GigaChat
            response = self.client.generate_answer(
                context=context,
                question=formatted_question,
                max_tokens=500
            )
            
            if response.success:
                answer = response.text.strip()
                
                # Добавляем источники
                sources = []
                for result in search_results[:3]:
                    sources.append(f"📄 {result['document_name']} (фрагмент #{result['chunk_index']})")
                
                formatted_answer = f"{answer}\n\n📚 Источники:\n" + "\n".join(sources)
                
                return formatted_answer
            else:
                logger.error(f"Ошибка GigaChat: {response.error}")
                return self._format_simple_answer(query, search_results)
            
        except Exception as e:
            logger.error(f"Ошибка при обращении к GigaChat: {e}")
            return self._format_simple_answer(query, search_results)
    
    def _format_simple_answer(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        Простое форматирование без LLM (fallback)
        """
        if not search_results:
            return "❌ К сожалению, информация по вашему запросу не найдена."
        
        best_result = search_results[0]
        
        # Извлекаем ключевые данные
        content = best_result['content']
        
        # Простое извлечение числовых значений
        import re
        percentages = re.findall(r'\d+[.,]?\d*\s*процент|\d+[.,]?\d*\s*%', content)
        amounts = re.findall(r'\d+[.,]?\d*\s*руб', content)
        times = re.findall(r'\d+\s*час|\d+:\d+|с\s*\d+\s*до\s*\d+', content)
        
        answer_parts = []
        
        # Основной ответ
        if best_result['similarity'] >= 0.6:
            answer_parts.append("✅ Найдена релевантная информация:")
        else:
            answer_parts.append("⚠️ Найдена частично релевантная информация:")
        
        # Показываем ключевые данные
        if percentages:
            answer_parts.append(f"💰 Проценты: {', '.join(percentages)}")
        if amounts:
            answer_parts.append(f"💰 Суммы: {', '.join(amounts)}")
        if times:
            answer_parts.append(f"⏰ Время: {', '.join(times)}")
        
        # Показываем фрагмент текста
        answer_parts.append(f"\n📝 Из документа:")
        answer_parts.append(f'"{content[:300]}{"..." if len(content) > 300 else ""}"')
        
        # Источник
        answer_parts.append(f"\n📚 Источник: {best_result['document_name']} (фрагмент #{best_result['chunk_index']})")
        
        return "\n".join(answer_parts)
    
    def summarize_document(self, content: str, max_length: int = 200) -> str:
        """
        Создает краткое резюме документа
        """
        if not self.client:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        try:
            question = f"Создай краткое резюме этого документа об оплате труда (не более {max_length} символов). Резюме должно содержать основные положения о размерах оплаты, надбавках и условиях."

            response = self.client.generate_answer(
                context=content[:2000],  # Ограничиваем контекст
                question=question,
                max_tokens=100
            )
            
            if response.success:
                return response.text.strip()
            else:
                logger.error(f"Ошибка при создании резюме: {response.error}")
                return content[:max_length] + "..." if len(content) > max_length else content
            
        except Exception as e:
            logger.error(f"Ошибка при создании резюме: {e}")
            return content[:max_length] + "..." if len(content) > max_length else content
    
    def health_check(self) -> bool:
        """
        Проверка работоспособности LLM сервиса
        """
        if not self.client:
            return False
        
        try:
            return self.client.health_check()
        except Exception as e:
            logger.error(f"Ошибка при проверке здоровья LLM: {e}")
            return False 