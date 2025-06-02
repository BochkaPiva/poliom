#!/usr/bin/env python3
"""
Мониторинг состояния API ключа GigaChat
Отслеживает работоспособность ключа и отправляет уведомления
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import requests
import uuid

# Загружаем переменные окружения
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gigachat_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GigaChatMonitor:
    def __init__(self):
        self.api_key = os.getenv("GIGACHAT_API_KEY")
        self.status_file = "gigachat_status.json"
        self.check_interval = 300  # 5 минут
        self.scopes = ["GIGACHAT_API_PERS", "GIGACHAT_API_B2B", "GIGACHAT_API_CORP"]
        
    def load_status(self):
        """Загружает последний статус из файла"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки статуса: {e}")
        
        return {
            "last_check": None,
            "status": "unknown",
            "working_scope": None,
            "error_count": 0,
            "first_error": None,
            "last_success": None
        }
    
    def save_status(self, status):
        """Сохраняет статус в файл"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения статуса: {e}")
    
    def test_api_key(self):
        """Тестирует API ключ со всеми scope"""
        if not self.api_key:
            return False, None, "API ключ не найден"
        
        for scope in self.scopes:
            try:
                url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
                
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "RqUID": str(uuid.uuid4()),
                    "Authorization": f"Basic {self.api_key}"
                }
                
                data = {"scope": scope}
                
                response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
                
                if response.status_code == 200:
                    token_data = response.json()
                    if token_data.get("access_token"):
                        return True, scope, "OK"
                        
            except Exception as e:
                logger.error(f"Ошибка тестирования scope {scope}: {e}")
                continue
        
        return False, None, "Все scope недоступны"
    
    def check_health(self):
        """Проверяет здоровье API ключа"""
        logger.info("🔍 Проверка состояния GigaChat API...")
        
        status = self.load_status()
        current_time = datetime.now().isoformat()
        
        is_working, working_scope, error_msg = self.test_api_key()
        
        if is_working:
            logger.info(f"✅ API ключ работает! Scope: {working_scope}")
            
            # Сброс счетчика ошибок при успехе
            if status["status"] != "working":
                logger.info("🎉 API ключ восстановлен!")
            
            status.update({
                "last_check": current_time,
                "status": "working",
                "working_scope": working_scope,
                "error_count": 0,
                "first_error": None,
                "last_success": current_time
            })
            
        else:
            logger.error(f"❌ API ключ не работает: {error_msg}")
            
            # Увеличиваем счетчик ошибок
            status["error_count"] += 1
            
            if status["first_error"] is None:
                status["first_error"] = current_time
                logger.warning("🚨 Первая ошибка API ключа зафиксирована!")
            
            status.update({
                "last_check": current_time,
                "status": "error",
                "working_scope": None
            })
            
            # Критические уведомления
            if status["error_count"] == 1:
                self.send_alert("🚨 GigaChat API ключ перестал работать!")
            elif status["error_count"] % 12 == 0:  # Каждый час (12 * 5 минут)
                hours = status["error_count"] * 5 // 60
                self.send_alert(f"⚠️ GigaChat API не работает уже {hours} часов!")
        
        self.save_status(status)
        return is_working, status
    
    def send_alert(self, message):
        """Отправляет уведомление (можно расширить для Telegram/email)"""
        logger.critical(f"🚨 ALERT: {message}")
        
        # Здесь можно добавить отправку в Telegram или email
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "api_key_preview": self.api_key[:20] + "..." if self.api_key else "None"
        }
        
        try:
            with open("gigachat_alerts.log", "a", encoding='utf-8') as f:
                f.write(f"{json.dumps(alert_data, ensure_ascii=False)}\n")
        except Exception as e:
            logger.error(f"Ошибка записи алерта: {e}")
    
    def get_status_report(self):
        """Возвращает подробный отчет о состоянии"""
        status = self.load_status()
        
        report = {
            "api_key_status": status["status"],
            "last_check": status["last_check"],
            "working_scope": status["working_scope"],
            "error_count": status["error_count"],
            "uptime_info": self._calculate_uptime(status)
        }
        
        return report
    
    def _calculate_uptime(self, status):
        """Вычисляет время работы/простоя"""
        if not status["last_check"]:
            return "Нет данных"
        
        last_check = datetime.fromisoformat(status["last_check"])
        now = datetime.now()
        
        if status["status"] == "working":
            if status["last_success"]:
                last_success = datetime.fromisoformat(status["last_success"])
                uptime = now - last_success
                return f"Работает {uptime}"
            return "Работает"
        else:
            if status["first_error"]:
                first_error = datetime.fromisoformat(status["first_error"])
                downtime = now - first_error
                return f"Не работает {downtime}"
            return "Статус неизвестен"
    
    def run_continuous_monitoring(self):
        """Запускает непрерывный мониторинг"""
        logger.info("🚀 Запуск мониторинга GigaChat API...")
        logger.info(f"⏰ Интервал проверки: {self.check_interval} секунд")
        
        try:
            while True:
                self.check_health()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Мониторинг остановлен пользователем")
        except Exception as e:
            logger.error(f"💥 Критическая ошибка мониторинга: {e}")

def main():
    monitor = GigaChatMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            # Одноразовая проверка
            is_working, status = monitor.check_health()
            print(f"\n📊 СТАТУС API: {'✅ Работает' if is_working else '❌ Не работает'}")
            
        elif command == "status":
            # Показать текущий статус
            report = monitor.get_status_report()
            print(f"\n📊 ОТЧЕТ О СОСТОЯНИИ GIGACHAT API:")
            print(f"Статус: {report['api_key_status']}")
            print(f"Последняя проверка: {report['last_check']}")
            print(f"Рабочий scope: {report['working_scope']}")
            print(f"Количество ошибок: {report['error_count']}")
            print(f"Время работы/простоя: {report['uptime_info']}")
            
        elif command == "monitor":
            # Непрерывный мониторинг
            monitor.run_continuous_monitoring()
            
        else:
            print("Доступные команды:")
            print("  check   - одноразовая проверка")
            print("  status  - показать статус")
            print("  monitor - непрерывный мониторинг")
    else:
        # По умолчанию - одноразовая проверка
        monitor.check_health()

if __name__ == "__main__":
    main() 