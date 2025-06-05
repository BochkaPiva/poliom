#!/usr/bin/env python3

# Читаем файл
with open('/app/bot/handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Простая замена проблемного блока
old_text = '''                    # Добавляем источники
                    if result.get('sources'):
                        response_text += "\\n\\n📚 **Источники:**"
                        for j, source in enumerate(result['sources'], 1):
                            title = source.get('title', 'Документ')
                            if len(title) > 5:  # Исключаем слишком короткие названия
                                response_text += f"\\n{j}. {title}"'''

new_text = '''                    # Добавляем источники
                    if result.get('sources'):
                        files = result.get('files', [])
                        response_text += "\\n\\n📚 **Источники:**"
                        for i, file in enumerate(files, 1):
                            response_text += f"\\n{i}. {file.get('title', 'Документ')}"'''

# Заменяем
content = content.replace(old_text, new_text)

# Записываем
with open('/app/bot/handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Исправлено!") 