import asyncio
import os

from google import genai
from google.genai import types
from groq import AsyncGroq

from app.config import settings
from app.core.exceptions import LLMProviderError
from app.core.logging import logger
from app.infrastructure.llm.base import LLMClientBase


class GoogleLLMAdapter(LLMClientBase):
    """Google Gemini LLM provider with retry, backoff, and timeout."""

    MAX_RETRIES = 3
    BASE_DELAY = 2.0  # seconds
    TIMEOUT = 30  # seconds per request

    def __init__(self, model_name: str, api_key: str | None = None):
        self.model = model_name
        self._api_key = api_key
        self._client = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            api_key = self._api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY is not configured.")
                raise LLMProviderError("GEMINI_API_KEY is not configured in settings or environment variables.")
            self._client = genai.Client(api_key=api_key)
        return self._client

    async def ainvoke(self, messages: list[dict], **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.0)
        
        # Convert dictionary messages to Google GenAI Content types
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))
            
        config = types.GenerateContentConfig(temperature=temperature)
        
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"Invoking Gemini {self.model} (attempt {attempt}/{self.MAX_RETRIES})...")
                
                response = await asyncio.wait_for(
                    self.client.aio.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=config
                    ),
                    timeout=self.TIMEOUT
                )
                logger.info("Successfully received response from Google Gemini.")
                return response.text or ""
                
            except TimeoutError:
                last_error = f"Request timed out after {self.TIMEOUT}s"
                logger.warning(f"Gemini timeout on attempt {attempt}/{self.MAX_RETRIES}")
            except Exception as e:
                last_error = str(e)
                is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                
                if is_rate_limit and attempt < self.MAX_RETRIES:
                    delay = self.BASE_DELAY * (2 ** (attempt - 1))  # exponential backoff
                    logger.warning(f"Gemini rate limited (attempt {attempt}). Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                elif attempt < self.MAX_RETRIES:
                    delay = self.BASE_DELAY * attempt
                    logger.warning(f"Gemini error on attempt {attempt}: {e}. Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Gemini failed after {self.MAX_RETRIES} attempts: {e}")
        
        raise LLMProviderError(f"Gemini API failed after {self.MAX_RETRIES} attempts. Last error: {last_error}")


class GroqLLMAdapter(LLMClientBase):
    """Groq LLM provider with retry, backoff, and timeout."""

    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    TIMEOUT = 20

    def __init__(self, model_name: str, api_key: str | None = None):
        self.model = model_name
        self._api_key = api_key
        self._client = None

    @property
    def client(self) -> AsyncGroq:
        if self._client is None:
            api_key = self._api_key or settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.error("GROQ_API_KEY is not configured.")
                raise LLMProviderError("GROQ_API_KEY is not configured in settings or environment variables.")
            self._client = AsyncGroq(api_key=api_key)
        return self._client

    async def ainvoke(self, messages: list[dict], **kwargs) -> str:
        temperature = kwargs.get("temperature", 0.0)
        
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"Invoking Groq {self.model} (attempt {attempt}/{self.MAX_RETRIES})...")
                
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature
                    ),
                    timeout=self.TIMEOUT
                )
                logger.info("Successfully received response from Groq.")
                return response.choices[0].message.content or ""
                
            except TimeoutError:
                last_error = f"Request timed out after {self.TIMEOUT}s"
                logger.warning(f"Groq timeout on attempt {attempt}/{self.MAX_RETRIES}")
            except Exception as e:
                last_error = str(e)
                if attempt < self.MAX_RETRIES:
                    delay = self.BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(f"Groq error on attempt {attempt}: {e}. Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Groq failed after {self.MAX_RETRIES} attempts: {e}")
        
        raise LLMProviderError(f"Groq API failed after {self.MAX_RETRIES} attempts. Last error: {last_error}")


def get_llm_client(provider: str, model_name: str) -> LLMClientBase:
    """Helper factory function to retrieve the configured LLM Client adapter."""
    provider_lower = provider.lower()
    if provider_lower == "google":
        return GoogleLLMAdapter(model_name)
    elif provider_lower == "groq":
        return GroqLLMAdapter(model_name)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported options: google, groq.")
