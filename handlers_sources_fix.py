# Исправленная логика формирования источников для handlers.py
# Заменить строки 679-697 в current_handlers.py

                        # Показываем источники на основе файлов (они уже правильно отфильтрованы в RAG)
                        files = result.get('files', [])
                        
                        if files:
                            response_text += "\n\n📚 **Источники:**"
                            for i, file in enumerate(files, 1):
                                title = file.get('title', 'Документ')
                                if len(title) > 5:  # Исключаем слишком короткие названия
                                    response_text += f"\n{i}. {title}" 