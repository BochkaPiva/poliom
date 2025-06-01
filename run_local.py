#!/usr/bin/env python3
"""
Экстренный запуск админ-панели БЕЗ Docker
Для случаев когда Docker не работает из-за нехватки места
"""

import subprocess
import sys
import os

def install_requirements():
    """Установка минимальных зависимостей"""
    requirements = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "python-multipart==0.0.6",
        "jinja2==3.1.2",
        "aiofiles==23.2.0"
    ]
    
    for req in requirements:
        print(f"Устанавливаю {req}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", req])

def create_minimal_app():
    """Создание минимального приложения"""
    app_code = '''
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="RAG Admin Panel - Emergency Mode")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>RAG Admin Panel - Emergency Mode</title></head>
        <body>
            <h1>🚨 RAG Admin Panel - Emergency Mode</h1>
            <p><strong>Статус:</strong> Работает локально (без Docker)</p>
            <p><strong>Порт:</strong> 8001</p>
            <p><strong>Режим:</strong> Минимальный функционал</p>
            <hr>
            <h2>Доступные функции:</h2>
            <ul>
                <li>✅ Веб-интерфейс работает</li>
                <li>❌ База данных (требует Docker)</li>
                <li>❌ ML-функции (требуют больше места)</li>
                <li>❌ Обработка документов (требует Docker)</li>
            </ul>
            <hr>
            <p><em>Для полного функционала освободите место на диске и перезапустите Docker</em></p>
        </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "emergency", "docker": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''
    
    with open("emergency_app.py", "w", encoding="utf-8") as f:
        f.write(app_code)

def main():
    print("🚨 ЭКСТРЕННЫЙ ЗАПУСК RAG ADMIN PANEL")
    print("=" * 50)
    
    try:
        print("1. Установка зависимостей...")
        install_requirements()
        
        print("2. Создание приложения...")
        create_minimal_app()
        
        print("3. Запуск сервера...")
        print("🌐 Админ-панель будет доступна на: http://localhost:8001")
        print("⚠️  Это минимальная версия без Docker")
        print("💾 Освободите место на диске для полного функционала")
        
        subprocess.run([sys.executable, "emergency_app.py"])
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("💡 Попробуйте освободить место на диске")

if __name__ == "__main__":
    main() 