
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
