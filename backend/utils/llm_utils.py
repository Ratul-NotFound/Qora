"""
LLM Utilities — Shared retry logic, JSON extraction, and model fallback for all agents.
"""
import json
import re
import asyncio
from typing import Optional


async def llm_call_with_retry(
    client,
    model: str,
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    max_retries: int = 3,
    fallback_model: Optional[str] = None,
) -> Optional[str]:
    """Call LLM with exponential backoff retry and optional model fallback."""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
        except Exception as e:
            last_error = e
            wait_time = (2 ** attempt) + 0.5
            print(f"[LLM] Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)

    # Try fallback model if primary exhausted
    if fallback_model and fallback_model != model:
        print(f"[LLM] Primary model failed. Trying fallback: {fallback_model}")
        try:
            response = await client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
        except Exception as e:
            print(f"[LLM] Fallback model also failed: {e}")

    print(f"[LLM] All retries exhausted. Last error: {last_error}")
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
