from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import SearchClient

from graphs.state import SearchNewsInput, SearchNewsOutput


def search_news_node(
    state: SearchNewsInput,
    config: RunnableConfig,
    runtime: Runtime[Context],
) -> SearchNewsOutput:
    """
    title: 搜索AI行业新闻
    desc: 通过 Web 搜索抓取指定主题的最新新闻，返回原始新闻列表
    integrations: Web Search
    """
    ctx = runtime.context
    client = SearchClient(ctx=ctx)

    query = f"{state.topic} 最新新闻"
    response = client.web_search(query=query, count=10, need_summary=True)

    news_list: list = []
    web_items = response.web_items
    if not web_items:
        return SearchNewsOutput(raw_news=[])

    for item in web_items:
        news_list.append(
            {
                "title": (item.title or "") if hasattr(item, "title") else "",
                "url": (item.url or "") if hasattr(item, "url") else "",
                "snippet": (item.snippet or "") if hasattr(item, "snippet") else "",
                "site": (item.site_name or "") if hasattr(item, "site_name") else "",
                "publish_time": (item.publish_time or "") if hasattr(item, "publish_time") else "",
                "summary": (item.summary or "") if hasattr(item, "summary") else "",
            }
        )

    return SearchNewsOutput(raw_news=news_list)