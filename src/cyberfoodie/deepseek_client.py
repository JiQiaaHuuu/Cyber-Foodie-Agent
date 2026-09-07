from __future__ import annotations

import json
import urllib.request
from typing import Dict, List

from .config import DEEPSEEK_ENDPOINT, DEEPSEEK_MODEL, load_api_key


def call_deepseek(messages: List[Dict[str, str]], temperature: float = 0.8) -> str:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("DeepSeek API Key 未配置")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 700,
    }
    request = urllib.request.Request(
        DEEPSEEK_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"].strip()
