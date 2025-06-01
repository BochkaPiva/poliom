#!/usr/bin/env python3
"""
Полноценная демонстрация системы поиска
Показывает работу как с LLM, так и с fallback форматированием
"""

import sys
import os
from pathlib import Path
import time

# Добавляем путь к services для импорта модулей
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения из корневого .env файла
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from shared.utils.search_service import SearchService

def print_header():
    """Красивый заголовок"""
    print("🔍" + "=" * 58 + "🔍")
    print("🚀        ДЕМОНСТРАЦИЯ СИСТЕМЫ ПОИСКА POLIOM        🚀")
    print("🔍" + "=" * 58 + "🔍")
    print()

def print_section(title):
    """Красивый заголовок секции"""
    print(f"\n{'🎯 ' + title + ' 🎯':^60}")
    print("─" * 60)

def print_query_result(query, result, query_num, total_queries):
    """Красиво выводит результат запроса"""
    print(f"\n📋 ЗАПРОС {query_num}/{total_queries}")
    print(f"❓ Вопрос: \"{query}\"")
    print("─" * 50)
    
    # Показываем метрики
    print(f"📊 Качество поиска: {result['search_quality'].upper()}")
    print(f"📈 Лучшая схожесть: {result['best_similarity']:.1%}")
    print(f"📄 Найдено результатов: {len(result['results'])}")
    
    if result['results']:
        best = result['results'][0]
        print(f"📚 Источник: {best['document_name']}")
        print(f"🧩 Фрагмент: #{best['chunk_index']}")
    
    print("\n💬 ОТВЕТ СИСТЕМЫ:")
    print("┌" + "─" * 48 + "┐")
    
    # Разбиваем ответ на строки для красивого вывода
    answer_lines = result['formatted_answer'].split('\n')
    for line in answer_lines:
        if len(line) <= 46:
            print(f"│ {line:<46} │")
        else:
            # Разбиваем длинные строки
            words = line.split(' ')
            current_line = ""
            for word in words:
                if len(current_line + word) <= 46:
                    current_line += word + " "
                else:
                    if current_line:
                        print(f"│ {current_line.strip():<46} │")
                    current_line = word + " "
            if current_line:
                print(f"│ {current_line.strip():<46} │")
    
    print("└" + "─" * 48 + "┘")

def demo_search_queries():
    """Демонстрирует различные типы поисковых запросов"""
    print_section("ТЕСТИРОВАНИЕ РАЗЛИЧНЫХ ЗАПРОСОВ")
    
    # Инициализируем сервис поиска
    search_service = SearchService()
    
    # Набор тестовых запросов разной сложности
    test_queries = [
        {
            "query": "Сколько процентов доплата за ночную работу?",
            "description": "Поиск конкретного числового значения"
        },
        {
            "query": "Как оплачивается работа в праздничные дни?",
            "description": "Поиск информации о процедурах"
        },
        {
            "query": "Какой размер надбавки за вредные условия труда?",
            "description": "Поиск размера компенсации"
        },
        {
            "query": "отпускные выплаты",
            "description": "Простой поиск по ключевым словам"
        },
        {
            "query": "командировочные расходы сотрудников",
            "description": "Поиск по составному запросу"
        }
    ]
    
    print(f"🎯 Будет протестировано {len(test_queries)} запросов")
    print("⏱️ Начинаем тестирование...\n")
    
    results_summary = []
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        description = test_case["description"]
        
        print(f"🔄 Обрабатываем запрос {i}/{len(test_queries)}: {description}")
        
        try:
            # Засекаем время
            start_time = time.time()
            result = search_service.search(query, max_results=3, min_similarity=0.3)
            end_time = time.time()
            
            # Добавляем время выполнения
            result['execution_time'] = end_time - start_time
            
            # Выводим результат
            print_query_result(query, result, i, len(test_queries))
            
            # Сохраняем для итогового отчета
            results_summary.append({
                'query': query,
                'quality': result['search_quality'],
                'similarity': result['best_similarity'],
                'results_count': len(result['results']),
                'execution_time': result['execution_time']
            })
            
            print(f"⏱️ Время выполнения: {result['execution_time']:.2f} сек")
            
        except Exception as e:
            print(f"❌ Ошибка при обработке запроса: {e}")
            results_summary.append({
                'query': query,
                'quality': 'error',
                'similarity': 0,
                'results_count': 0,
                'execution_time': 0
            })
        
        # Небольшая пауза между запросами
        if i < len(test_queries):
            time.sleep(0.5)
    
    return results_summary

def demo_context_search():
    """Демонстрирует поиск с контекстом"""
    print_section("ПОИСК С РАСШИРЕННЫМ КОНТЕКСТОМ")
    
    search_service = SearchService()
    
    query = "доплата за ночную работу"
    print(f"🔍 Запрос с контекстом: \"{query}\"")
    print("📝 Система найдет основной фрагмент и добавит соседние для полноты картины")
    
    try:
        result = search_service.search_with_context(query, context_size=2)
        
        print(f"\n📊 Результат:")
        print(f"   • Качество: {result['search_quality'].upper()}")
        print(f"   • Основных результатов: {len(result['results'])}")
        
        if 'context_chunks' in result:
            print(f"   • Контекстных фрагментов: {len(result['context_chunks'])}")
        
        print(f"\n💬 ОТВЕТ С КОНТЕКСТОМ:")
        print("┌" + "─" * 58 + "┐")
        
        # Выводим ответ с контекстом
        context_lines = result['formatted_answer'].split('\n')
        for line in context_lines:
            if len(line) <= 56:
                print(f"│ {line:<56} │")
            else:
                # Разбиваем длинные строки
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + word) <= 56:
                        current_line += word + " "
                    else:
                        if current_line:
                            print(f"│ {current_line.strip():<56} │")
                        current_line = word + " "
                if current_line:
                    print(f"│ {current_line.strip():<56} │")
        
        print("└" + "─" * 58 + "┘")
        
    except Exception as e:
        print(f"❌ Ошибка при поиске с контекстом: {e}")

def print_summary(results_summary):
    """Выводит итоговый отчет"""
    print_section("ИТОГОВЫЙ ОТЧЕТ")
    
    if not results_summary:
        print("❌ Нет данных для отчета")
        return
    
    # Подсчитываем статистику
    total_queries = len(results_summary)
    successful_queries = len([r for r in results_summary if r['quality'] != 'error'])
    avg_similarity = sum(r['similarity'] for r in results_summary) / total_queries if total_queries > 0 else 0
    avg_time = sum(r['execution_time'] for r in results_summary) / total_queries if total_queries > 0 else 0
    
    # Качество запросов
    quality_counts = {}
    for result in results_summary:
        quality = result['quality']
        quality_counts[quality] = quality_counts.get(quality, 0) + 1
    
    print(f"📊 СТАТИСТИКА ТЕСТИРОВАНИЯ:")
    print(f"   • Всего запросов: {total_queries}")
    print(f"   • Успешных: {successful_queries}")
    print(f"   • Средняя схожесть: {avg_similarity:.1%}")
    print(f"   • Среднее время: {avg_time:.2f} сек")
    
    print(f"\n📈 РАСПРЕДЕЛЕНИЕ ПО КАЧЕСТВУ:")
    for quality, count in quality_counts.items():
        percentage = (count / total_queries) * 100
        print(f"   • {quality.upper()}: {count} ({percentage:.1f}%)")
    
    print(f"\n🎯 ДЕТАЛИЗАЦИЯ ПО ЗАПРОСАМ:")
    for i, result in enumerate(results_summary, 1):
        status = "✅" if result['quality'] != 'error' else "❌"
        print(f"   {status} Запрос {i}: {result['similarity']:.1%} схожести, {result['results_count']} результатов")

def main():
    """Основная функция демонстрации"""
    print_header()
    
    # Проверяем статус LLM
    gigachat_key = os.getenv('GIGACHAT_API_KEY')
    if gigachat_key:
        print("🤖 GigaChat API ключ найден")
        print("💡 Система будет пытаться использовать LLM для форматирования")
        print("🔄 При недоступности LLM будет использоваться fallback форматирование")
    else:
        print("⚠️ GigaChat API ключ не найден")
        print("🔄 Будет использоваться fallback форматирование")
    
    try:
        # Основная демонстрация
        results = demo_search_queries()
        
        # Демонстрация поиска с контекстом
        demo_context_search()
        
        # Итоговый отчет
        print_summary(results)
        
        print_section("ЗАКЛЮЧЕНИЕ")
        print("🎉 Демонстрация завершена успешно!")
        print("📈 Система поиска готова к использованию")
        print("🚀 Можно интегрировать в Telegram-бот или веб-интерфейс")
        
        return 0
        
    except Exception as e:
        print(f"❌ Критическая ошибка во время демонстрации: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 