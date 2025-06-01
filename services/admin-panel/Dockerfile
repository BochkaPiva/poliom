# Multi-stage build для минимизации размера
FROM python:3.11-slim as builder

# Создаем пользователя app в builder stage
RUN useradd --create-home --shell /bin/bash app

# Устанавливаем зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY services/admin-panel/requirements.txt /tmp/requirements.txt
COPY services/shared/requirements.txt /tmp/shared_requirements.txt

# Переключаемся на пользователя app и устанавливаем пакеты в его домашнюю директорию
USER app
RUN pip install --no-cache-dir --user \
    -r /tmp/requirements.txt \
    -r /tmp/shared_requirements.txt

# Финальный образ
FROM python:3.11-slim

# Устанавливаем только runtime зависимости
RUN apt-get update && apt-get install -y \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаем того же пользователя app
RUN useradd --create-home --shell /bin/bash app

# Копируем установленные пакеты (уже с правильным владельцем)
COPY --from=builder --chown=app:app /home/app/.local /home/app/.local

# Создаем рабочую директорию
WORKDIR /app

# Копируем shared модули
COPY services/shared ./shared

# Копируем код приложения
COPY services/admin-panel .

# Создаем директории и устанавливаем права
RUN mkdir -p /app/uploads /app/static /app/templates \
    && chown -R app:app /app

# Переключаемся на пользователя app
USER app

# Добавляем .local/bin в PATH для пользователя app и PYTHONPATH для shared модулей
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Открываем порт
EXPOSE 8001

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"] 