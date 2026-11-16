"""
Unified LLM Provider with resilient fallback, timeout protection, retry backoff, and token tracking.
Supports OpenAI, Anthropic, Google Gemini, and deterministic offline Mock provider.
"""
import time
import json
import re
from typing import Dict, Any, Tuple, Optional, List
import httpx
from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.schemas.chat import AnswerResponse, Citation
from app.services.token_service import TokenService
from app.core.logging import get_logger

logger = get_logger("llm_provider")


class LLMClient:
    @classmethod
    def call_llm(
        cls,
        system_prompt: str,
        user_prompt: str,
        context_chunks: List[Any],
        temperature: float = 0.0,
        max_retries: int = 2
    ) -> Tuple[str, int, int]:
        """
        Executes LLM call with backoff and returns (raw_response_text, prompt_tokens, completion_tokens).
        """
        provider = settings.LLM_PROVIDER.lower()
        prompt_tokens = TokenService.count_tokens(system_prompt + "\n" + user_prompt)

        # 1. Deterministic Mock Provider (for offline development, CI, testing)
        if provider == "mock" or not (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY or settings.GEMINI_API_KEY):
            return cls._mock_generate(user_prompt, context_chunks, prompt_tokens)

        # 2. Live Providers with retry
        for attempt in range(max_retries + 1):
            try:
                if provider == "openai" and settings.OPENAI_API_KEY:
                    return cls._call_openai(system_prompt, user_prompt, temperature)
                elif provider == "anthropic" and settings.ANTHROPIC_API_KEY:
                    return cls._call_anthropic(system_prompt, user_prompt, temperature)
                elif provider == "google" and settings.GEMINI_API_KEY:
                    return cls._call_gemini(system_prompt, user_prompt, temperature)
                else:
                    return cls._mock_generate(user_prompt, context_chunks, prompt_tokens)
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries:
                    raise LLMProviderError(f"External LLM call failed after {max_retries + 1} attempts: {str(e)}")
                time.sleep(1.0 * (2 ** attempt))

        return cls._mock_generate(user_prompt, context_chunks, prompt_tokens)

    @classmethod
    def _mock_generate(
        cls,
        user_prompt: str,
        context_chunks: List[Any],
        prompt_tokens: int
    ) -> Tuple[str, int, int]:
        """
        Produces realistic grounded JSON structured output based strictly on provided context chunks.
        """
        if not context_chunks:
            resp = AnswerResponse(
                answer="I cannot answer this query based on the uploaded documents because no relevant evidence was found.",
                citations=[],
                confidence_label="insufficient_evidence",
                evidence_summary="No context chunks were retrieved matching the query.",
                warnings=["Insufficient evidence in knowledge base."]
            )
            raw = resp.model_dump_json()
            return raw, prompt_tokens, TokenService.count_tokens(raw)

        # Select primary supporting chunk
        top_chunk = context_chunks[0]
        chunk_text = getattr(top_chunk, "original_text", "")
        doc_id = getattr(top_chunk, "document_id", "doc-1")
        filename = getattr(top_chunk, "filename", "document.txt")
        cid = getattr(top_chunk, "chunk_id", "chunk-1")
        page_num = getattr(top_chunk, "page_number", 1)

        # Extract first 1-2 sentences for exact quoted_text
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chunk_text) if len(s.strip()) > 10]
        quote = sentences[0] if sentences else chunk_text[:120].strip()

        resp = AnswerResponse(
            answer=f"Based on {filename}, {quote}",
            citations=[
                Citation(
                    document_id=doc_id,
                    filename=filename,
                    chunk_id=cid,
                    page_number=page_num,
                    quoted_text=quote
                )
            ],
            confidence_label="supported",
            evidence_summary=f"Derived from {filename} chunk {cid}.",
            warnings=[]
        )
        raw = resp.model_dump_json()
        return raw, prompt_tokens, TokenService.count_tokens(raw)

    @classmethod
    def _call_openai(cls, system_prompt: str, user_prompt: str, temperature: float) -> Tuple[str, int, int]:
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

    @classmethod
    def _call_anthropic(cls, system_prompt: str, user_prompt: str, temperature: float) -> Tuple[str, int, int]:
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.LLM_MODEL or "claude-3-5-sonnet-20241022",
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": 1500,
            "temperature": temperature
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            return content, usage.get("input_tokens", 0), usage.get("output_tokens", 0)

    @classmethod
    def _call_gemini(cls, system_prompt: str, user_prompt: str, temperature: float) -> Tuple[str, int, int]:
        model = settings.LLM_MODEL or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json"
            }
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            return content, usage.get("promptTokenCount", 0), usage.get("candidatesTokenCount", 0)
