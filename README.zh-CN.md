# AI 行业新闻日报

[English](README.md)

一个基于 [Coze Vibe Coding](https://code.coze.cn) 的项目：通过定时触发的 LangGraph 工作流，抓取 AI 行业最新新闻，由大语言模型精选出 3 条最有价值的内容，整理成易读的日报文本，并通过邮件推送。

**在线预览：** https://code.coze.cn/p/7689841331820036122/preview

![项目预览](assets/preview.png)

## 工作流程

主图 `src/graphs/graph.py` 是一个线性流程：

```
search_news_node → select_news_node → format_message_node → send_to_email_node → END
```

| 节点名 | 文件位置 | 类型 | 功能描述 |
|-------|---------|------|---------|
| `search_news_node` | `src/graphs/nodes/search_news_node.py` | task | 通过 Web 搜索抓取指定主题的最新新闻 |
| `select_news_node` | `src/graphs/nodes/select_news_node.py` | agent | LLM 精选 3 条关键新闻并结构化输出（配置：`config/select_news_llm_cfg.json`） |
| `format_message_node` | `src/graphs/nodes/format_message_node.py` | task | 将精选新闻整理为日报文本 |
| `send_to_email_node` | `src/graphs/nodes/send_to_email_node.py` | task | 通过 SMTP 将日报发送至邮箱 |

每日 8 点定时触发与最终投递由外层 Coze 平台调度/集成负责，本工作流只负责生成 `digest_message` 并通过 SMTP 邮件发送。

更完整的架构说明见 `CLAUDE.md`，平台生成的节点清单见 `AGENTS.md`。

## 快速开始

需要 Python >=3.12 与 [`uv`](https://docs.astral.sh/uv/)。

```bash
# 安装依赖
bash scripts/setup.sh

# 本地运行完整工作流
bash scripts/local_run.sh -m flow

# 运行单个节点
bash scripts/local_run.sh -m node -n search_news_node -i '{"topic": "AI"}'

# 启动 HTTP 服务
bash scripts/http_run.sh -p 5000
```

## 本地运行验证

2026-09-27 在 macOS（`uv` 管理的虚拟环境）上对本工作流进行了本地冒烟测试：

- **安装依赖** — `bash scripts/setup.sh` 执行成功。注意：`pycairo`、`dbus-python`、`PyGObject` 是 Coze devbox 模板自带的依赖，`src/` 中并未实际引用，但在本地构建时仍需要系统库支持；macOS 上需先安装：`brew install cairo pkg-config dbus glib gobject-introspection`。
- **应用启动 / 主图装配** — 执行 `COZE_WORKSPACE_PATH="$(pwd)" .venv/bin/python src/main.py -m flow -i '{"topic": "AI"}'` 可正常启动：日志、APScheduler、LangGraph 主图均初始化成功，无导入或配置错误。
- **纯逻辑节点** — `format_message_node` 无需任何外部服务即可完整运行，例如：
  ```bash
  COZE_WORKSPACE_PATH="$(pwd)" .venv/bin/python src/main.py -m node -n format_message_node \
    -i '{"top_news": [{"title": "Test AI News", "url": "https://example.com", "summary": "A short summary."}]}'
  ```
  输出：
  ```json
  {
    "digest_message": "AI 行业要闻早报 · 2026-09-27\n\n1. Test AI News\n   A short summary.\n   原文链接: https://example.com"
  }
  ```
- **依赖平台集成的节点**（`search_news_node`、`select_news_node`、`send_to_email_node`）**无法在 Coze 平台之外运行**：它们调用 `coze_coding_dev_sdk.SearchClient`/`LLMClient` 及 `coze_workload_identity.Client`，需要 Coze 平台签发的鉴权 token。本地运行完整流程会在 `search_news_node` 处报错：
  ```
  coze_coding_dev_sdk.core.exceptions.APIError: Search failed: {'Code': '190000007', 'Message': '... token validation failed: failed to parse token: token contains an invalid number of segments'}
  ```
  这是预期行为——完整的端到端运行（搜索 → LLM 精选 → 邮件发送）需要在已配置好这些集成凭据的 Coze devbox/预览环境中进行。

## 项目结构

```
src/
  main.py              # FastAPI 入口（HTTP 服务 + 命令行运行）
  graphs/               # LangGraph 状态、节点与主图定义
  storage/              # Postgres / checkpointer / S3 存储辅助模块
config/                 # 各节点的 LLM 配置
scripts/                # setup / run / pack 脚本
```
