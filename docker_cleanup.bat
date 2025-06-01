@echo off
echo 🧹 ЕЖЕНЕДЕЛЬНАЯ ОЧИСТКА DOCKER
echo ================================

echo 📊 Проверяю текущий размер Docker...
docker system df 2>nul
if errorlevel 1 (
    echo ❌ Docker не запущен или не установлен
    pause
    exit /b 1
)

echo.
echo 🗑️ Начинаю очистку...

echo 1. Удаляю остановленные контейнеры...
docker container prune -f

echo 2. Удаляю неиспользуемые образы...
docker image prune -f

echo 3. Удаляю неиспользуемые volumes...
docker volume prune -f

echo 4. Удаляю build cache...
docker builder prune -f

echo.
echo 📊 Размер после очистки:
docker system df

echo.
echo ✅ Очистка завершена!
echo 💡 Рекомендуется запускать этот скрипт раз в неделю
echo.
pause 