"""Small OpenAI-compatible chat client used by the evaluation scripts."""

from __future__ import annotations

import concurrent.futures
import os
from typing import Iterable

from openai import OpenAI


class MissingCredentialError(RuntimeError):
    pass


class GPTChatter:
    """Batch chat-completion helper.

    The repository does not ship endpoint presets. Users provide both the
    API key and the base URL through environment variables or constructor
    arguments, which keeps credentials and routing choices outside the code.
    """

    def __init__(
        self,
        model_name: str,
        *,
        api_key_env: str = "RFM_API_KEY",
        base_url_env: str = "RFM_BASE_URL",
        api_key: str | None = None,
        base_url: str | None = None,
        max_workers: int = 8,
    ) -> None:
        self.model_name = model_name
        self.max_workers = max_workers

        resolved_key = api_key or os.getenv(api_key_env)
        if not resolved_key:
            raise MissingCredentialError(
                f"Missing API key. Set {api_key_env} or pass api_key explicitly."
            )

        resolved_base_url = base_url or os.getenv(base_url_env)
        if not resolved_base_url:
            raise MissingCredentialError(
                f"Missing base URL. Set {base_url_env} or pass base_url explicitly."
            )

        self.client = OpenAI(api_key=resolved_key, base_url=resolved_base_url)

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
