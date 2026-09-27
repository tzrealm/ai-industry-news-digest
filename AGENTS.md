## 项目概述
- **名称**: AI 行业新闻推送工作流
- **功能**: 定时抓取 AI 行业最新新闻，通过大语言模型精选 3 条关键内容，生成易读日报供推送

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| search_news_node | `src/graphs/nodes/search_news_node.py` | task | Web搜索抓取指定主题最新新闻 | - | - |
| select_news_node | `src/graphs/nodes/select_news_node.py` | agent | LLM精选3条关键新闻并结构化输出 | - | `config/select_news_llm_cfg.json` |
| format_message_node | `src/graphs/nodes/format_message_node.py` | task | 将精选新闻整理为日报文本 | - | - |
| send_to_email_node | `src/graphs/nodes/send_to_email_node.py` | task | 通过 SMTP 将日报发送至用户邮箱 | - | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 技能使用
- 节点 `search_news_node` 使用 Web Search（`coze_coding_dev_sdk.SearchClient`）
- 节点 `select_news_node` 使用大语言模型（`coze_coding_dev_sdk.LLMClient`，模型 `doubao-seed-2-0-lite-260215`）

## 备注
- 主图在 `src/graphs/graph.py` 编译为 `main_graph`，线性流程：search → select → format → send_email → END
- 每日 8 点定时触发与最终投递由外层调度/平台负责，本工作流将日报 `digest_message` 通过 SMTP 邮件发送至集成账号邮箱