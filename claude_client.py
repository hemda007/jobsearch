"""Shared Anthropic API client with retry logic and JSON extraction."""

import json
import time

import anthropic

import config

# Singleton client instance
_client = None


def get_client() -> anthropic.Anthropic:
    """Return a shared Anthropic client instance."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def extract_json(text: str) -> dict:
    """Extract JSON from a Claude response, handling markdown code blocks."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


def call_claude(prompt: str, max_tokens: int = 1024) -> str:
    """
    Call Claude API with automatic retry on failure.

    Returns the raw response text (caller handles parsing).
    Retries once with 5s backoff on API errors.
    """
    client = get_client()

    try:
        response = client.messages.create(
            model=config.MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except anthropic.APIError as e:
        print(f"  Claude API error, retrying in 5s: {e}")
        time.sleep(5)
        response = client.messages.create(
            model=config.MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()


def call_claude_json(prompt: str, max_tokens: int = 1024) -> dict:
    """Call Claude API and parse the response as JSON."""
    text = call_claude(prompt, max_tokens)
    return extract_json(text)
