import datetime

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import FormatMessageInput, FormatMessageOutput


def format_message_node(
    state: FormatMessageInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> FormatMessageOutput:
    """
    title: 格式化新闻日报
    desc: 将精选出的关键新闻整理成易读的 AI 行业要闻日报文本
    """
    ctx = runtime.context  # noqa: F841 (保留运行时上下文)

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    lines: list = [f"AI 行业要闻早报 · {today}", ""]

    news = state.top_news if isinstance(state.top_news, list) else []
    if not news:
        lines.append("今日暂无匹配的 AI 行业新闻。")
    else:
        for i, item in enumerate(news, 1):
            title = item.get("title", "") if isinstance(item, dict) else ""
            summary = item.get("summary", "") if isinstance(item, dict) else ""
            url = item.get("url", "") if isinstance(item, dict) else ""
            lines.append(f"{i}. {title}")
            if summary:
                lines.append(f"   {summary}")
            if url:
                lines.append(f"   原文链接: {url}")
            lines.append("")

    digest = "\n".join(lines).strip()
    return FormatMessageOutput(digest_message=digest)