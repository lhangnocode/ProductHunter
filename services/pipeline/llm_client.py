"""
LLM provider clients for product normalization.

The pipeline writes staging rows in llm_normalizer.py; this module owns only
provider-specific request/response handling.
"""
from __future__ import annotations

import json
from typing import Any, Protocol

import requests

from services.pipeline.config import (
    LITELLM_API_KEY,
    LITELLM_BASE_URL,
    LITELLM_PASSWORD,
    LITELLM_USERNAME,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MAX_OUTPUT_TOKENS,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
)
from services.pipeline.define.category import CATEGORIES
from services.pipeline.define.instruction import LLM_INSTRUCTION


class ProductNormalizerClient(Protocol):
    def normalize_batch(self, names: list[str]) -> list[dict[str, Any]]:
        """Return normalized result objects aligned with input names."""


NORMALIZATION_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "brand": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "model": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "manufacture_model_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "category": {"type": "string", "enum": CATEGORIES},
                    "specs": {
                        "anyOf": [
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "name": {"type": "string"},
                                        "value": {"type": "string"},
                                    },
                                    "required": ["name", "value"],
                                },
                            },
                            {"type": "null"},
                        ]
                    },
                },
                "required": ["brand", "model", "manufacture_model_id", "category", "specs"],
            },
        }
    },
    "required": ["items"],
}


class OpenAIProductNormalizerClient:
    def __init__(
        self,
        api_key: str = OPENAI_API_KEY,
        base_url: str = OPENAI_BASE_URL,
        model: str = OPENAI_MODEL,
        timeout_seconds: int = OPENAI_TIMEOUT_SECONDS,
        max_output_tokens: int = OPENAI_MAX_OUTPUT_TOKENS,
    ) -> None:
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set in services/.env or environment.")
        from openai import OpenAI

        client_kwargs: dict[str, Any] = {"api_key": api_key, "timeout": timeout_seconds}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = OpenAI(**client_kwargs)
        self._model = model
        self._max_output_tokens = max_output_tokens

    def normalize_batch(self, names: list[str]) -> list[dict[str, Any]]:
        if not names:
            return []

        response = self._client.responses.create(
            model=self._model,
            input=[
                {
                    "role": "system",
                    "content": (
                        f"{LLM_INSTRUCTION}\n\n"
                        "For this API call, return an object with exactly one key, "
                        '"items", whose value is the JSON array described above.'
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(names, ensure_ascii=False),
                },
            ],
            max_output_tokens=self._max_output_tokens,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "product_normalization_batch",
                    "strict": True,
                    "schema": NORMALIZATION_RESPONSE_SCHEMA,
                }
            },
        )

        if getattr(response, "status", None) == "incomplete":
            reason = getattr(getattr(response, "incomplete_details", None), "reason", None)
            raise RuntimeError(f"OpenAI response incomplete: {reason or 'unknown reason'}")

        output_text = response.output_text
        if not output_text:
            raise ValueError("OpenAI response did not include output_text.")

        payload = json.loads(output_text)
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError(f"Expected response.items list, got {type(items).__name__}")
        return items


class LiteRTLMProductNormalizerClient:
    def __init__(self) -> None:
        self._headers = self._get_auth_headers()

    def normalize_batch(self, names: list[str]) -> list[dict[str, Any]]:
        if not names:
            return []

        numbered = "\n".join(f"{i + 1}. {name}" for i, name in enumerate(names))
        resp = requests.post(
            f"{LITELLM_BASE_URL}/api/conversations/data-normalizer/messages",
            json={"message": numbered},
            headers=self._headers,
            timeout=500,
        )
        resp.raise_for_status()
        reply = resp.json().get("reply", "")
        clean = self._strip_markdown_json(reply)
        parsed = json.loads(clean)
        if not isinstance(parsed, list):
            raise ValueError(f"Expected JSON array, got {type(parsed).__name__}: {clean[:200]}")
        return parsed

    def _get_auth_headers(self) -> dict[str, str]:
        if LITELLM_API_KEY:
            return {"Authorization": f"Bearer {LITELLM_API_KEY}"}
        if LITELLM_USERNAME and LITELLM_PASSWORD:
            token = self._jwt_login()
            return {"Authorization": f"Bearer {token}"}
        raise EnvironmentError(
            "No LiteRTLM credentials. Set LITELLM_API_KEY or "
            "LITELLM_USERNAME + LITELLM_PASSWORD in services/.env."
        )

    def _jwt_login(self) -> str:
        resp = requests.post(
            f"{LITELLM_BASE_URL}/api/auth/login",
            json={"username": LITELLM_USERNAME, "password": LITELLM_PASSWORD},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"LiteRTLM login failed: {data.get('error')}")
        return data["accessToken"]

    @staticmethod
    def _strip_markdown_json(text: str) -> str:
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            end = -1 if lines and lines[-1].strip() == "```" else len(lines)
            clean = "\n".join(lines[1:end])
        return clean


def create_product_normalizer_client() -> ProductNormalizerClient:
    if LLM_PROVIDER == "openai":
        return OpenAIProductNormalizerClient()
    if LLM_PROVIDER in {"litertlm", "lite_rtlm", "lite-rtlm"}:
        return LiteRTLMProductNormalizerClient()
    raise ValueError(f"Unsupported LLM_PROVIDER={LLM_PROVIDER!r}. Use 'openai' or 'litertlm'.")
