#!/usr/bin/env python3
"""
Тест токена GigaChat
"""

import sys
import os
from pathlib import Path

# Добавляем путь к services
services_path = Path(__file__).parent.parent
sys.path.append(str(services_path))

# Загружаем переменные окружения
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

from shared.utils.llm_client import GigaChatClient

def test_gigachat_token():
    """Тестирование токена GigaChat"""
    
    print("🧪 ТЕСТИРОВАНИЕ ТОКЕНА GIGACHAT")
    print("=" * 50)
    
    # Получаем токен из переменных окружения
    gigachat_key = os.getenv("GIGACHAT_API_KEY")
    
    if not gigachat_key:
        print("❌ GIGACHAT_API_KEY не найден в переменных окружения")
        return False
    
    print(f"✅ Токен найден: {gigachat_key[:20]}...")
    
    # Создаем клиент
    client = GigaChatClient(gigachat_key)
    
    # Тестируем получение access token
    print("\n🔑 Тестирование получения access token...")
    access_token = client._get_access_token()
    
    if access_token:
        print(f"✅ Access token получен: {access_token[:20]}...")
        
        # Тестируем простой запрос
        print("\n💬 Тестирование простого запроса...")
        response = client.generate_response("Привет! Как дела?", max_tokens=50)
        
        if response.success:
            print(f"✅ Ответ получен: {response.text[:100]}...")
            print(f"📊 Токенов использовано: {response.tokens_used}")
            return True
        else:
            print(f"❌ Ошибка генерации ответа: {response.error}")
            return False
    else:
        print("❌ Не удалось получить access token")
        return False

if __name__ == "__main__":
    success = test_gigachat_token()
    if success:
        print("\n🎉 Все тесты пройдены успешно!")
    else:
        print("\n💥 Тесты провалены!")
        sys.exit(1) 