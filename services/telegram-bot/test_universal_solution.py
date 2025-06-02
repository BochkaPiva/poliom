#!/usr/bin/env python3
"""
Тестирование универсального решения для обхода блокировки GigaChat
"""

import re

def extract_key_information(context: str, question: str) -> str:
    """Извлекает ключевую информацию из контекста для формирования ответа"""
    
    # Разбиваем контекст на источники
    sources = re.split(r'\[Источник \d+:', context)
    
    # Ключевые слова из вопроса для поиска релевантной информации
    question_words = set(re.findall(r'\b\w+\b', question.lower()))
    
    # Удаляем стоп-слова
    stop_words = {'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об', 'и', 'или', 'а', 'но', 'что', 'как', 'когда', 'где', 'почему', 'какой', 'какая', 'какие', 'который', 'которая', 'которые'}
    question_words = question_words - stop_words
    
    relevant_info = []
    
    for source in sources[1:]:  # Пропускаем первый пустой элемент
        if not source.strip():
            continue
            
        # Извлекаем название документа
        doc_match = re.search(r'^([^\]]+)\]', source)
        doc_name = doc_match.group(1) if doc_match else "Документ"
        
        # Получаем текст источника
        source_text = source.split(']', 1)[-1].strip()
        
        # Ищем релевантные предложения
        sentences = re.split(r'[.!?]+', source_text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Пропускаем слишком короткие предложения
                continue
                
            sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
            
            # Проверяем пересечение с ключевыми словами вопроса
            if question_words & sentence_words:
                relevant_info.append({
                    'text': sentence,
                    'source': doc_name,
                    'relevance': len(question_words & sentence_words)
                })
    
    # Сортируем по релевантности
    relevant_info.sort(key=lambda x: x['relevance'], reverse=True)
    
    if not relevant_info:
        return None
        
    # Формируем ответ из наиболее релевантной информации
    response_parts = ["📋 **Информация из корпоративных документов:**\n"]
    
    used_sources = set()
    added_info = 0
    
    for info in relevant_info[:5]:  # Берем топ-5 наиболее релевантных
        if added_info >= 3:  # Ограничиваем количество пунктов
            break
            
        text = info['text']
        source = info['source']
        
        # Избегаем дублирования информации
        if text not in [item['text'] for item in relevant_info[:added_info]]:
            response_parts.append(f"• {text}")
            used_sources.add(source)
            added_info += 1
    
    if used_sources:
        response_parts.append(f"\n*Источники: {', '.join(used_sources)}*")
    
    return "\n".join(response_parts)

def extract_specific_data_patterns(context: str, question: str) -> str:
    """Извлекает специфические паттерны данных (даты, числа, проценты и т.д.)"""
    
    patterns = {
        'dates': r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b|\b\d{1,2}[-е\s]*(?:число|числа)\b',
        'percentages': r'\b\d+(?:[.,]\d+)?%\b|\b\d+(?:[.,]\d+)?\s*процент[а-я]*\b',
        'money': r'\b\d+(?:\s?\d{3})*(?:[.,]\d+)?\s*(?:руб|рубл[ей]*|тыс|млн)\b',
        'time': r'\b\d{1,2}:\d{2}\b|\b\d{1,2}\s*час[а-я]*\b',
        'periods': r'\b(?:ежемесячно|еженедельно|ежегодно|раз в месяц|два раза в месяц)\b'
    }
    
    found_data = []
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, context, re.IGNORECASE)
        if matches:
            found_data.extend(matches)
    
    if found_data:
        # Убираем дубликаты
        unique_data = list(set(found_data))
        return f"**Найденные данные:** {', '.join(unique_data)}"
    
    return None

def test_universal_extraction():
    """Тестирует универсальный механизм извлечения информации"""
    
    # Тестовый контекст из корпоративных документов
    test_context = """[Источник 1: Правила внутреннего трудового распорядка]
Установленными днями для расчетов с работниками являются 12-е и 27-е числа месяца. Заработная плата выплачивается два раза в месяц. Первая выплата составляет 50% от оклада и производится 15 числа. Вторая выплата производится 27 числа и включает оставшуюся часть заработной платы.

[Источник 2: Положение об оплате труда]
Рабочее время составляет 40 часов в неделю. Сверхурочная работа оплачивается в двойном размере. Отпуск предоставляется продолжительностью 28 календарных дней. Премии выплачиваются ежемесячно в размере до 30% от оклада.

[Источник 3: Социальная политика]
Компания предоставляет медицинское страхование всем сотрудникам. Компенсация питания составляет 5000 рублей в месяц. Работникам с детьми предоставляется дополнительный отпуск 3 дня в году."""
    
    # Тестовые вопросы
    test_questions = [
        "Когда выплачивается заработная плата?",
        "Сколько часов составляет рабочая неделя?",
        "Какие социальные льготы предоставляет компания?",
        "Какой размер премии?",
        "Сколько дней отпуска положено?",
        "Есть ли компенсация питания?",
        "Как оплачивается сверхурочная работа?"
    ]
    
    print("="*80)
    print("ТЕСТИРОВАНИЕ УНИВЕРСАЛЬНОГО МЕХАНИЗМА ИЗВЛЕЧЕНИЯ ИНФОРМАЦИИ")
    print("="*80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- ВОПРОС {i}: {question} ---")
        
        # Пытаемся извлечь ключевую информацию
        extracted_info = extract_key_information(test_context, question)
        
        if extracted_info:
            print("✅ ИЗВЛЕЧЕНА КЛЮЧЕВАЯ ИНФОРМАЦИЯ:")
            print(extracted_info)
        else:
            # Пытаемся найти специфические данные
            specific_data = extract_specific_data_patterns(test_context, question)
            if specific_data:
                print("✅ НАЙДЕНЫ СПЕЦИФИЧЕСКИЕ ДАННЫЕ:")
                print(f"📊 **Информация из документов:**\n\n{specific_data}\n\n*Найдено в корпоративной документации*")
            else:
                print("❌ ИНФОРМАЦИЯ НЕ НАЙДЕНА")
        
        print("-" * 60)
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ СПЕЦИФИЧЕСКИХ ПАТТЕРНОВ")
    print("="*80)
    
    # Тестируем извлечение специфических данных
    patterns_test_context = """
    Выплаты производятся 12-го и 27-го числа каждого месяца.
    Премия составляет 25% от оклада.
    Рабочий день с 9:00 до 18:00.
    Компенсация питания 5000 рублей.
    Отпуск 28 дней в году.
    Сверхурочные оплачиваются в размере 150% от ставки.
    """
    
    specific_data = extract_specific_data_patterns(patterns_test_context, "данные")
    if specific_data:
        print("✅ НАЙДЕННЫЕ ПАТТЕРНЫ:")
        print(specific_data)
    else:
        print("❌ ПАТТЕРНЫ НЕ НАЙДЕНЫ")
    
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*80)

if __name__ == "__main__":
    test_universal_extraction() 