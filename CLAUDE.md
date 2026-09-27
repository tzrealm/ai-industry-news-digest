# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is a **Coze Vibe Coding** project: a LangGraph workflow, generated and hosted by the Coze coding platform, that produces a daily "AI industry news digest" and emails it to a user. See `AGENTS.md` for the platform-generated node manifest (node names, files, types, config).

The workflow (`src/graphs/graph.py`, compiled as `main_graph`) is a linear, non-branching graph:

```
search_news_node -> select_news_node -> format_message_node -> send_to_email_node -> END
```

- `search_news_node` — calls `coze_coding_dev_sdk.SearchClient.web_search` to fetch raw candidate news for `topic`.
- `select_news_node` — an **agent node**: loads its LLM config from `config/select_news_llm_cfg.json` (path resolved relative to `COZE_WORKSPACE_PATH`, injected into node metadata as `llm_cfg`), renders the `up` (user prompt) Jinja2 template with `raw_news`, calls `coze_coding_dev_sdk.LLMClient`, and parses the model's JSON reply into up to 3 `top_news` items. `_safe_json_loads` in this file defensively extracts JSON even if the model wraps it in markdown fences.
- `format_message_node` — pure formatting, no I/O; turns `top_news` into the final digest text.
- `send_to_email_node` — fetches SMTP credentials via `coze_workload_identity.Client().get_integration_credential("integration-email-imap-smtp")` and sends a plain-text email over SSL.

State flows through Pydantic models in `src/graphs/state.py` (`GlobalState`/`GraphInput`/`GraphOutput` plus one Input/Output pair per node). When adding or changing a node's fields, update the corresponding pair here — the graph and `main.py`'s single-node runner both introspect these schemas.

`src/main.py` is the FastAPI entrypoint used both for local CLI runs and HTTP serving. It wraps the compiled graph with `coze_coding_utils` helpers for logging, streaming (SSE), async task execution with a Postgres-backed checkpointer, run cancellation, and an OpenAI-compatible `/v1/chat/completions` shim. Key routes: `/run`, `/stream_run`, `/async_run` + `/task/{id}`, `/cancel/{run_id}`, `/node_run/{node_id}`, `/graph_parameter`, `/health`.

The `storage/` package provides the Postgres session/engine (`storage/database/db.py`), the LangGraph checkpointer (`storage/memory/memory_saver.py`), and S3 access (`storage/s3/s3_storage.py`) — used only when running through the platform's async-task/checkpointing path, not by the simple linear digest flow itself.

## Commands

Dependencies are managed with `uv` (see `pyproject.toml`; Python >=3.12). Install/sync:

```bash
bash scripts/setup.sh          # uv sync into .venv (devbox) or --target $PIP_TARGET (deploy)
```

Run the workflow locally (loads env vars via `scripts/load_env.sh` first):

```bash
bash scripts/local_run.sh -m flow                              # run the full graph, default input
bash scripts/local_run.sh -m flow -i '{"topic": "..."}'        # run the full graph with custom input
bash scripts/local_run.sh -m node -n search_news_node -i '{"topic": "..."}'   # run a single node
```

Start the HTTP server:

```bash
bash scripts/http_run.sh -p 5000        # or: bash scripts/local_run.sh -m http -p 5000
```

Lock dependencies (used by the platform's pack step): `bash scripts/pack.sh` (runs `uv lock`).

Tests: `pytest` (config in `pyproject.toml`; `pythonpath = ["src"]`, so imports in tests use the same `graphs.*`/`storage.*` module paths as the app code). No test files exist in the repo yet.

## Notes specific to this codebase

- Node functions follow a fixed LangGraph signature: `(state: <NodeInput>, config: RunnableConfig, runtime: Runtime[Context]) -> <NodeOutput>`. The docstring on each node (`title`/`desc`/`integrations`) is read by the Coze platform tooling, not just documentation — keep it in sync with `AGENTS.md`'s node table when editing a node.
- `select_news_node`'s LLM config file path is resolved as `os.path.join(os.getenv("COZE_WORKSPACE_PATH", ""), config["metadata"]["llm_cfg"])`, so `COZE_WORKSPACE_PATH` must be set (handled by `scripts/local_run.sh` → `load_env.sh` locally).
- Email sending in `send_to_email_node` always sends to the configured integration account itself (the digest recipient is the integrated mailbox owner), not an arbitrary address from the workflow input.
