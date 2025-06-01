# Multi-stage build для минимизации размера
FROM python:3.11-slim as builder

# Создаем пользователя botuser в builder stage
RUN useradd --create-home --shell /bin/bash botuser

# Устанавливаем зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY services/telegram-bot/requirements.txt /tmp/requirements.txt
COPY services/shared/requirements.txt /tmp/shared_requirements.txt

# Переключаемся на пользователя botuser и устанавливаем пакеты в его домашнюю директорию
USER botuser
RUN pip install --no-cache-dir --user \
    -r /tmp/requirements.txt \
    -r /tmp/shared_requirements.txt

# Финальный образ
FROM python:3.11-slim

# Создаем того же пользователя botuser
RUN useradd --create-home --shell /bin/bash botuser

# Копируем установленные пакеты (уже с правильным владельцем)
COPY --from=builder --chown=botuser:botuser /home/botuser/.local /home/botuser/.local

# Добавляем .local/bin в PATH для пользователя botuser
ENV PATH=/home/botuser/.local/bin:$PATH

# Создаем рабочую директорию
WORKDIR /app

# Копируем shared модули
COPY services/shared ./shared

# Копируем код приложения
COPY services/telegram-bot .

# Устанавливаем права на директорию
RUN chown -R botuser:botuser /app

# Переключаемся на пользователя botuser
USER botuser

# Добавляем PYTHONPATH для shared модулей
ENV PYTHONPATH=/app:$PYTHONPATH

# Запускаем бота
CMD ["python", "main.py"] 