"""DeepSeek LLM 客户端 —— 认知模块和 Reply LLM 共用"""
import json
from openai import OpenAI
from src.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    return _client


async def call_json(prompt: str, json_schema_hint: str = "") -> dict:
    """调用认知模块 —— 强制 JSON 输出"""
    system_msg = (
        "You are a cognitive module in a virtual character system. "
        "You MUST output valid JSON. "
        + json_schema_hint
    )
    client = get_client()
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"{prompt}\n\nOutput valid JSON only."},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=2000,
    )
    raw = resp.choices[0].message.content or "{}"
    # 清理可能的 markdown 包裹
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("\n```", 1)[0]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"parse_error": True, "raw": raw}


async def call_text(prompt: str) -> str:
    """调用 Reply LLM —— 自然语言输出，不做 JSON 约束"""
    client = get_client()
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=500,
    )
    return resp.choices[0].message.content or "（沉默）"
