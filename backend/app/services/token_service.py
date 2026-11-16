"""
Token counting, context budget management, and cost estimation service.
"""
from typing import List, Tuple
from app.core.config import settings
from app.schemas.retrieval import RetrievedChunk

try:
    import tiktoken
    _TIKTOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")
except Exception:
    _TIKTOKEN_ENCODER = None


class TokenService:
    @staticmethod
    def count_tokens(text: str) -> int:
        """Accurately counts tokens using cl100k_base or fallback heuristic."""
        if not text:
            return 0
        if _TIKTOKEN_ENCODER is not None:
            try:
                return len(_TIKTOKEN_ENCODER.encode(text, disallowed_special=()))
            except Exception:
                pass
        # Fallback approximation: 1 token ~= 4 characters in English
        return max(1, len(text) // 4)

    @staticmethod
    def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates estimated cost in USD based on configured model pricing."""
        prompt_cost = (prompt_tokens / 1000.0) * settings.INPUT_TOKEN_PRICE_PER_1K
        completion_cost = (completion_tokens / 1000.0) * settings.OUTPUT_TOKEN_PRICE_PER_1K
        return round(prompt_cost + completion_cost, 6)

    @classmethod
    def fit_chunks_within_budget(
        cls,
        chunks: List[RetrievedChunk],
        max_token_budget: int = 2500
    ) -> Tuple[List[RetrievedChunk], int]:
        """
        Deduplicates and selects top chunks fitting strictly within the token budget.
        Returns (selected_chunks, total_tokens_used).
        """
        selected: List[RetrievedChunk] = []
        total_tokens = 0
        seen_chunk_ids = set()

        for chunk in chunks:
            if chunk.chunk_id in seen_chunk_ids:
                continue
            chunk_tokens = chunk.token_count or cls.count_tokens(chunk.original_text)
            if total_tokens + chunk_tokens <= max_token_budget:
                selected.append(chunk)
                seen_chunk_ids.add(chunk.chunk_id)
                total_tokens += chunk_tokens
            else:
                # If cannot fit full chunk and we have nothing yet, take a truncated version if needed
                if not selected and chunk_tokens > max_token_budget:
                    # Truncate text to fit budget
                    truncated_text = chunk.original_text[: max_token_budget * 4]
                    truncated_chunk = chunk.model_copy(update={
                        "original_text": truncated_text,
                        "token_count": max_token_budget
                    })
                    selected.append(truncated_chunk)
                    total_tokens += max_token_budget
                break

        return selected, total_tokens
