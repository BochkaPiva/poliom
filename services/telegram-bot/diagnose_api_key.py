#!/usr/bin/env python3
"""
Диагностика проблем с API ключом GigaChat
"""

import sys
import os
import base64
import json
import requests
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

def diagnose_api_key():
    """Полная диагностика API ключа"""
    
    print("🔍 ДИАГНОСТИКА API КЛЮЧА GIGACHAT")
    print("=" * 60)
    
    # Получаем ключ
    gigachat_key = os.getenv("GIGACHAT_API_KEY")
    
    if not gigachat_key:
        print("❌ GIGACHAT_API_KEY не найден в .env")
        return False
    
    print(f"✅ API ключ найден: {gigachat_key[:20]}...")
    print(f"📏 Длина: {len(gigachat_key)} символов")
    
    # Декодируем ключ
    try:
        decoded = base64.b64decode(gigachat_key)
        decoded_str = decoded.decode('utf-8')
        print(f"✅ Base64 декодирование успешно")
        
        if ':' in decoded_str:
            client_id, client_secret = decoded_str.split(':', 1)
            print(f"🆔 Client ID: {client_id}")
            print(f"🔐 Client Secret: {client_secret[:10]}...")
        else:
            print("❌ Неверный формат декодированного ключа")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка декодирования: {e}")
        return False
    
    # Тестируем разные scope
    scopes = [
        "GIGACHAT_API_PERS",
        "GIGACHAT_API_B2B", 
        "GIGACHAT_API_CORP"
    ]
    
    print(f"\n🧪 ТЕСТИРОВАНИЕ РАЗНЫХ SCOPE:")
    print("-" * 40)
    
    for scope in scopes:
        print(f"\n🔍 Тестирую scope: {scope}")
        success = test_token_with_scope(gigachat_key, scope)
        if success:
            print(f"✅ Scope {scope} работает!")
            return True
        else:
            print(f"❌ Scope {scope} не работает")
    
    print(f"\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ ПРОБЛЕМЫ:")
    print("-" * 40)
    print("1. 🕐 API ключ истек (проверьте дату создания)")
    print("2. 🔄 Ключ был отозван в личном кабинете")
    print("3. 📋 Неправильный scope для вашего типа аккаунта")
    print("4. 🏢 Изменения в настройках приложения")
    print("5. 💳 Проблемы с оплатой/лимитами")
    print("6. 🔧 Технические проблемы на стороне Сбера")
    
    return False

def test_token_with_scope(api_key, scope):
    """Тестирование токена с определенным scope"""
    
    try:
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {api_key}"
        }
        
        data = {
            "scope": scope
        }
        
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if access_token:
                print(f"  ✅ Access token получен: {access_token[:20]}...")
                return True
        else:
            error_data = response.json() if response.content else {}
            print(f"  ❌ Ошибка {response.status_code}: {error_data}")
            
    except Exception as e:
        print(f"  ❌ Исключение: {e}")
    
    return False

def check_account_type():
    """Проверка типа аккаунта"""
    
    print(f"\n📋 ОПРЕДЕЛЕНИЕ ТИПА АККАУНТА:")
    print("-" * 40)
    print("Для правильного scope нужно знать тип вашего аккаунта:")
    print("• GIGACHAT_API_PERS - физические лица")
    print("• GIGACHAT_API_B2B - ИП и юр.лица (предоплата)")
    print("• GIGACHAT_API_CORP - ИП и юр.лица (постоплата)")
    print("\nПроверьте в личном кабинете:")
    print("https://developers.sber.ru/portal/products/gigachat")

def show_recovery_steps():
    """Шаги восстановления"""
    
    print(f"\n🔧 ШАГИ ВОССТАНОВЛЕНИЯ:")
    print("-" * 40)
    print("1. 🌐 Зайдите в личный кабинет GigaChat")
    print("2. 🔍 Найдите ваше приложение")
    print("3. 📊 Проверьте статус приложения")
    print("4. 💰 Проверьте баланс и лимиты")
    print("5. 🔑 Перевыпустите Authorization Data")
    print("6. 📝 Обновите GIGACHAT_API_KEY в .env")
    print("7. 🔄 Перезапустите приложение")
    
    print(f"\n⚠️ ВАЖНО:")
    print("- Ключи могут истекать при изменении настроек")
    print("- Проверьте правильность scope для вашего типа аккаунта")
    print("- Убедитесь, что приложение активно")

if __name__ == "__main__":
    success = diagnose_api_key()
    check_account_type()
    show_recovery_steps()
    
    if not success:
        print(f"\n💥 Требуется обновление API ключа!")
        sys.exit(1)
    else:
        print(f"\n🎉 API ключ работает корректно!") 