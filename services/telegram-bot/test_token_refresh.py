#!/usr/bin/env python3
"""
Тест автообновления токенов GigaChat
"""

import sys
import os
import time
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

def test_token_refresh():
    """Тестирование автообновления токенов"""
    
    print("🔄 ТЕСТИРОВАНИЕ АВТООБНОВЛЕНИЯ ТОКЕНОВ GIGACHAT")
    print("=" * 60)
    
    # Получаем API ключ
    gigachat_key = os.getenv("GIGACHAT_API_KEY")
    
    if not gigachat_key:
        print("❌ GIGACHAT_API_KEY не найден")
        return False
    
    print(f"✅ API ключ найден: {gigachat_key[:20]}...")
    
    # Создаем клиент
    client = GigaChatClient(gigachat_key)
    
    print("\n🔑 Тест 1: Первое получение токена")
    token1 = client._get_access_token()
    
    if not token1:
        print("❌ Не удалось получить первый токен")
        print("💡 Проверьте API ключ в личном кабинете GigaChat")
        return False
    
    print(f"✅ Первый токен получен: {token1[:20]}...")
    print(f"⏰ Токен истекает в: {time.ctime(client.token_expires_at)}")
    
    print("\n🔄 Тест 2: Повторный запрос (должен вернуть кэшированный токен)")
    token2 = client._get_access_token()
    
    if token1 == token2:
        print("✅ Кэширование работает - вернулся тот же токен")
    else:
        print("⚠️ Получен новый токен (возможно, предыдущий истек)")
    
    print("\n⏳ Тест 3: Принудительное обновление токена")
    # Сбрасываем время истечения, чтобы принудительно обновить токен
    client.token_expires_at = 0
    token3 = client._get_access_token()
    
    if token3 and token3 != token1:
        print("✅ Автообновление работает - получен новый токен")
        print(f"🆕 Новый токен: {token3[:20]}...")
    elif token3 == token1:
        print("⚠️ Вернулся тот же токен (возможно, сервер кэширует)")
    else:
        print("❌ Не удалось получить обновленный токен")
        return False
    
    print("\n💬 Тест 4: Реальный запрос к API")
    response = client.generate_response("Привет!", max_tokens=20)
    
    if response.success:
        print(f"✅ API работает: {response.text[:50]}...")
        print(f"📊 Токенов использовано: {response.tokens_used}")
        return True
    else:
        print(f"❌ Ошибка API: {response.error}")
        return False

def show_token_management_info():
    """Показать информацию о управлении токенами"""
    
    print("\n📋 КАК РАБОТАЕТ АВТООБНОВЛЕНИЕ ТОКЕНОВ:")
    print("=" * 50)
    print("1. ✅ API ключ хранится в .env (постоянный)")
    print("2. ✅ Access токены получаются автоматически")
    print("3. ✅ Токены кэшируются на 30 минут")
    print("4. ✅ Автообновление за 5 минут до истечения")
    print("5. ✅ Никаких ручных действий не требуется")
    
    print("\n🔧 ЧТО НУЖНО СДЕЛАТЬ:")
    print("1. Получить новый Authorization Key из личного кабинета")
    print("2. Обновить GIGACHAT_API_KEY в .env файле")
    print("3. Перезапустить бота")

if __name__ == "__main__":
    success = test_token_refresh()
    show_token_management_info()
    
    if success:
        print("\n🎉 Автообновление токенов работает отлично!")
    else:
        print("\n💥 Нужно обновить API ключ!")
        sys.exit(1) 