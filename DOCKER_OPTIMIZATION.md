# 🐳 Оптимизация Docker для ML-приложений

## 📊 **Реальные размеры образов**

### ✅ **Нормальные размеры для RAG-системы:**
- **Admin Panel**: ~9GB (включает sentence-transformers + модели)
- **Telegram Bot**: ~9GB (та же база)
- **PostgreSQL**: ~600MB
- **Redis**: ~60MB

**Итого: ~19GB** - это **НОРМАЛЬНО** для ML-приложения!

## 🎯 **Почему образы большие?**

### **sentence-transformers включает:**
- Модель `ai-forever/sbert_large_nlu_ru`: ~1.5GB
- PyTorch: ~2GB
- Transformers библиотека: ~500MB
- Зависимости: ~1GB

**Это НЕОБХОДИМО для RAG функционала!**

## 🚀 **Оптимизации, которые мы применили**

### 1. **Multi-stage build**
```dockerfile
FROM python:3.11-slim as builder
# Сборка зависимостей

FROM python:3.11-slim
# Только runtime
```

### 2. **Кэширование моделей**
```yaml
volumes:
  - ml_models_cache:/app/models_cache
environment:
  - TRANSFORMERS_CACHE=/app/models_cache
```

### 3. **Ограничения ресурсов**
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

### 4. **Оптимизированные зависимости**
- Убраны дублирования
- Только необходимые пакеты
- Фиксированные версии

## 💡 **Стратегии экономии места**

### **1. Очистка неиспользуемых образов**
```bash
# Регулярно очищайте
docker system prune -a --volumes -f

# Удаляйте старые образы
docker image prune -a -f
```

### **2. Используйте .dockerignore**
```
*.md
.git/
__pycache__/
*.log
```

### **3. Сборка только нужных сервисов**
```bash
# Только админ-панель
docker-compose build admin-panel

# Только бот
docker-compose build telegram-bot
```

## 📈 **Требования к системе**

### **Минимальные требования:**
- **RAM**: 8GB (для комфортной работы)
- **Диск**: 30GB свободного места
- **CPU**: 4 ядра

### **Рекомендуемые:**
- **RAM**: 16GB
- **Диск**: 50GB SSD
- **CPU**: 8 ядер

## 🔧 **Команды для мониторинга**

### **Проверка размеров:**
```bash
# Размеры образов
docker images

# Использование диска
docker system df

# Детальная информация
docker system df -v
```

### **Очистка:**
```bash
# Полная очистка (ОСТОРОЖНО!)
docker system prune -a --volumes -f

# Только неиспользуемые образы
docker image prune -a -f

# Только build cache
docker builder prune -f
```

## 🎯 **Оптимизация для продакшена**

### **1. Используйте Docker Registry**
```bash
# Соберите один раз
docker-compose build

# Загрузите в registry
docker tag poliom-admin-panel:latest your-registry/admin-panel:v1.0
docker push your-registry/admin-panel:v1.0
```

### **2. Предзагрузка моделей**
```dockerfile
# В Dockerfile добавьте
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('ai-forever/sbert_large_nlu_ru')"
```

### **3. Используйте bind mounts для разработки**
```yaml
volumes:
  - ./services/admin-panel:/app:ro  # Read-only
```

## ✅ **Итоговые рекомендации**

### **Для разработки:**
1. **Соберите образы один раз**: `docker-compose build`
2. **Используйте volumes для данных**
3. **Регулярно очищайте**: `docker system prune -f`

### **Для продакшена:**
1. **Используйте Docker Registry**
2. **Предзагружайте модели в образ**
3. **Мониторьте использование ресурсов**

## 🚨 **ВАЖНО: НЕ УДАЛЯЙТЕ**

**sentence-transformers** - это ЯДРО RAG системы!
Без него система не сможет:
- Создавать эмбеддинги документов
- Искать релевантную информацию
- Отвечать на вопросы пользователей

**9GB образ - это нормально для ML-приложения!** 