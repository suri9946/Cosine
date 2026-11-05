"""Small, fail-closed HTTP client for the project's already-installed Ollama models."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import requests
from dotenv import load_dotenv


PROJECT_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
CHEMLLM_MODEL = "hf.co/ceafgnigguh123/ChemLLM-7B-Chat-GGUF:Q4_K_M"
JUDGE_MODEL = "llama3.2:3b"


class OllamaError(RuntimeError):
    """Base error with user-safe messages (no request headers or secrets)."""


class OllamaUnavailable(OllamaError):
    """The local Ollama service could not be reached before timeout."""


class OllamaRequestFailed(OllamaError):
    """Ollama returned an HTTP or API-level error."""


class OllamaModelUnavailable(OllamaError):
    """The exact configured model name is not registered in Ollama."""


class OllamaResponseInvalid(OllamaError):
    """Ollama returned malformed or incomplete response data."""


@dataclass(frozen=True)
class OllamaChatResponse:
    model: str
    content: str
    raw: dict[str, Any]


class OllamaClient:
    """Use Ollama's local tags/show/chat APIs with bounded timeouts.

    No retry is performed for chat POSTs: retrying a long generation after an
    ambiguous network failure could duplicate model work and obscure failures.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: tuple[float, float] = (5.0, 180.0),
        num_ctx: int = 4096,
        keep_alive: str | int = os.getenv("OLLAMA_KEEP_ALIVE", "15m"),
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.keep_alive = keep_alive
        self.session = session or requests.Session()

    def list_models(self) -> list[dict[str, Any]]:
        payload = self._request_json("GET", "/api/tags")
        models = payload.get("models")
        if not isinstance(models, list):
            raise OllamaResponseInvalid("Ollama /api/tags response has no model list.")
        return [item for item in models if isinstance(item, dict)]

    def model_names(self) -> set[str]:
        return {str(item.get("name", "")) for item in self.list_models() if item.get("name")}

    def require_model(self, model: str) -> None:
        if model not in self.model_names():
            raise OllamaModelUnavailable(
                f"Required Ollama model is not registered: {model}. Check the local Ollama installation."
            )

    def show_model(self, model: str) -> dict[str, Any]:
        payload = self._request_json("POST", "/api/show", json={"name": model})
        if payload.get("error"):
            raise OllamaModelUnavailable(f"Ollama could not show model metadata for {model}.")
        return payload

    def chat(
        self,
        model: str,
        messages: Sequence[Mapping[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
        format: str | dict[str, Any] | None = None,
        verify_model: bool = True,
    ) -> OllamaChatResponse:
        if not model.strip():
            raise ValueError("model must be a non-empty string")
        if not messages:
            raise ValueError("messages must contain at least one message")
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        if temperature < 0 or temperature > 2:
            raise ValueError("temperature must be between 0 and 2")
        normalized_messages: list[dict[str, str]] = []
        allowed_roles = {"system", "user", "assistant", "tool"}
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if role not in allowed_roles or not isinstance(content, str):
                raise ValueError("each message requires a supported role and string content")
            normalized_messages.append({"role": role, "content": content})

        if verify_model:
            self.require_model(model)
        payload: dict[str, Any] = {
            "model": model,
            "messages": normalized_messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": temperature,
                "num_ctx": self.num_ctx,
                "num_predict": max_tokens,
            },
        }
        if format is not None:
            payload["format"] = format
        response = self._request_json("POST", "/api/chat", json=payload)
        if response.get("error"):
            raise OllamaRequestFailed(f"Ollama chat failed for configured model {model}.")
        message = response.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        actual_model = response.get("model", model)
        if not isinstance(content, str) or not content.strip():
            raise OllamaResponseInvalid("Ollama chat response did not contain message content.")
        return OllamaChatResponse(model=str(actual_model), content=content, raw=response)

    def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
                **kwargs,
            )
        except requests.Timeout as exc:
            raise OllamaUnavailable("The local Ollama request timed out.") from exc
        except requests.ConnectionError as exc:
            raise OllamaUnavailable("The local Ollama service is unavailable.") from exc
        except requests.RequestException as exc:
            raise OllamaRequestFailed("The local Ollama request failed.") from exc
        if response.status_code >= 400:
            if response.status_code == 404:
                raise OllamaModelUnavailable("Ollama returned not found; verify the configured model name.")
            raise OllamaRequestFailed(f"Ollama returned HTTP {response.status_code}.")
        try:
            payload = response.json()
        except (ValueError, requests.JSONDecodeError) as exc:
            raise OllamaResponseInvalid("Ollama returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise OllamaResponseInvalid("Ollama returned a JSON value with an unexpected shape.")
        return payload

    def close(self) -> None:
        self.session.close()
