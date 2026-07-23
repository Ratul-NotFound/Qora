"""
LLM Utilities — Shared retry logic, JSON extraction, and multi-model fallback chain for all agents.
"""
import json
import re
import asyncio
from typing import Optional, List

# List of robust fallback models on OpenRouter (tried automatically if primary model fails or 404s)
FREE_FALLBACK_MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "openrouter/free",
]


async def llm_call_with_retry(
    client,
    model: str,
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    max_retries: int = 2,
    fallback_model: Optional[str] = None,
) -> Optional[str]:
    """Call LLM with exponential backoff retry and automatic multi-model failover."""
    
    # Candidate models to try in sequence
    candidates = [model]
    if fallback_model and fallback_model not in candidates:
        candidates.append(fallback_model)
    for fb in FREE_FALLBACK_MODELS:
        if fb not in candidates:
            candidates.append(fb)

    last_error = None

    for target_model in candidates:
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as e:
                last_error = e
                err_str = str(e)
                print(f"[LLM] Model '{target_model}' attempt {attempt + 1}/{max_retries} failed: {e}")
                
                # If 404, 400, or 429 (rate limited / offline model), switch to next candidate model
                if "404" in err_str or "400" in err_str or "429" in err_str or "unavailable" in err_str.lower() or "rate" in err_str.lower():
                    print(f"[LLM] Model '{target_model}' rate-limited or offline ({e}). Switching to next candidate model...")
                    break
                
                wait_time = (2 ** attempt) + 0.5
                await asyncio.sleep(wait_time)

    print(f"[LLM] All candidate models exhausted. Last error: {last_error}")
    return None


def extract_json(raw: str) -> Optional[any]:
    """Robustly extract JSON from LLM output, handling markdown fences and extra text."""
    if not raw:
        return None

    # Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array
    match = re.search(r'\[[\s\S]*\]', cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Try to find JSON object
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None
