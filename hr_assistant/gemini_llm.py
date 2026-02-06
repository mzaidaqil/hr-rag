from __future__ import annotations

from typing import List, Optional

from google import genai
from google.genai import errors as genai_errors

from .config import Settings


class GeminiChat:
    def __init__(self, settings: Settings):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    def list_models(self) -> List[str]:
        try:
            return [m.name for m in self._client.models.list()]
        except Exception:
            return []

    def answer(self, *, system: str, user: str, temperature: float = 0.2) -> str:
        try:
            # Keep it simple: one system instruction + user prompt.
            resp = self._client.models.generate_content(
                model=self._model,
                contents=f"{system}\n\nUser:\n{user}",
                config={
                    "temperature": temperature,
                },
            )
            # google-genai returns `.text` for convenience.
            return (resp.text or "").strip()
        except genai_errors.ClientError as e:
            # Common case: wrong/unsupported model alias for this API key.
            available = self.list_models()
            hint = ""
            if available:
                # Show a small sample to avoid huge logs.
                sample = ", ".join(available[:10])
                hint = f" Available models (sample): {sample}"
            raise RuntimeError(
                f"Gemini generate_content failed for model '{self._model}'. "
                f"Set GEMINI_MODEL in your .env to an available model.{hint}"
            ) from e

