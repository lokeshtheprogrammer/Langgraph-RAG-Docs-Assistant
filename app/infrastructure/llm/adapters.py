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
                text = response.text
                if not text or not text.strip():
                    # Safety filter or unexpected empty finish — treat as retryable error
                    finish = getattr(response, 'candidates', [{}])
                    reason = finish[0].finish_reason if finish else 'UNKNOWN'
                    raise LLMProviderError(
                        f"Gemini returned an empty response (finish_reason={reason}). "
                        "This may be due to a safety filter or content policy block."
                    )
                return text
                
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
                text = response.choices[0].message.content
                if not text or not text.strip():
                    raise LLMProviderError(
                        "Groq returned an empty response. "
                        "This may be due to a content policy block or token limit."
                    )
                return text
                
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


class FallbackLLMAdapter(LLMClientBase):
    """Wraps a primary LLM client and falls back to a secondary client on failure."""

    def __init__(self, primary: LLMClientBase, secondary: LLMClientBase):
        self.primary = primary
        self.secondary = secondary

    async def ainvoke(self, messages: list[dict], **kwargs) -> str:
        try:
            return await self.primary.ainvoke(messages, **kwargs)
        except Exception as e:
            logger.warning(f"Primary LLM client failed: {e}. Falling back to secondary LLM client...")
            try:
                return await self.secondary.ainvoke(messages, **kwargs)
            except Exception as sec_e:
                logger.critical(f"Secondary LLM client also failed: {sec_e}")
                raise LLMProviderError(
                    f"Both primary and secondary LLM providers failed.\n"
                    f"Primary Error: {e}\n"
                    f"Secondary Error: {sec_e}"
                ) from sec_e


def get_llm_client(provider: str, model_name: str) -> LLMClientBase:
    """Helper factory function to retrieve the configured LLM Client adapter."""
    provider_lower = provider.lower()
    
    # Check if fallback provider can be enabled
    gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    
    if provider_lower == "google":
        google_client = GoogleLLMAdapter(model_name)
        if groq_key:
            # Use a robust, fast model on Groq as secondary fallback
            groq_client = GroqLLMAdapter("llama-3.3-70b-versatile", api_key=groq_key)
            logger.info("Enabling automatic fallback: Google Gemini -> Groq (llama-3.3-70b-versatile).")
            return FallbackLLMAdapter(google_client, groq_client)
        return google_client
        
    elif provider_lower == "groq":
        groq_client = GroqLLMAdapter(model_name)
        if gemini_key:
            # Use gemini-2.5-flash as secondary fallback
            google_client = GoogleLLMAdapter("gemini-2.5-flash", api_key=gemini_key)
            logger.info("Enabling automatic fallback: Groq -> Google Gemini (gemini-2.5-flash).")
            return FallbackLLMAdapter(groq_client, google_client)
        return groq_client
        
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported options: google, groq.")

