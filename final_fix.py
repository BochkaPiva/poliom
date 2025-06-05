#!/usr/bin/env python3

# Читаем файл
with open('/app/bot/handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем сложную логику источников на простую
old_block = '''                        # Выводим синхронизированные источники только если они есть
                        if shown_sources:
                            response_text += "\\n\\n📚 **Источники:**"
                            for i, source in enumerate(shown_sources, 1):
                                title = source.get('title', 'Документ')
                                if len(title) > 5:  # Исключаем слишком короткие названия
                                    response_text += f"\\n{i}. {title}"'''

new_block = '''                        # Показываем файлы как источники
                        if files:
                            response_text += "\\n\\n📚 **Источники:**"
                            for i, file in enumerate(files, 1):
                                title = file.get('title', 'Документ')
                                response_text += f"\\n{i}. {title}"'''

# Заменяем
content = content.replace(old_block, new_block)

# Записываем
with open('/app/bot/handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Источники исправлены!") 