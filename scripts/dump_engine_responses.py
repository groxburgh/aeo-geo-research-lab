"""
Diagnostic script — dumps one raw API response per engine to scripts/raw_responses/.
Not a permanent test harness. Run once to capture ground truth response shapes.

Usage:
    python scripts/dump_engine_responses.py
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv(".env")

OUT = Path(__file__).parent / "raw_responses"
OUT.mkdir(exist_ok=True)

QUERY = "What is generative engine optimization?"


def _serialize(obj):
    """Best-effort serializer for SDK response objects."""
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------
def dump_openai():
    import openai
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[openai] SKIP — OPENAI_API_KEY not set")
        return

    print("[openai] Calling API...")
    client = openai.OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search_preview"}],
        input=QUERY,
        max_output_tokens=500,
    )

    raw = _serialize(response)
    dest = OUT / "openai.json"
    dest.write_text(json.dumps(raw, indent=2, default=str))
    print(f"[openai] Written to {dest}")

    # Surface citation-relevant paths
    print("[openai] Output item types:", [getattr(i, "type", i.get("type") if isinstance(i, dict) else "?") for i in response.output])
    for item in response.output:
        item_type = getattr(item, "type", None)
        print(f"[openai]   item.type={item_type}")
        if item_type == "web_search_call":
            results = getattr(item, "results", None)
            print(f"[openai]     .results = {results!r}")
        if item_type == "message":
            for part in getattr(item, "content", []):
                part_type = getattr(part, "type", None)
                print(f"[openai]     content part.type={part_type}")
                annotations = getattr(part, "annotations", None)
                if annotations:
                    print(f"[openai]       annotations: {annotations}")


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------
def dump_anthropic():
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[anthropic] SKIP — ANTHROPIC_API_KEY not set")
        return

    print("[anthropic] Calling API...")
    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 1}],
            messages=[{"role": "user", "content": QUERY}],
            max_tokens=500,
        )

        raw = _serialize(response)
        dest = OUT / "anthropic.json"
        dest.write_text(json.dumps(raw, indent=2, default=str))
        print(f"[anthropic] Written to {dest}")

        print("[anthropic] Content block types:", [getattr(b, "type", "?") for b in response.content])
        for block in response.content:
            block_type = getattr(block, "type", None)
            print(f"[anthropic]   block.type={block_type}")
            if block_type == "text":
                print(f"[anthropic]     text[:100]={block.text[:100]!r}")
            else:
                print(f"[anthropic]     full block: {_serialize(block)}")

    except Exception:
        tb = traceback.format_exc()
        print(f"[anthropic] ERROR:\n{tb}")
        error_payload = {"traceback": tb}
        dest = OUT / "anthropic_error.json"
        dest.write_text(json.dumps(error_payload, indent=2))
        print(f"[anthropic] Error payload written to {dest}")


# ---------------------------------------------------------------------------
# Perplexity (sanity check only — known working)
# ---------------------------------------------------------------------------
def dump_perplexity():
    import requests
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("[perplexity] SKIP — PERPLEXITY_API_KEY not set")
        return

    print("[perplexity] Calling API...")
    resp = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "sonar", "messages": [{"role": "user", "content": QUERY}]},
        timeout=30,
    )
    resp.raise_for_status()
    raw = resp.json()
    dest = OUT / "perplexity.json"
    dest.write_text(json.dumps(raw, indent=2))
    print(f"[perplexity] Written to {dest}")
    print(f"[perplexity] citations field: {raw.get('citations', 'NOT PRESENT')[:3]}")


if __name__ == "__main__":
    dump_openai()
    print()
    dump_anthropic()
    print()
    dump_perplexity()
    print("\nDone. Check scripts/raw_responses/ for full output.")
