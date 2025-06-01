# services/shared/utils/llm_client.py

import logging
import requests
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Ответ от LLM"""
    text: str
    tokens_used: int
    model: str
    success: bool
    error: Optional[str] = None

class GigaChatClient:
    """Простой клиент для GigaChat - единственный LLM провайдер"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.model = "GigaChat"
        
    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запроса"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, 
                         prompt: str, 
                         max_tokens: int = 1000,
                         temperature: float = 0.7) -> LLMResponse:
        """
        Генерация ответа от GigaChat
        
        Args:
            prompt: Текст запроса
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации (0.0-1.0)
            
        Returns:
            LLMResponse: Ответ от модели
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                return LLMResponse(
                    text=data["choices"][0]["message"]["content"],
                    tokens_used=data.get("usage", {}).get("total_tokens", 0),
                    model=self.model,
                    success=True
                )
            else:
                logger.error(f"GigaChat API error: {response.status_code} - {response.text}")
                return LLMResponse(
                    text="",
                    tokens_used=0,
                    model=self.model,
                    success=False,
                    error=f"API error: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Error calling GigaChat: {str(e)}")
            return LLMResponse(
                text="",
                tokens_used=0,
                model=self.model,
                success=False,
                error=str(e)
            )

class SimpleLLMClient:
    """Упрощенный клиент - только GigaChat"""
    
    def __init__(self, gigachat_api_key: str):
        self.gigachat = GigaChatClient(gigachat_api_key)
        logger.info("Инициализирован простой LLM клиент с GigaChat")
    
    def generate_answer(self, 
                       context: str, 
                       question: str,
                       max_tokens: int = 1000) -> LLMResponse:
        """
        Генерация ответа на основе контекста
        
        Args:
            context: Контекст из найденных документов
            question: Вопрос пользователя
            max_tokens: Максимальное количество токенов
            
        Returns:
            LLMResponse: Ответ от модели
        """
        # Простой промпт для корпоративного чатбота
        prompt = f"""Ты - корпоративный помощник. Отвечай на вопросы сотрудников на основе предоставленной информации.

КОНТЕКСТ:
{context}

ВОПРОС: {question}

ИНСТРУКЦИИ:
- Отвечай только на основе предоставленного контекста
- Если информации недостаточно, скажи об этом честно
- Отвечай на русском языке
- Будь вежливым и профессиональным

ОТВЕТ:"""

        return self.gigachat.generate_response(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.3  # Низкая температура для более точных ответов
        )
    
    def health_check(self) -> bool:
        """Проверка работоспособности LLM"""
        try:
            response = self.gigachat.generate_response(
                prompt="Привет! Это тест.",
                max_tokens=50
            )
            return response.success
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False 