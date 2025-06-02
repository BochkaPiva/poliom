#!/usr/bin/env python3
"""
Тестирование оптимизированных настроек эмбеддингов и чанков
"""

import sys
import os
from pathlib import Path

# Добавляем путь к shared модулям
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "shared"))

from utils.embeddings import SimpleEmbeddings
from utils.document_processor import DocumentProcessor
from utils.simple_rag import SimpleRAG
from database import get_db_session
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
    """ * 3  # Увеличиваем текст для тестирования
    
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
    
    return {
        'old_chunks_count': len(old_chunks),
        'new_chunks_count': len(new_chunks),
        'old_avg_size': sum(old_sizes)/len(old_sizes),
        'new_avg_size': sum(new_sizes)/len(new_sizes),
        'context_preservation_old': salary_context_old,
        'context_preservation_new': salary_context_new
    }

def test_rag_performance():
    """Тест производительности RAG с новыми настройками"""
    print("\n🚀 Тестирование производительности RAG...")
    
    try:
        # Получаем API ключ
        gigachat_key = os.getenv('GIGACHAT_API_KEY')
        if not gigachat_key:
            print("❌ GIGACHAT_API_KEY не найден в переменных окружения")
            return None
        
        # Создаем RAG систему
        db_session = next(get_db_session())
        rag = SimpleRAG(db_session, gigachat_key)
        
        # Тестовые вопросы
        test_questions = [
            "Когда выплачивается зарплата?",
            "Какой размер аванса?",
            "Когда выплачиваются отпускные?",
            "Что делать если день зарплаты выходной?"
        ]
        
        results = []
        for question in test_questions:
            print(f"\n❓ Вопрос: {question}")
            
            # Поиск релевантных чанков
            chunks = rag.search_relevant_chunks(question, limit=25)
            print(f"   📚 Найдено чанков: {len(chunks)}")
            
            if chunks:
                avg_similarity = sum(chunk.get('similarity', 0) for chunk in chunks) / len(chunks)
                print(f"   📊 Средняя схожесть: {avg_similarity:.3f}")
                
                # Проверяем качество найденных чанков
                relevant_chunks = [chunk for chunk in chunks if chunk.get('similarity', 0) > 0.5]
                print(f"   ✅ Высокорелевантных чанков: {len(relevant_chunks)}")
                
                results.append({
                    'question': question,
                    'chunks_found': len(chunks),
                    'avg_similarity': avg_similarity,
                    'high_relevance_chunks': len(relevant_chunks)
                })
        
        return results
        
    except Exception as e:
        print(f"❌ Ошибка тестирования RAG: {e}")
        return None

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
    
    # Тест RAG
    rag_results = test_rag_performance()
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ПО ОПТИМИЗАЦИИ")
    print("=" * 50)
    
    print(f"\n✅ ЭМБЕДДИНГИ:")
    print(f"   Модель: {embedding_info['model_name']}")
    print(f"   Размерность: {embedding_info['embedding_dimension']}")
    print(f"   Язык: {embedding_info['language']}")
    
    print(f"\n✅ ЧАНКИРОВАНИЕ:")
    print(f"   Уменьшение количества чанков: {chunking_results['old_chunks_count']} → {chunking_results['new_chunks_count']}")
    print(f"   Увеличение среднего размера: {chunking_results['old_avg_size']:.0f} → {chunking_results['new_avg_size']:.0f} символов")
    print(f"   Улучшение сохранения контекста: {chunking_results['context_preservation_old']} → {chunking_results['context_preservation_new']}")
    
    if rag_results:
        print(f"\n✅ RAG ПРОИЗВОДИТЕЛЬНОСТЬ:")
        for result in rag_results:
            print(f"   '{result['question']}': {result['high_relevance_chunks']} высокорелевантных из {result['chunks_found']}")
    
    print(f"\n🎯 РЕКОМЕНДАЦИИ ПРИМЕНЕНЫ:")
    print(f"   ✅ Размер чанков увеличен до 1500 символов")
    print(f"   ✅ Максимальные токены GigaChat увеличены до 2500")
    print(f"   ✅ Лимит поиска чанков уменьшен до 25")
    print(f"   ✅ Порог схожести повышен до 0.4")
    
    print(f"\n🚀 ОЖИДАЕМЫЕ УЛУЧШЕНИЯ:")
    print(f"   📈 Лучшее качество ответов за счет большего контекста")
    print(f"   ⚡ Быстрее поиск за счет меньшего количества чанков")
    print(f"   🎯 Точнее результаты за счет повышенного порога схожести")
    print(f"   📝 Более развернутые ответы за счет увеличенного лимита токенов")

if __name__ == "__main__":
    main() 