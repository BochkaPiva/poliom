# 🔍 АНАЛИЗ: ПОЧЕМУ DOCKER ЗАНЯЛ 100GB

## 🚨 ОСНОВНЫЕ ПРИЧИНЫ:

### 1. **НАКОПЛЕНИЕ НЕИСПОЛЬЗУЕМЫХ ОБРАЗОВ**
```bash
# Каждый docker pull скачивает образ:
docker pull postgres:13    # ~300MB
docker pull redis:latest   # ~100MB  
docker pull nginx:alpine   # ~50MB
docker pull python:3.11    # ~900MB
# Итого: уже 1.35GB только базовых образов
```

### 2. **МНОЖЕСТВЕННЫЕ ВЕРСИИ ОБРАЗОВ**
```bash
# При обновлениях старые версии остаются:
myapp:v1.0    # 500MB
myapp:v1.1    # 500MB  
myapp:v1.2    # 500MB
myapp:latest  # 500MB
# Итого: 2GB для одного приложения
```

### 3. **BUILD CACHE (КЭШИРОВАНИЕ СБОРКИ)**
```bash
# При каждом docker build создается кэш:
RUN pip install requirements.txt  # 200MB кэш
RUN npm install                   # 500MB кэш
RUN apt-get update && install...  # 300MB кэш
# Кэш может достигать 10-20GB!
```

### 4. **VOLUMES (ПОСТОЯННЫЕ ДАННЫЕ)**
```bash
# Базы данных, файлы, логи:
postgres_data     # 5-10GB
elasticsearch_data # 10-20GB
logs_volume       # 1-5GB
uploads_volume    # 2-10GB
```

### 5. **ОСТАНОВЛЕННЫЕ КОНТЕЙНЕРЫ**
```bash
# Каждый остановленный контейнер сохраняется:
docker ps -a  # Показывает ВСЕ контейнеры
# Может быть 50-100 старых контейнеров по 100-500MB каждый
```

## 📊 ТИПИЧНОЕ РАСПРЕДЕЛЕНИЕ 100GB:

```
Docker Data (100GB):
├── 40GB - Образы (images)
├── 25GB - Build cache  
├── 20GB - Volumes (данные БД)
├── 10GB - Остановленные контейнеры
└── 5GB  - Системные файлы WSL2
```

## ✅ КАК ПРЕДОТВРАТИТЬ В БУДУЩЕМ:

### 1. **РЕГУЛЯРНАЯ ОЧИСТКА (раз в неделю):**
```bash
# Удалить неиспользуемые образы:
docker image prune -a

# Удалить остановленные контейнеры:
docker container prune

# Удалить неиспользуемые volumes:
docker volume prune

# ПОЛНАЯ ОЧИСТКА (осторожно!):
docker system prune -a --volumes
```

### 2. **МОНИТОРИНГ РАЗМЕРА:**
```bash
# Проверить размер Docker:
docker system df

# Детальная информация:
docker system df -v
```

### 3. **НАСТРОЙКА ЛИМИТОВ:**
```json
// В Docker Desktop Settings:
{
  "disk-size-gb": 20,  // Ограничить до 20GB
  "memory-gb": 4,
  "swap-gb": 1
}
```

### 4. **АВТОМАТИЧЕСКАЯ ОЧИСТКА:**
```bash
# Добавить в cron/планировщик:
# Каждое воскресенье в 2:00
0 2 * * 0 docker system prune -f
```

### 5. **ОПТИМИЗАЦИЯ ОБРАЗОВ:**
```dockerfile
# Использовать alpine образы:
FROM python:3.11-alpine  # вместо python:3.11

# Многоэтапная сборка:
FROM node:alpine as builder
# ... сборка
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

## 🛠️ РЕКОМЕНДУЕМЫЕ НАСТРОЙКИ:

### Docker Desktop Settings:
- **Disk Size:** 20-30GB (вместо unlimited)
- **Memory:** 4-6GB  
- **Enable Resource Saver:** ✅
- **Auto-cleanup:** ✅

### Регулярное обслуживание:
```bash
# Еженедельный скрипт очистки:
#!/bin/bash
echo "Очистка Docker..."
docker container prune -f
docker image prune -f  
docker volume prune -f
docker builder prune -f
echo "Готово!"
```

## 🚨 ПРИЗНАКИ ПРОБЛЕМЫ:

- Диск C: заполнен > 90%
- Docker Desktop тормозит
- Ошибки "No space left on device"
- WSL2 потребляет много RAM

## 💡 ПРОФИЛАКТИКА:

1. **Мониторинг:** Проверять `docker system df` раз в неделю
2. **Очистка:** Запускать `docker system prune` после проектов  
3. **Лимиты:** Установить ограничения в Docker Desktop
4. **Образы:** Использовать легкие alpine образы
5. **Volumes:** Регулярно проверять и очищать данные

---

**🎯 ВЫВОД:** Docker может легко занять 100GB без регулярного обслуживания. Это нормально для активной разработки, но требует контроля! 