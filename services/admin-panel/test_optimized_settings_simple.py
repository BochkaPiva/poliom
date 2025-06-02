#!/usr/bin/env python3
"""
Упрощенное тестирование оптимизированных настроек эмбеддингов и чанков
"""

import sys
import os
from pathlib import Path

# Добавляем путь к shared модулям
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "shared"))

from utils.embeddings import SimpleEmbeddings
from utils.document_processor import DocumentProcessor
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_embedding_quality():
    """Тест качества эмбеддингов"""
    print("🔍 Тестирование качества эмбеддингов...")
    
    embeddings = SimpleEmbeddings()
    
    # Тестовые тексты
    test_texts = [
        "Заработная плата выплачивается два раза в месяц",
        "Зарплата перечисляется 12 и 27 числа каждого месяца",
        "Отпускные выплачиваются за три дня до отпуска",
        "Рабочий день начинается в 9:00 утра",
        "Обеденный перерыв длится один час"
    ]
    
    # Создаем эмбеддинги
    embeddings_list = []
    for text in test_texts:
        emb = embeddings.create_embedding(text)
        embeddings_list.append(emb)
        print(f"✅ Эмбеддинг создан для: '{text[:50]}...' (размерность: {len(emb)})")
    
    # Тестируем схожесть
    print("\n📊 Тестирование схожести:")
    similarity_salary = embeddings.calculate_similarity(embeddings_list[0], embeddings_list[1])
    similarity_different = embeddings.calculate_similarity(embeddings_list[0], embeddings_list[3])
    
    print(f"Схожесть зарплатных текстов: {similarity_salary:.3f}")
    print(f"Схожесть разных тем: {similarity_different:.3f}")
    
    return embeddings.get_model_info()

def test_chunking_quality():
    """Тест качества чанкирования"""
    print("\n📝 Тестирование качества чанкирования...")
    
    processor = DocumentProcessor()
    
    # Тестовый текст (имитация корпоративного документа)
    test_text = """
    ПОЛОЖЕНИЕ О ЗАРАБОТНОЙ ПЛАТЕ
    
    1. ОБЩИЕ ПОЛОЖЕНИЯ
    Настоящее положение определяет порядок начисления и выплаты заработной платы сотрудникам компании.
    
    2. СРОКИ ВЫПЛАТЫ
    Заработная плата выплачивается два раза в месяц:
    - Аванс выплачивается 12 числа каждого месяца в размере 40% от оклада
    - Основная часть заработной платы выплачивается 27 числа каждого месяца
    
    В случае если день выплаты приходится на выходной или праздничный день, выплата производится в предшествующий рабочий день.
    
    3. ПОРЯДОК НАЧИСЛЕНИЯ
    Заработная плата начисляется исходя из отработанного времени и установленного оклада.
    При расчете учитываются:
    - Оклад согласно штатному расписанию
    - Премии и доплаты
    - Районные коэффициенты
    - Удержания согласно законодательству
    
    4. ОТПУСКНЫЕ ВЫПЛАТЫ
    Отпускные выплачиваются не позднее чем за 3 дня до начала отпуска.
    Расчет производится исходя из среднего заработка за 12 месяцев.
    
    5. БОЛЬНИЧНЫЕ ВЫПЛАТЫ
    Пособие по временной нетрудоспособности выплачивается в соответствии с действующим законодательством.
    
    6. ДОПОЛНИТЕЛЬНЫЕ ВЫПЛАТЫ
    Компания может производить дополнительные выплаты в виде премий, бонусов и других поощрений.
    Размер и условия таких выплат определяются отдельными приказами руководства.
    
    7. ОТВЕТСТВЕННОСТЬ
    За нарушение сроков выплаты заработной платы компания несет ответственность в соответствии с трудовым законодательством.
    """ * 2  # Увеличиваем текст для тестирования
    
    # Тестируем старые настройки (1000 символов)
    old_chunks = processor.split_into_chunks(test_text, chunk_size=1000, overlap=200)
    
    # Тестируем новые настройки (1500 символов)
    new_chunks = processor.split_into_chunks(test_text, chunk_size=1500, overlap=200)
    
    print(f"📊 Результаты чанкирования:")
    print(f"Старые настройки (1000): {len(old_chunks)} чанков")
    print(f"Новые настройки (1500): {len(new_chunks)} чанков")
    
    # Анализируем размеры чанков
    old_sizes = [len(chunk) for chunk in old_chunks]
    new_sizes = [len(chunk) for chunk in new_chunks]
    
    print(f"\n📏 Размеры чанков (старые):")
    print(f"   Мин: {min(old_sizes)}, Макс: {max(old_sizes)}, Средний: {sum(old_sizes)/len(old_sizes):.1f}")
    
    print(f"📏 Размеры чанков (новые):")
    print(f"   Мин: {min(new_sizes)}, Макс: {max(new_sizes)}, Средний: {sum(new_sizes)/len(new_sizes):.1f}")
    
    # Проверяем качество разбиения
    print(f"\n🔍 Анализ качества:")
    
    # Проверяем, сохраняется ли контекст о зарплате
    salary_context_old = sum(1 for chunk in old_chunks if 'заработная плата' in chunk.lower() and '12' in chunk and '27' in chunk)
    salary_context_new = sum(1 for chunk in new_chunks if 'заработная плата' in chunk.lower() and '12' in chunk and '27' in chunk)
    
    print(f"Чанков с полным контекстом о зарплате (старые): {salary_context_old}")
    print(f"Чанков с полным контекстом о зарплате (новые): {salary_context_new}")
    
    # Проверяем фрагментацию информации
    complete_info_old = sum(1 for chunk in old_chunks if 'аванс' in chunk.lower() and 'основная часть' in chunk.lower())
    complete_info_new = sum(1 for chunk in new_chunks if 'аванс' in chunk.lower() and 'основная часть' in chunk.lower())
    
    print(f"Чанков с полной информацией о выплатах (старые): {complete_info_old}")
    print(f"Чанков с полной информацией о выплатах (новые): {complete_info_new}")
    
    return {
        'old_chunks_count': len(old_chunks),
        'new_chunks_count': len(new_chunks),
        'old_avg_size': sum(old_sizes)/len(old_sizes),
        'new_avg_size': sum(new_sizes)/len(new_sizes),
        'context_preservation_old': salary_context_old,
        'context_preservation_new': salary_context_new,
        'complete_info_old': complete_info_old,
        'complete_info_new': complete_info_new
    }

def analyze_token_efficiency():
    """Анализ эффективности использования токенов"""
    print("\n🎯 Анализ эффективности токенов...")
    
    # Примерные расчеты для русского текста
    # 1 токен ≈ 0.75 слова ≈ 4-5 символов
    
    old_chunk_size = 1000  # символов
    new_chunk_size = 1500  # символов
    
    old_tokens_per_chunk = old_chunk_size / 4.5  # примерно
    new_tokens_per_chunk = new_chunk_size / 4.5
    
    old_chunks_for_context = 50  # старый лимит
    new_chunks_for_context = 25  # новый лимит
    
    old_total_tokens = old_tokens_per_chunk * old_chunks_for_context
    new_total_tokens = new_tokens_per_chunk * new_chunks_for_context
    
    print(f"📊 Сравнение использования токенов:")
    print(f"Старые настройки:")
    print(f"   Токенов на чанк: ~{old_tokens_per_chunk:.0f}")
    print(f"   Чанков в контексте: {old_chunks_for_context}")
    print(f"   Общий контекст: ~{old_total_tokens:.0f} токенов")
    
    print(f"Новые настройки:")
    print(f"   Токенов на чанк: ~{new_tokens_per_chunk:.0f}")
    print(f"   Чанков в контексте: {new_chunks_for_context}")
    print(f"   Общий контекст: ~{new_total_tokens:.0f} токенов")
    
    efficiency_improvement = (old_total_tokens - new_total_tokens) / old_total_tokens * 100
    
    print(f"\n✅ Улучшение эффективности: {efficiency_improvement:.1f}%")
    print(f"   Экономия токенов: ~{old_total_tokens - new_total_tokens:.0f} токенов")
    print(f"   Больше места для ответа: +{2500 - 1000} токенов")
    
    return {
        'old_total_tokens': old_total_tokens,
        'new_total_tokens': new_total_tokens,
        'efficiency_improvement': efficiency_improvement
    }

def main():
    """Основная функция тестирования"""
    print("🔧 ТЕСТИРОВАНИЕ ОПТИМИЗИРОВАННЫХ НАСТРОЕК")
    print("=" * 50)
    
    # Тест эмбеддингов
    embedding_info = test_embedding_quality()
    print(f"\n📋 Информация о модели эмбеддингов:")
    for key, value in embedding_info.items():
        print(f"   {key}: {value}")
    
    # Тест чанкирования
    chunking_results = test_chunking_quality()
    
    # Анализ токенов
    token_analysis = analyze_token_efficiency()
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ПО ОПТИМИЗАЦИИ")
    print("=" * 50)
    
    print(f"\n✅ ЭМБЕДДИНГИ:")
    print(f"   Модель: {embedding_info['model_name']}")
    print(f"   Размерность: {embedding_info['embedding_dimension']}")
    print(f"   Язык: {embedding_info['language']}")
    print(f"   Стоимость: {embedding_info['cost']}")
    
    print(f"\n✅ ЧАНКИРОВАНИЕ:")
    print(f"   Уменьшение количества чанков: {chunking_results['old_chunks_count']} → {chunking_results['new_chunks_count']}")
    print(f"   Увеличение среднего размера: {chunking_results['old_avg_size']:.0f} → {chunking_results['new_avg_size']:.0f} символов")
    print(f"   Улучшение сохранения контекста: {chunking_results['context_preservation_old']} → {chunking_results['context_preservation_new']}")
    print(f"   Полная информация в чанках: {chunking_results['complete_info_old']} → {chunking_results['complete_info_new']}")
    
    print(f"\n✅ ЭФФЕКТИВНОСТЬ ТОКЕНОВ:")
    print(f"   Экономия контекстных токенов: {token_analysis['efficiency_improvement']:.1f}%")
    print(f"   Увеличение лимита ответа: 1000 → 2500 токенов (+150%)")
    
    print(f"\n🎯 ПРИМЕНЁННЫЕ ОПТИМИЗАЦИИ:")
    print(f"   ✅ Размер чанков: 1000 → 1500 символов (+50%)")
    print(f"   ✅ Максимальные токены GigaChat: 1000 → 2500 (+150%)")
    print(f"   ✅ Лимит поиска чанков: 50 → 25 (-50%)")
    print(f"   ✅ Порог схожести: 0.3 → 0.4 (+33%)")
    
    print(f"\n🚀 ОЖИДАЕМЫЕ УЛУЧШЕНИЯ:")
    print(f"   📈 Лучшее качество ответов за счет большего контекста в чанках")
    print(f"   ⚡ Быстрее поиск за счет меньшего количества обрабатываемых чанков")
    print(f"   🎯 Точнее результаты за счет повышенного порога схожести")
    print(f"   📝 Более развернутые ответы за счет увеличенного лимита токенов")
    print(f"   💰 Экономия токенов контекста для более эффективного использования")
    
    print(f"\n🔍 РЕКОМЕНДАЦИИ ДЛЯ ДАЛЬНЕЙШЕЙ ОПТИМИЗАЦИИ:")
    print(f"   📊 Мониторить качество ответов в продакшене")
    print(f"   🔄 При необходимости можно увеличить размер чанков до 2000 символов")
    print(f"   ⚖️ Балансировать между качеством и скоростью поиска")
    print(f"   📈 Рассмотреть использование более мощной модели эмбеддингов при росте нагрузки")

if __name__ == "__main__":
    main() 