@echo off
echo Удаляю Docker файл размером 97GB...
del /f /q "C:\Users\%USERNAME%\AppData\Local\Docker\wsl\disk\docker_data.vhdx"
if exist "C:\Users\%USERNAME%\AppData\Local\Docker\wsl\disk\docker_data.vhdx" (
    echo Файл все еще заблокирован, попробуйте:
    echo 1. Перезагрузить компьютер
    echo 2. Запустить этот файл от имени администратора
    echo 3. Удалить Docker Desktop полностью
) else (
    echo ✅ Файл успешно удален! Освобождено ~97GB места!
)
echo.
echo Проверяю свободное место на диске...
fsutil volume diskfree C:
pause 