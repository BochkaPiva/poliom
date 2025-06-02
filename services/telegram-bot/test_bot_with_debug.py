#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from bot.config import config
from bot.rag_service import RAGService

# Настройка логирования точно как в боте
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def is_blocked_response(response: str) -> bool:
    """Точно такая же функция как в handlers.py"""
    blocked_phrases = [
        "Генеративные языковые модели не обладают собственным мнением",
        "разговоры на чувствительные темы могут быть ограничены",
        "разговоры на некоторые темы временно ограничены",
        "Как и любая языковая модель, GigaChat не обладает собственным мнением",
        "К сожалению, иногда генеративные языковые модели могут создавать некорректные ответы",
        "ответы на вопросы, связанные с чувствительными темами, временно ограничены",
        "во избежание неправильного толкования, ответы на вопросы, связанные с чувствительными темами, временно ограничены"
    ]
    
    # Также проверяем на неполные ответы без конкретных дат для вопросов о зарплате
    if any(phrase in response for phrase in blocked_phrases):
        return True
    
    # Дополнительная проверка для ответов о зарплате без конкретных дат
    if ("заработная плата выплачивается два раза в месяц" in response.lower() and 
        "сроки выплаты" in response.lower() and 
        "устанавливаются в правилах" in response.lower() and
        not any(date in response for date in ['12', '27', '15'])):
        return True
    
    return False

async def test_bot_logic():
    """Тестирование точно такой же логики как в боте"""
    
    print("🤖 ТЕСТИРОВАНИЕ ЛОГИКИ БОТА")
    print("=" * 60)
    
    # Инициализация RAG сервиса
    print("🔄 Инициализация RAG сервиса...")
    rag_service = RAGService(config.GIGACHAT_API_KEY)
    await rag_service.initialize()
    print("✅ RAG сервис инициализирован\n")
    
    # Проблемные вопросы пользователя
    test_questions = [
        "Какие выплаты есть к юбилейным датам?",
        "Отпуск",
        "Юбилейные даты",
        "Когда я могу оформить отпуск"
    ]
    
    for i, message_text in enumerate(test_questions, 1):
        print(f"\n{i}. Вопрос: '{message_text}'")
        print("-" * 50)
        
        try:
            # Получаем ответ от RAG системы - точно как в боте
            result = await rag_service.answer_question(message_text, user_id=123)
            
            # Проверяем качество результата - точно как в боте
            if not result or 'answer' not in result:
                response_text = "❌ Извините, не удалось обработать ваш запрос. Попробуйте переформулировать вопрос."
                print(f"❌ Результат: {response_text}")
                continue
            
            # Логируем полученные данные для отладки
            chunks = result.get('chunks', [])
            logger.info(f"Получено {len(chunks)} чанков от RAG системы")
            
            # Проверяем релевантность найденных чанков
            relevant_chunks = []
            
            if chunks:
                # Фильтруем чанки по схожести с более мягкими порогами
                for j, chunk in enumerate(chunks):
                    similarity = chunk.get('similarity', 0)
                    logger.info(f"Чанк {j+1}: similarity={similarity}")
                    
                    if similarity >= 0.25:  # Еще больше снижен порог для отладки
                        relevant_chunks.append(chunk)
                        logger.info(f"Чанк {j+1} добавлен как релевантный (similarity={similarity})")
                    else:
                        # Проверяем, содержит ли чанк ключевые слова из вопроса
                        question_words = set(message_text.lower().split())
                        chunk_words = set(chunk.get('content', '').lower().split())
                        
                        # Если есть пересечение ключевых слов, добавляем чанк
                        overlap = question_words & chunk_words
                        if len(overlap) >= 1:
                            relevant_chunks.append(chunk)
                            logger.info(f"Чанк {j+1} добавлен по ключевым словам: {overlap}")
            
            # Логируем итоговое количество релевантных чанков
            logger.info(f"Итого релевантных чанков: {len(relevant_chunks)}")
            logger.info(f"Ответ GigaChat заблокирован: {is_blocked_response(result['answer'])}")
            
            print(f"📊 Статистика:")
            print(f"   • Найдено чанков: {len(chunks)}")
            print(f"   • Релевантных чанков: {len(relevant_chunks)}")
            print(f"   • GigaChat заблокирован: {is_blocked_response(result['answer'])}")
            print(f"   • Ответ GigaChat: {result['answer'][:100]}...")
            
            # Упрощенная логика обработки ответов - точно как в боте
            if len(relevant_chunks) > 0:
                if is_blocked_response(result['answer']):
                    logger.info("GigaChat заблокирован, используем extract_key_information")
                    response_text = "🔧 Извлечение информации из контекста (GigaChat заблокирован)"
                else:
                    logger.info("Используем ответ GigaChat")
                    response_text = result['answer']
                    
                    # Добавляем источники
                    if result.get('sources'):
                        response_text += "\n\n📚 **Источники:**"
                        for j, source in enumerate(result['sources'], 1):
                            title = source.get('title', 'Документ')
                            response_text += f"\n{j}. {title}"
            else:
                logger.info("Нет релевантных чанков - возвращаем сообщение о том, что информация не найдена")
                response_text = "🔍 **Информация не найдена**"
            
            print(f"✅ Финальный ответ: {response_text[:200]}...")
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_logic()) 