"""Provider-agnostic LLM wrapper: one function, swappable backends, with retries
and automatic cross-provider fallback.

Everything above this file works with plain dicts and never imports a provider
SDK, so switching Groq <-> Gemini is a config change, not a code change.

Resilience (this is the only place failures are handled):
  1. Try the primary provider (env LLM_PROVIDER, default "groq").
  2. On a transient error (rate limit / timeout / overload), retry with backoff.
  3. If the primary still fails, FALL BACK to the other provider when its key is
     set. Only if every available provider fails do we raise LLMError.

Keys: set GROQ_API_KEY and/or GEMINI_API_KEY in .env. A provider with no key is
simply skipped, so the app runs with whichever key(s) you have.
"""

from __future__ import annotations

import json
import os
import re
import time

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
PRIMARY_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

MAX_RETRIES = 3           # per provider, for transient errors
BACKOFF_SECONDS = 2.0     # 2s, 4s, 6s ...
REQUEST_TIMEOUT = 60


class LLMError(RuntimeError):
    """Raised only when every available provider has failed."""


def _is_transient(exc: Exception) -> bool:
    """Rate limits, timeouts and overloads are worth retrying / failing over."""
    s = str(exc).lower()
    return any(k in s for k in ("429", "rate", "timeout", "timed out", "overload",
                                "503", "500", "unavailable"))


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a reply, tolerating ``` fences and any
    surrounding reasoning text (some models emit both)."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"no JSON object in reply: {text[:200]!r}")


# --- provider callers: each takes a prompt, returns raw text, raises on error ---

def _call_groq(prompt: str, model: str | None, temperature: float) -> str:
    from groq import Groq  # imported lazily so Gemini-only users don't need it

    client = Groq(api_key=os.environ["GROQ_API_KEY"], timeout=REQUEST_TIMEOUT)
    resp = client.chat.completions.create(
        model=model or GROQ_MODEL,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_gemini(prompt: str, model: str | None, temperature: float) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    gen_model = genai.GenerativeModel(model or GEMINI_MODEL)
    response = gen_model.generate_content(
        prompt,
        generation_config={"temperature": temperature,
                           "response_mime_type": "application/json"},
        request_options={"timeout": REQUEST_TIMEOUT},
    )
    return response.text


_CALLERS = {"groq": _call_groq, "gemini": _call_gemini}
_KEY_ENV = {"groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY"}


def _providers_in_order() -> list[str]:
    """Primary first, then the other — keeping only providers that have a key."""
    order = [PRIMARY_PROVIDER] + [p for p in _CALLERS if p != PRIMARY_PROVIDER]
    return [p for p in order if os.getenv(_KEY_ENV[p])]


def call_json(prompt: str, *, model: str | None = None, temperature: float = 0.4) -> dict:
    """Send `prompt`, return a parsed JSON object. Tries each available provider
    with retries; raises LLMError only if all of them fail."""
    providers = _providers_in_order()
    if not providers:
        raise LLMError("No LLM key set. Add GROQ_API_KEY or GEMINI_API_KEY to .env.")

    errors: list[str] = []
    for provider in providers:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return _extract_json(_CALLERS[provider](prompt, model, temperature))
            except Exception as exc:  # noqa: BLE001 - we normalize everything to LLMError
                if _is_transient(exc) and attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_SECONDS * attempt)
                    continue
                errors.append(f"{provider}: {exc}")
                break  # non-transient or out of retries -> try the next provider
    raise LLMError("All LLM providers failed -> " + " | ".join(errors))
