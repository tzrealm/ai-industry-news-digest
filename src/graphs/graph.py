from langgraph.graph import END, StateGraph

from graphs.state import GlobalState, GraphInput, GraphOutput
from graphs.nodes.format_message_node import format_message_node
from graphs.nodes.search_news_node import search_news_node
from graphs.nodes.select_news_node import select_news_node
from graphs.nodes.send_to_email_node import send_to_email_node

# 创建状态图，指定工作流入参与出参结构
builder = StateGraph(
    GlobalState,
    input_schema=GraphInput,
    output_schema=GraphOutput,
)

# 添加节点
builder.add_node("search_news_node", search_news_node)
builder.add_node(
    "select_news_node",
    select_news_node,
    metadata={"type": "agent", "llm_cfg": "config/select_news_llm_cfg.json"},
)
builder.add_node("format_message_node", format_message_node)
builder.add_node("send_to_email_node", send_to_email_node)

# 设置入口点
builder.set_entry_point("search_news_node")

# 连接边（有向无环图）
builder.add_edge("search_news_node", "select_news_node")
builder.add_edge("select_news_node", "format_message_node")
builder.add_edge("format_message_node", "send_to_email_node")
builder.add_edge("send_to_email_node", END)

# 编译主图
main_graph = builder.compile()