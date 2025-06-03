# 🤖 POLIOM HR Assistant

Корпоративный Telegram бот-помощник для HR департамента POLIOM с админ-панелью для обработки документов и ответов на вопросы на основе содержимого документов (RAG - Retrieval-Augmented Generation).

## 🚀 Возможности

- 🤖 **Telegram бот** - POLIOM HR Assistant для сотрудников
- 🧠 **GigaChat интеграция** - российская LLM для генерации ответов
- 📄 **Обработка документов**: PDF, DOCX, TXT 
- 🔧 **Админ-панель** для управления документами и пользователями
- 🔍 **Векторный поиск** с PostgreSQL + pgvector
- ⚡ **Асинхронная обработка** с Celery
- 🐳 **Docker** для простого деплоя

## 📋 Требования

- Python 3.11+
- PostgreSQL с pgvector
- Redis
- Docker & Docker Compose
- GigaChat API ключ
- Telegram Bot Token

## 🔑 Ключевые характеристики проекта

- **База данных**: `poliom` (PostgreSQL на порту 5433)
- **Бот**: `@poliom_hr_bot` (токен уже настроен)
- **LLM**: GigaChat (российская модель)
- **Эмбеддинги**: sentence-transformers
- **Целевая аудитория**: HR департамент и сотрудники POLIOM

## 🏃‍♂️ Быстрый старт

### Локально (разработка)
```bash
# 1. Клонируйте репозиторий
git clone <repository-url>
cd poliom

# 2. Создайте .env файл на основе .env.production
cp .env.production .env.local

# 3. Отредактируйте переменные для локального использования
# DATABASE_URL=postgresql://postgres:postgres@localhost:5433/poliom
# REDIS_URL=redis://localhost:6379/0

# 4. Запустите с помощью Docker Compose
docker-compose up -d
```

### Продакшн развертывание

#### 🇷🇺 VK Cloud (рекомендуется для России)
```bash
# Автоматическое развертывание на VK Cloud
cd deploy_scripts
.\vk_cloud_setup.ps1  # Windows
# или
./vk_cloud_setup.sh   # Linux/macOS
```

#### 🌍 DigitalOcean (международный)
Следуйте подробной инструкции в [SETUP_GUIDE.md](SETUP_GUIDE.md)

## 📚 Документация

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Пошаговое руководство для новичков
- [CHECKLIST.md](CHECKLIST.md) - Чеклист для деплоя 
- [DEPLOYMENT.md](DEPLOYMENT.md) - Подробная инструкция по деплою
- [QUICK_START.md](QUICK_START.md) - Быстрый старт
- [hosting_comparison.md](hosting_comparison.md) - Сравнение хостинг-провайдеров
- **🆕 [DEPLOY_VK_CLOUD.md](DEPLOY_VK_CLOUD.md)** - Полное руководство по VK Cloud
- **🆕 [VK_CLOUD_CHECKLIST.md](VK_CLOUD_CHECKLIST.md)** - Чек-лист для VK Cloud
- **🆕 [deploy_scripts/README.md](deploy_scripts/README.md)** - Автоматизация развертывания

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ POLIOM HR Bot   │    │   Admin Panel   │    │  Celery Worker  │
│                 │    │                 │    │                 │
│  - Получение    │    │  - Загрузка     │    │  - Обработка    │
│    вопросов     │    │    документов   │    │    документов   │
│  - GigaChat     │    │  - Управление   │    │  - Векторизация │
│    интеграция   │    │    пользователями│    │  - Индексация   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
              ┌─────────────────────────────────────┐
              │           SHARED SERVICES           │
              │                                     │
              │  ┌─────────────┐  ┌─────────────┐   │
              │  │ PostgreSQL  │  │    Redis    │   │
              │  │ + pgvector  │  │             │   │
              │  │   (poliom)  │  │ - Кэш       │   │
              │  │             │  │ - Очереди   │   │
              │  │ - Документы │  │ - Сессии    │   │
              │  │ - Векторы   │  │             │   │
              │  │ - Пользо-   │  │             │   │
              │  │   ватели    │  │             │   │
              │  └─────────────┘  └─────────────┘   │
              └─────────────────────────────────────┘
```

## 🔧 Конфигурация

### Основные переменные
```env
# Telegram бот (уже настроен)
TELEGRAM_BOT_TOKEN=8193143410:AAGYCMxno9-DoslEFMTGX_vKuAM0meEwKrA

# GigaChat (уже настроен)
GIGACHAT_API_KEY=NDg5N2EwOTctMjE1MS00NzU1LTg1YjItN2Y4MzY0NzhjMWVlOjUwMDE2OTJkLTVhNzItNDI0MC05NDU5LWI0ZmM2YzkwNzcwMw==
GIGACHAT_SCOPE=GIGACHAT_API_PERS

# База данных POLIOM
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/poliom
REDIS_URL=redis://localhost:6379/0
```

### ML модели
```env
EMBEDDING_MODEL=all-MiniLM-L6-v2
TRANSFORMERS_CACHE=/app/models_cache
SEARCH_LIMIT=5
SIMILARITY_THRESHOLD=0.7
```

## 🛠️ Разработка

### Структура проекта
```
├── services/
│   ├── telegram-bot/     # POLIOM HR Telegram бот
│   ├── admin-panel/      # Веб админ-панель
│   └── shared/           # Общие модули
├── uploads/              # Загруженные документы
├── docker-compose.yml    # Для разработки
├── docker-compose.prod.yml # Для продакшна
├── requirements.txt      # Все зависимости
└── deploy.sh            # Скрипт деплоя
```

### Запуск в dev режиме
```bash
# Для POLIOM HR бота
cd services/telegram-bot
python main.py

# Для админ-панели
cd services/admin-panel
python main.py

# Для Celery worker
cd services/admin-panel
celery -A celery_app worker --loglevel=info
```

## 📊 Мониторинг

### Проверка статуса
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f poliom_telegram_bot_prod
```

### Метрики
- Использование памяти
- Количество обработанных документов
- Время ответа бота и GigaChat
- Размер очередей Celery

## 🔐 Безопасность

- Все API ключи в переменных окружения
- Контейнеры запускаются от непривилегированного пользователя
- HTTPS в продакшене
- Валидация входных данных
- Rate limiting для API

## 💰 Стоимость продакшна

### 🇷🇺 VK Cloud (рекомендуется для России)
- **Welcome bonus**: 5000₽ бесплатно для новых пользователей
- Kubernetes кластер (3 узла): ~15,000₽/месяц
- PostgreSQL с pgvector: ~8,000₽/месяц
- Object Storage: ~1,000₽/месяц
- Load Balancer: ~1,500₽/месяц
- **Итого**: ~27,500₽/месяц (первый месяц ~22,500₽ с бонусом)

### 🌍 DigitalOcean (международный)
- Droplet (4GB RAM): $24/месяц
- PostgreSQL + pgvector: $15/месяц  
- Redis: $15/месяц
- **Итого**: ~$54/месяц
- **Первые 60 дней БЕСПЛАТНО** ($200 кредитов)

## 🚀 Готов к деплою

Проект полностью готов к развертыванию в продакшене на разных платформах:

### ✅ VK Cloud (автоматизированное развертывание)
- 🤖 **Автоматические скрипты** для развертывания
- ☁️ **Kubernetes** с автомасштабированием
- 🗄️ **Managed PostgreSQL** с pgvector из коробки
- 📦 **Object Storage** для файлов
- 📊 **Мониторинг** и логирование
- 🛡️ **Безопасность** и резервное копирование

### ✅ DigitalOcean (проверено в продакшене)
- 📖 Подробная документация
- 🔧 Готовые скрипты деплоя
- ✅ Проверенные конфигурации

## 📞 Поддержка

- 📖 Полная документация в директории проекта
- 🔧 Готовые скрипты деплоя и конфигурации
- ✅ Чеклист для контроля всех этапов
- 🤖 Автоматизированные скрипты для VK Cloud

---

🎉 **Удачного использования POLIOM HR Assistant!** 