# План миграции на BGE-M3

## Обзор миграции

Переход с `cointegrated/rubert-tiny2` на `BAAI/bge-m3` требует комплексных изменений в архитектуре системы из-за кардинальных различий между моделями.

## Сравнение моделей

### Текущая модель: rubert-tiny2
- **Размер**: 29M параметров
- **Размерность эмбеддингов**: 312
- **Максимальная длина**: 512 токенов
- **Язык**: Русский
- **Тип**: Локальная модель
- **Память**: ~120MB

### Целевая модель: BGE-M3
- **Размер**: 567M параметров (+1850%)
- **Размерность эмбеддингов**: 1024 (+228%)
- **Максимальная длина**: 8192 токена (+1500%)
- **Язык**: Мультиязычная (100+ языков)
- **Тип**: Трансформер с attention
- **Память**: ~2.3GB (+1817%)

## Этапы миграции

### Этап 1: Подготовка инфраструктуры

#### 1.1 Системные требования
```bash
# Минимальные требования
RAM: 8GB → 16GB
GPU: Опционально → Рекомендуется (4GB+ VRAM)
Диск: +3GB для модели
```

#### 1.2 Зависимости
```bash
# Обновление requirements.txt
sentence-transformers>=2.2.2
torch>=1.13.0
transformers>=4.21.0
```

### Этап 2: Модификация кода

#### 2.1 Обновление embedding сервиса
**Файл**: `services/shared/utils/embeddings.py`

```python
# Новый класс для BGE-M3
class BGEEmbeddings:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('BAAI/bge-m3')
        self.dimension = 1024
        self.max_length = 8192
        
    def create_embedding(self, text: str) -> List[float]:
        # Обрезка текста до максимальной длины
        if len(text) > self.max_length:
            text = text[:self.max_length]
        return self.model.encode(text).tolist()
```

#### 2.2 Обновление конфигурации
**Файл**: `.env.example`
```env
# Обновленные параметры
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIMENSION=1024
MAX_CHUNK_SIZE=6000  # Увеличено с 1500
CHUNK_OVERLAP=300    # Увеличено с 150
```

#### 2.3 Модификация обработки текста
**Файл**: `services/shared/utils/text_processing.py`

```python
def chunk_text(text: str, chunk_size: int = 6000, overlap: int = 300) -> List[str]:
    """
    Увеличенные размеры чанков для BGE-M3
    """
    # Обновленная логика чанкинга
```

#### 2.4 Обновление базы данных
```sql
-- Миграция схемы БД
ALTER TABLE document_chunks 
ADD COLUMN new_embedding VECTOR(1024);

-- Индекс для новых эмбеддингов
CREATE INDEX idx_new_embedding ON document_chunks 
USING ivfflat (new_embedding vector_cosine_ops);
```

### Этап 3: Миграция данных

#### 3.1 Скрипт пересчета эмбеддингов
**Файл**: `services/admin-panel/migrate_to_bge_m3.py`

```python
import asyncio
from services.shared.utils.embeddings import BGEEmbeddings
from services.shared.models.document import DocumentChunk

async def migrate_embeddings():
    """
    Пересчет всех эмбеддингов с BGE-M3
    """
    bge = BGEEmbeddings()
    chunks = DocumentChunk.select()
    
    for chunk in chunks:
        new_embedding = bge.create_embedding(chunk.content)
        chunk.new_embedding = new_embedding
        chunk.save()
        
    print(f"Migrated {chunks.count()} chunks")
```

#### 3.2 Обновление поисковых параметров
**Файл**: `services/shared/utils/simple_rag.py`

```python
# Новые параметры поиска
SEARCH_LIMIT = 15        # Уменьшено с 25
SIMILARITY_THRESHOLD = 0.5  # Увеличено с 0.4
```

### Этап 4: Оптимизация производительности

#### 4.1 Кэширование эмбеддингов
```python
from functools import lru_cache

class BGEEmbeddings:
    @lru_cache(maxsize=1000)
    def create_embedding_cached(self, text: str) -> tuple:
        return tuple(self.create_embedding(text))
```

#### 4.2 Батчевая обработка
```python
def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
    """Обработка нескольких текстов за раз"""
    return self.model.encode(texts).tolist()
```

#### 4.3 GPU ускорение
```python
import torch

class BGEEmbeddings:
    def __init__(self):
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = SentenceTransformer('BAAI/bge-m3', device=device)
```

### Этап 5: Тестирование

#### 5.1 Юнит-тесты
**Файл**: `tests/test_bge_embeddings.py`

```python
def test_embedding_dimension():
    bge = BGEEmbeddings()
    embedding = bge.create_embedding("тест")
    assert len(embedding) == 1024

def test_similarity_calculation():
    bge = BGEEmbeddings()
    emb1 = bge.create_embedding("зарплата")
    emb2 = bge.create_embedding("заработная плата")
    similarity = cosine_similarity([emb1], [emb2])[0][0]
    assert similarity > 0.7
```

#### 5.2 Интеграционные тесты
```python
def test_search_quality():
    """Тест качества поиска с BGE-M3"""
    query = "когда выплачивается зарплата"
    results = search_documents(query)
    assert len(results) > 0
    assert any("зарплата" in r.content.lower() for r in results)
```

### Этап 6: Развертывание

#### 6.1 Поэтапное развертывание
1. **Тестовая среда**: Полная миграция и тестирование
2. **A/B тестирование**: Параллельная работа обеих моделей
3. **Постепенный переход**: 10% → 50% → 100% трафика
4. **Мониторинг**: Отслеживание качества и производительности

#### 6.2 Откат (Rollback план)
```python
# Переключение обратно на rubert-tiny2
EMBEDDING_MODEL=cointegrated/rubert-tiny2
EMBEDDING_DIMENSION=312
# Использование старых эмбеддингов из БД
```

## Ожидаемые улучшения

### Качество поиска
- **Точность**: +15-20% благодаря лучшему пониманию контекста
- **Полнота**: +25% за счет поддержки длинных документов
- **Мультиязычность**: Поддержка запросов на разных языках

### Производительность
- **Скорость поиска**: Без изменений (оптимизированные индексы)
- **Время создания эмбеддингов**: +300% (компенсируется батчевой обработкой)
- **Потребление памяти**: +1800% (требует масштабирования)

## Риски и митигация

### Технические риски
1. **Нехватка памяти**: Увеличение RAM серверов
2. **Медленная обработка**: GPU ускорение + батчинг
3. **Совместимость**: Тщательное тестирование зависимостей

### Бизнес риски
1. **Время простоя**: Поэтапная миграция без остановки сервиса
2. **Ухудшение качества**: A/B тестирование перед полным переходом
3. **Увеличение затрат**: Планирование бюджета на инфраструктуру

## Временные рамки

- **Подготовка**: 1-2 дня
- **Разработка**: 3-5 дней
- **Тестирование**: 2-3 дня
- **Миграция данных**: 1-2 дня (в зависимости от объема)
- **Развертывание**: 1 день
- **Мониторинг**: 1-2 недели

**Общее время**: 2-3 недели

## Заключение

Миграция на BGE-M3 значительно улучшит качество поиска и расширит возможности системы, но потребует существенных изменений в архитектуре и увеличения ресурсов. Поэтапный подход с тщательным тестированием минимизирует риски и обеспечит плавный переход. 