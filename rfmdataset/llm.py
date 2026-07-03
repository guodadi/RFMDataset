"""Small OpenAI-compatible chat client used by the evaluation scripts."""

from __future__ import annotations

import concurrent.futures
import os
from dataclasses import dataclass
from typing import Iterable

from openai import OpenAI


@dataclass(frozen=True)
class ClientConfig:
    """Configuration for an OpenAI-compatible endpoint."""

    api_key_env: str
    base_url_env: str | None = None
    default_base_url: str | None = None
    model_aliases: dict[str, str] | None = None


CLIENT_CONFIGS: dict[str, ClientConfig] = {
    "openai": ClientConfig("OPENAI_API_KEY", "OPENAI_BASE_URL"),
    "deepseek": ClientConfig("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    "dashscope": ClientConfig("DASHSCOPE_API_KEY", "DASHSCOPE_BASE_URL"),
    "openai-compatible": ClientConfig("OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_BASE_URL"),
    "local": ClientConfig("LOCAL_API_KEY", "LOCAL_BASE_URL", "http://127.0.0.1:8000/v1"),
}


class MissingCredentialError(RuntimeError):
    pass


class GPTChatter:
    """Batch chat-completion helper.

    Credentials are read from environment variables only. This keeps the
    repository safe to publish and makes endpoints configurable by users.
    """

    def __init__(
        self,
        model_name: str,
        client: str = "openai",
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        max_workers: int = 8,
    ) -> None:
        if client not in CLIENT_CONFIGS:
            known = ", ".join(sorted(CLIENT_CONFIGS))
            raise ValueError(f"Unknown client '{client}'. Known clients: {known}")

        config = CLIENT_CONFIGS[client]
        self.model_name = (config.model_aliases or {}).get(model_name, model_name)
        self.max_workers = max_workers

        resolved_key = api_key or os.getenv(config.api_key_env)
        if not resolved_key:
            raise MissingCredentialError(
                f"Missing API key. Set {config.api_key_env} or pass api_key explicitly."
            )

        resolved_base_url = (
            base_url
            or (os.getenv(config.base_url_env) if config.base_url_env else None)
            or config.default_base_url
        )
        kwargs = {"api_key": resolved_key}
        if resolved_base_url:
            kwargs["base_url"] = resolved_base_url
        self.client = OpenAI(**kwargs)

    def get_llm_response(
        self,
        prompt_list: Iterable[str],
        *,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
        stream: bool = False,
    ) -> list[str]:
        prompts = list(prompt_list)
        responses: list[str | None] = [None] * len(prompts)

        def fetch(prompt: str, index: int) -> tuple[int, str]:
            kwargs = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
            }
            if temperature is not None:
                kwargs["temperature"] = temperature
            if max_new_tokens is not None:
                kwargs["max_tokens"] = max_new_tokens
            if timeout is not None:
                kwargs["timeout"] = timeout
            if stream:
                kwargs["stream"] = True

            try:
                result = self.client.chat.completions.create(**kwargs)
                if stream:
                    answer = ""
                    for chunk in result:
                        content = chunk.choices[0].delta.content
                        if content:
                            print(content, end="")
                            answer += content
                else:
                    answer = result.choices[0].message.content or ""
                return index, answer
            except Exception as exc:
                return index, f"Error: {exc}"

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(fetch, prompt, index): index
                for index, prompt in enumerate(prompts)
            }
            for future in concurrent.futures.as_completed(future_to_index):
                index, response = future.result()
                responses[index] = response

        return [response or "" for response in responses]


# Backward-compatible spelling used by the original research scripts.
GPT_Chatter = GPTChatter
