#!/usr/bin/env python3
"""
Тест подключения к GigaChat API с правильной OAuth аутентификацией
"""

import sys
import os
from pathlib import Path

# Добавляем путь к services для импорта модулей
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения из корневого .env файла
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from shared.utils.llm_client import SimpleLLMClient

def test_gigachat_connection():
    """Тестирует подключение к GigaChat с OAuth"""
    print("🤖 ТЕСТ ПОДКЛЮЧЕНИЯ К GIGACHAT (OAuth)")
    print("=" * 60)
    
    # Проверяем наличие Authorization key
    auth_key = os.getenv('GIGACHAT_API_KEY')
    if not auth_key:
        print("❌ GIGACHAT_API_KEY не найден в переменных окружения")
        print("💡 Убедитесь, что в .env файле указан Authorization key от GigaChat")
        return False
    
    print(f"✅ Authorization key найден: {auth_key[:20]}...")
    print("📝 Это должен быть Authorization key, а не Access token")
    
    try:
        # Инициализируем клиент
        print("\n🔧 Инициализация клиента GigaChat...")
        client = SimpleLLMClient(auth_key)
        print("✅ Клиент GigaChat инициализирован")
        
        # Проверяем получение Access token
        print("\n🔑 Проверка получения Access token...")
        access_token = client.gigachat._get_access_token()
        
        if access_token:
            print("✅ Access token успешно получен")
            print(f"🔑 Token: {access_token[:20]}...")
        else:
            print("❌ Не удалось получить Access token")
            print("💡 Проверьте правильность Authorization key")
            return False
        
        # Проверяем здоровье
        print("\n🔍 Проверка работоспособности API...")
        is_healthy = client.health_check()
        
        if is_healthy:
            print("✅ GigaChat API доступен и работает")
        else:
            print("⚠️ GigaChat API недоступен или есть проблемы")
            return False
        
        # Тестовый запрос
        print("\n💬 Тестовый запрос к GigaChat...")
        test_context = """
        Документ содержит следующую информацию о доплатах:
        - Доплата за ночную работу составляет 40 процентов от часовой тарифной ставки
        - Работа в праздничные дни оплачивается в двойном размере
        - За вредные условия труда предусмотрена надбавка 12%
        """
        test_question = "Какой размер доплаты за ночную работу?"
        
        response = client.generate_answer(
            context=test_context,
            question=test_question,
            max_tokens=200
        )
        
        if response.success:
            print("✅ Успешный ответ от GigaChat:")
            print("┌" + "─" * 58 + "┐")
            print(f"│ 📝 Ответ: {response.text[:50]:<50} │")
            if len(response.text) > 50:
                remaining_text = response.text[50:]
                while remaining_text:
                    line = remaining_text[:50]
                    remaining_text = remaining_text[50:]
                    print(f"│          {line:<50} │")
            print("└" + "─" * 58 + "┘")
            print(f"🔢 Токенов использовано: {response.tokens_used}")
            print(f"🤖 Модель: {response.model}")
            
            # Проверяем, что ответ содержит ожидаемую информацию
            if "40" in response.text and ("процент" in response.text.lower() or "%" in response.text):
                print("🎯 Ответ содержит ожидаемую информацию о 40%")
                return True
            else:
                print("⚠️ Ответ не содержит ожидаемой информации")
                return True  # Все равно считаем успешным, если API работает
        else:
            print(f"❌ Ошибка при запросе: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        print("🔍 Детали ошибки:")
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("🚀 Запуск теста подключения к GigaChat...")
    print("📋 Проверяем OAuth аутентификацию и работу API\n")
    
    success = test_gigachat_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН: GigaChat готов к использованию!")
        print("✅ OAuth аутентификация работает корректно")
        print("✅ API отвечает на запросы")
        print("🚀 Можно запускать полную демонстрацию поиска")
        return 0
    else:
        print("💥 ТЕСТ НЕ ПРОЙДЕН: Проблемы с подключением к GigaChat")
        print("🔧 Возможные причины:")
        print("   • Неправильный Authorization key")
        print("   • Проблемы с сетевым подключением")
        print("   • Проблемы с SSL сертификатами")
        print("   • API GigaChat временно недоступен")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 