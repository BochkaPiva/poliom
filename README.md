# RAG Chatbot - Корпоративный чат-бот с поиском по документам

Интеллектуальный чат-бот для корпоративного использования с возможностью поиска информации в загруженных документах на основе технологии RAG (Retrieval-Augmented Generation).

## 🚀 Возможности

- **Telegram бот** для взаимодействия с пользователями
- **Веб-панель администратора** для управления системой
- **Загрузка и обработка документов** (PDF, DOCX, TXT)
- **Поиск по документам** с использованием векторного поиска
- **Интеграция с GigaChat** для генерации ответов
- **Управление пользователями** и администраторами
- **Мониторинг запросов** и статистика

## 🏗️ Архитектура

Проект состоит из следующих компонентов:

- **Admin Panel** - веб-интерфейс для администраторов
- **Telegram Bot** - бот для пользователей
- **Shared** - общие модули (модели БД, утилиты)
- **PostgreSQL** - основная база данных
- **Redis** - кэширование и очереди задач
- **Celery** - асинхронная обработка документов

## 🛠️ Технологии

- **Backend**: FastAPI, SQLAlchemy, Celery
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: PostgreSQL, Redis
- **ML/AI**: Transformers, Sentence-Transformers, GigaChat API
- **Deployment**: Docker, Docker Compose

## 📋 Требования

- Docker и Docker Compose
- Python 3.11+ (для локальной разработки)
- PostgreSQL 15+
- Redis 7+

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/BochkaPiva/poliom.git
cd poliom
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и настройте переменные:

```bash
cp .env.example .env
```

Основные переменные:
- `POSTGRES_PASSWORD` - пароль для PostgreSQL
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `GIGACHAT_API_KEY` - ключ API GigaChat

### 3. Запуск с Docker

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### 4. Доступ к сервисам

- **Админ-панель**: http://localhost:8001
  - Логин: `admin`
  - Пароль: `admin123`
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Локальная разработка

### Настройка админ-панели

```bash
cd services/admin-panel

# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Установка зависимостей
pip install -r requirements.txt

# Запуск локально
python run_local.py
```

### Настройка Telegram бота

```bash
cd services/telegram-bot

# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск локально
python run_local.py
```

## 📊 Использование

### Загрузка документов

1. Войдите в админ-панель
2. Перейдите в раздел "Документы"
3. Загрузите файлы (PDF, DOCX, TXT)
4. Дождитесь обработки документов

### Настройка Telegram бота

1. Создайте бота через @BotFather
2. Получите токен и добавьте в `.env`
3. Запустите сервисы
4. Начните диалог с ботом

### Управление пользователями

- Просмотр всех пользователей
- Блокировка/разблокировка
- Статистика запросов
- История взаимодействий

## 🔒 Безопасность

- Аутентификация администраторов
- Валидация загружаемых файлов
- Ограничения размера файлов
- Логирование всех действий

## 📈 Мониторинг

- Статистика использования
- Логи обработки документов
- Мониторинг производительности
- Отслеживание ошибок

## 🤝 Разработка

### Структура проекта

```
poliom/
├── services/
│   ├── admin-panel/     # Веб-панель администратора
│   ├── telegram-bot/    # Telegram бот
│   └── shared/          # Общие модули
├── docker-compose.yml   # Конфигурация Docker
├── .env                 # Переменные окружения
└── README.md           # Документация
```

### Добавление новых функций

1. Создайте ветку для новой функции
2. Внесите изменения
3. Добавьте тесты
4. Создайте Pull Request

## 📝 API

### Admin Panel API

- `GET /` - Главная страница
- `GET /documents` - Управление документами
- `POST /documents/upload` - Загрузка документа
- `GET /users` - Управление пользователями
- `GET /admins` - Управление администраторами

### Telegram Bot

- `/start` - Начало работы
- `/help` - Справка
- Текстовые сообщения - поиск по документам

## 🐛 Устранение неполадок

### Проблемы с подключением к БД

```bash
# Проверка статуса PostgreSQL
docker-compose ps postgres

# Просмотр логов
docker-compose logs postgres
```

### Проблемы с обработкой документов

```bash
# Проверка Celery worker
docker-compose logs celery-worker

# Перезапуск обработки
docker-compose restart celery-worker
```

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 👥 Авторы

- [BochkaPiva](https://github.com/BochkaPiva)

## 🙏 Благодарности

- [Hugging Face](https://huggingface.co/) за модели трансформеров
- [FastAPI](https://fastapi.tiangolo.com/) за отличный веб-фреймворк
- [SQLAlchemy](https://www.sqlalchemy.org/) за ORM 