#!/usr/bin/env python3
"""
Проверка и анализ токена GigaChat
"""

import sys
import os
import base64
import json
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

def analyze_gigachat_token():
    """Анализ токена GigaChat"""
    
    print("🔍 АНАЛИЗ ТОКЕНА GIGACHAT")
    print("=" * 50)
    
    # Получаем токен из переменных окружения
    gigachat_key = os.getenv("GIGACHAT_API_KEY")
    
    if not gigachat_key:
        print("❌ GIGACHAT_API_KEY не найден в переменных окружения")
        return False
    
    print(f"✅ Токен найден")
    print(f"📏 Длина токена: {len(gigachat_key)} символов")
    print(f"🔤 Первые 20 символов: {gigachat_key[:20]}...")
    print(f"🔤 Последние 20 символов: ...{gigachat_key[-20:]}")
    
    # Проверяем, является ли токен валидным Base64
    try:
        decoded = base64.b64decode(gigachat_key)
        decoded_str = decoded.decode('utf-8')
        print(f"✅ Токен является валидным Base64")
        print(f"📝 Декодированное содержимое: {decoded_str}")
        
        # Проверяем формат (должно быть client_id:client_secret)
        if ':' in decoded_str:
            client_id, client_secret = decoded_str.split(':', 1)
            print(f"🆔 Client ID: {client_id}")
            print(f"🔐 Client Secret: {client_secret[:10]}...")
        else:
            print("⚠️ Неожиданный формат декодированного токена")
            
    except Exception as e:
        print(f"❌ Ошибка декодирования Base64: {e}")
        return False
    
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("1. Убедитесь, что токен получен из официального интерфейса GigaChat")
    print("2. Проверьте, не истек ли срок действия токена")
    print("3. Убедитесь, что у вас есть доступ к GigaChat API")
    print("4. Попробуйте сгенерировать новый токен")
    
    return True

def show_token_generation_guide():
    """Показать инструкцию по получению токена"""
    
    print("\n📋 ИНСТРУКЦИЯ ПО ПОЛУЧЕНИЮ ТОКЕНА GIGACHAT:")
    print("=" * 60)
    print("1. Перейдите на https://developers.sber.ru/portal/products/gigachat")
    print("2. Войдите в личный кабинет")
    print("3. Создайте новое приложение или выберите существующее")
    print("4. Получите Authorization Data (Base64)")
    print("5. Скопируйте полученный токен в .env файл как GIGACHAT_API_KEY")
    print("\n⚠️ ВАЖНО: Токен должен быть в формате Base64!")

if __name__ == "__main__":
    success = analyze_gigachat_token()
    show_token_generation_guide()
    
    if not success:
        sys.exit(1) 