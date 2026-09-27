import json
import os
import re

from jinja2 import Template
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import LLMClient

from graphs.state import SelectNewsInput, SelectNewsOutput


def _safe_json_loads(text: str):
    """从模型返回内容中稳健地提取 JSON（兼容 Markdown 代码块包裹）。"""
    import json as _json

    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    for start_char, end_char in (("[", "]"), ("{", "}")):
        start = cleaned.find(start_char)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(cleaned)):
            if cleaned[i] == start_char:
                depth += 1
            elif cleaned[i] == end_char:
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start : i + 1]
                    try:
                        return _json.loads(candidate)
                    except Exception:
                        break
    return None


def _extract_content(resp_content) -> str:
    """安全提取 AIMessage.content 中的文本内容。"""
    if isinstance(resp_content, str):
        return resp_content
    if isinstance(resp_content, list):
        parts: list = []
        for item in resp_content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
        return "".join(parts)
    return str(resp_content)


def _normalize_top_news(data) -> list:
    """把模型返回的 JSON 规范化为 [{title,url,summary}] 列表，最多3条。"""
    top_news: list = []
    if data is None:
        return top_news

    if isinstance(data, dict):
        items = (
            data.get("top_news")
            or data.get("news")
            or data.get("items")
            or data.get("result")
            or []
        )
    else:
        items = data

    if not isinstance(items, list):
        items = []

    for it in items:
        if not isinstance(it, dict):
            continue
        title = str(it.get("title", "") or "")
        url = str(it.get("url", "") or "")
        summary = str(
            it.get("summary")
            or it.get("reason")
            or it.get("snippet")
            or ""
        )
        if not title:
            continue
        top_news.append({"title": title, "url": url, "summary": summary})
    return top_news[:3]


def select_news_node(
    state: SelectNewsInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> SelectNewsOutput:
    """
    title: 智能精选新闻
    desc: 使用大语言模型从候选新闻中挑选出 3 条最具价值的关键新闻，并输出结构化结果
    integrations: 大语言模型
    """
    ctx = runtime.context

    cfg_file = os.path.join(
        os.getenv("COZE_WORKSPACE_PATH", ""), config["metadata"]["llm_cfg"]
    )
    with open(cfg_file, "r", encoding="utf-8") as fd:
        _cfg = json.load(fd)

    llm_config = _cfg.get("config", {}) or {}
    sp = _cfg.get("sp", "")
    up = _cfg.get("up", "")

    up_tpl = Template(up)
    user_prompt = up_tpl.render(
        {"raw_news": json.dumps(state.raw_news, ensure_ascii=False)}
    )

    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=user_prompt),
    ]

    client = LLMClient(ctx=ctx)
    resp = client.invoke(
        messages=messages,
        model=llm_config.get("model"),
        temperature=llm_config.get("temperature", 0.3),
        max_completion_tokens=llm_config.get("max_completion_tokens", 2000),
        thinking=llm_config.get("thinking", "disabled"),
    )

    text = _extract_content(resp.content)
    data = _safe_json_loads(text)
    top_news = _normalize_top_news(data)

    return SelectNewsOutput(top_news=top_news)