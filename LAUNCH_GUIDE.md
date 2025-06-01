# 🚀 Руководство по запуску корпоративного RAG чатбота

## ✅ Исправленная архитектура

### Что было исправлено:
1. **Убран Document Processor как отдельный сервис** - теперь обработка документов интегрирована в админ-панель
2. **Упрощена архитектура** - меньше HTTP запросов, более эффективная работа
3. **Celery для обработки документов** - асинхронная обработка в фоне
4. **Единая точка управления** - все в админ-панели

### Текущая архитектура:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   Admin Panel   │    │   PostgreSQL    │
│                 │    │                 │    │                 │
│ - Обработка     │◄──►│ - Управление    │◄──►│ - База данных   │
│   запросов      │    │   документами   │    │ - Пользователи  │
│ - RAG поиск     │    │ - Пользователи  │    │ - Документы     │
│                 │    │ - Администраторы│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       
         │              ┌─────────────────┐              
         │              │ Celery Worker   │              
         │              │                 │              
         └──────────────│ - Обработка     │              
                        │   документов    │              
                        │ - Создание      │              
                        │   эмбеддингов   │              
                        └─────────────────┘              
                                 │                       
                        ┌─────────────────┐              
                        │     Redis       │              
                        │                 │              
                        │ - Очереди       │              
                        │ - Кэширование   │              
                        └─────────────────┘              
```

## 🔧 Предварительная настройка

### 1. Проверьте файл .env
Убедитесь, что файл `.env` содержит все необходимые настройки:

```bash
# База данных
POSTGRES_DB=rag_chatbot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# GigaChat
GIGACHAT_API_KEY=your_gigachat_api_key_here
GIGACHAT_SCOPE=GIGACHAT_API_PERS

# Админ-панель
ADMIN_SECRET_KEY=super-secret-admin-key-change-in-production

# Дополнительные настройки
MAX_FILE_SIZE=52428800
LOG_LEVEL=INFO
```

### 2. Получите API ключи

#### Telegram Bot Token:
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

#### GigaChat API Key:
1. Зарегистрируйтесь на https://developers.sber.ru/
2. Создайте проект
3. Получите API ключ
4. Скопируйте в `.env`

## 🚀 Запуск системы

### 1. Запустите все сервисы
```bash
docker-compose up -d
```

### 2. Проверьте статус сервисов
```bash
docker-compose ps
```

Все сервисы должны быть в статусе "Up":
- `rag_postgres` - База данных
- `rag_redis` - Кэш и очереди
- `rag_admin_panel` - Админ-панель
- `rag_celery_worker` - Обработчик документов
- `rag_telegram_bot` - Telegram бот

### 3. Проверьте логи
```bash
# Все логи
docker-compose logs

# Конкретный сервис
docker-compose logs admin-panel
docker-compose logs celery-worker
docker-compose logs telegram-bot
```

## 📋 Первоначальная настройка

### 1. Создайте первого администратора
Откройте админ-панель: http://localhost:8001

Перейдите в раздел "Администраторы" и создайте первого админа.

### 2. Загрузите документы
1. Перейдите в раздел "Документы"
2. Нажмите "Загрузить документ"
3. Выберите файл (PDF, DOCX, TXT)
4. Заполните название и описание
5. Нажмите "Загрузить"

### 3. Проверьте обработку
Документы обрабатываются асинхронно через Celery. Статус можно отслеживать в админ-панели.

## 🔍 Тестирование

### 1. Проверьте Telegram бота
1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Задайте вопрос по загруженным документам

### 2. Проверьте админ-панель
- Управление документами: http://localhost:8001/documents
- Управление пользователями: http://localhost:8001/users
- Управление администраторами: http://localhost:8001/admins

## 🛠️ Мониторинг и отладка

### Проверка здоровья сервисов
```bash
# Проверка PostgreSQL
docker exec rag_postgres pg_isready -U postgres

# Проверка Redis
docker exec rag_redis redis-cli ping

# Проверка админ-панели
curl http://localhost:8001/

# Проверка Celery
docker exec rag_celery_worker celery -A celery_app inspect ping
```

### Просмотр логов в реальном времени
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f admin-panel
docker-compose logs -f celery-worker
docker-compose logs -f telegram-bot
```

### Перезапуск сервисов
```bash
# Перезапуск всех сервисов
docker-compose restart

# Перезапуск конкретного сервиса
docker-compose restart admin-panel
docker-compose restart celery-worker
docker-compose restart telegram-bot
```

## 🔧 Устранение неполадок

### Проблема: Сервис не запускается
1. Проверьте логи: `docker-compose logs [service-name]`
2. Проверьте переменные окружения в `.env`
3. Убедитесь, что порты не заняты

### Проблема: Документы не обрабатываются
1. Проверьте статус Celery: `docker-compose logs celery-worker`
2. Проверьте Redis: `docker exec rag_redis redis-cli ping`
3. Проверьте размер файла (максимум 50MB)

### Проблема: Бот не отвечает
1. Проверьте токен бота в `.env`
2. Проверьте логи: `docker-compose logs telegram-bot`
3. Убедитесь, что GigaChat API ключ корректный

### Проблема: Нет доступа к админ-панели
1. Проверьте, что порт 8001 свободен
2. Проверьте логи: `docker-compose logs admin-panel`
3. Попробуйте перезапустить: `docker-compose restart admin-panel`

## 📊 Производительность

### Рекомендуемые ресурсы:
- **RAM**: минимум 4GB, рекомендуется 8GB
- **CPU**: минимум 2 ядра, рекомендуется 4 ядра
- **Диск**: минимум 10GB свободного места

### Масштабирование:
```bash
# Увеличить количество Celery workers
docker-compose up -d --scale celery-worker=3
```

## 🔒 Безопасность

### В продакшене обязательно:
1. Смените `ADMIN_SECRET_KEY` на сложный ключ
2. Смените пароль PostgreSQL
3. Используйте HTTPS для админ-панели
4. Ограничьте доступ к портам через firewall

## 📈 Мониторинг

### Полезные команды:
```bash
# Использование ресурсов
docker stats

# Размер томов
docker system df

# Очистка неиспользуемых ресурсов
docker system prune
```

## ✅ Готово к работе!

После выполнения всех шагов у вас будет полностью рабочий корпоративный RAG чатбот:

1. **Админ-панель**: http://localhost:8001
2. **Telegram бот**: доступен по токену
3. **База данных**: PostgreSQL на порту 5432
4. **Redis**: на порту 6379

Система готова к загрузке документов и обслуживанию пользователей! 