---
name: langgraph-v1
description: Use when writing or refactoring Python agent code to be valid for LangGraph v1 + LangChain v1 (latest stable): migrate off langgraph.prebuilt.create_react_agent and other deprecated LangGraph prebuilts; use langchain.agents.create_agent + middleware; update prompts/system_prompt, state schema (TypedDict-only), tools list (no ToolNode), structured output strategies, streaming node names, runtime context injection, and message content_blocks/output_version changes.
---

# LangGraph v1 + LangChain v1: delta-only cheat sheet (write valid v1 code)

## 1) Prebuilt agent: `create_react_agent` → `create_agent`

- Replace:
  - `from langgraph.prebuilt import create_react_agent`
- With:
  - `from langchain.agents import create_agent`

## 2) Prompt param rename + type change

- Replace `prompt=...` with `system_prompt=...`
- Pass `system_prompt` as a **string** (not `SystemMessage`).

## 3) Hooks replaced by middleware

- Replace:
  - `pre_model_hook=...` → middleware implementing `before_model(...)`
  - `post_model_hook=...` → middleware implementing `after_model(...)`
- Dynamic system prompt:
  - Use `@dynamic_prompt` middleware (`from langchain.agents.middleware import dynamic_prompt, ModelRequest`).

## 4) State schema restrictions (v1 agents)

- Use `TypedDict` state only.
- Prefer inheriting from `langchain.agents.AgentState` for agent state.
- Do **not** use pydantic/dataclass state schemas for `create_agent`.

## 5) Runtime context injection

- Prefer:
  - `agent.invoke(..., context=Context(...))`
  - `agent.stream(..., context=Context(...))`
- The old `config["configurable"]` pattern may still work for backward compatibility, but don’t use it in new v1 code unless required.

## 6) Tools input shape

- Pass `tools=[...]` as a list of:
  - `@tool` functions / `BaseTool` instances
  - plain callables with type hints + docstring
  - provider tool dicts (built-in provider tools)
- Do **not** pass `ToolNode(...)` to `create_agent`.

## 7) Tool error handling

- Replace ToolNode-style `handle_tool_errors=...` with middleware implementing `wrap_tool_call(...)` (or the `@wrap_tool_call` helper).

## 8) Model selection + “pre-bound model” caveat

- Dynamic model selection: implement via middleware (`wrap_model_call(...)` and request overrides).
- Don’t pass a pre-bound model (e.g., `ChatOpenAI().bind_tools(...)`) into `create_agent` when structured output is in play; prefer passing the model id / base model and supply `tools=` to `create_agent`.

## 9) Structured output changes

- Prompted output via `response_format=("please ...", Schema)` is removed.
- Use:
  - `from langchain.agents.structured_output import ToolStrategy, ProviderStrategy`
  - `response_format=ToolStrategy(Schema)` or `ProviderStrategy(Schema)`

## 10) Streaming node name rename

- When streaming events, expect node name `"model"` (not `"agent"`).

## 11) Messages: standard content blocks

- Prefer `message.content_blocks` for provider-agnostic structured content.
- If you need standardized blocks serialized into `message.content`, opt in via:
  - `LC_OUTPUT_VERSION=v1` or model init `output_version="v1"`.

## 12) Package / imports changed in LangChain v1

- The top-level `langchain` namespace is slim; common v1 modules:
  - `langchain.agents`, `langchain.messages`, `langchain.tools`, `langchain.chat_models`, `langchain.embeddings`
- If you need legacy chains/retrievers/indexing/hub/community re-exports, use `langchain-classic` and update imports accordingly.

## 13) Other breaking changes worth enforcing in generated code

- Assume Python **3.10+**.
- Chat model invocation return type is now `AIMessage` (not `BaseMessage`).
- `.text()` becomes `.text` (property); avoid calling it.
