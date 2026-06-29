# ReadFlow

ReadFlow 是一个结合 AI 与 RAG（检索增强生成）技术的辅助阅读工具。用户通过网页上传 PDF 文档，系统对文档进行解析、切分、向量化，并支持基于文档内容的检索问答。

## Tech Stack

- **后端**: Python / FastAPI（待初始化）
- **前端**: 网页端（具体框架待确定）
- **核心能力**:
  - PDF 上传与解析
  - 文本切分与向量化（RAG）
  - 检索问答（Retriever + LLM）

## Harness

This project uses the Long-Running Agent Harness v3.6.0.

- Feature tracking: `.harness/features.json`
- Context and decisions: `.harness/context_summary.md`（每次会话开始时阅读）
- Progress handoff: `.harness/claude-progress.txt`
- Build/test: `.harness/init.sh`
- Quality gates: `.claude/hooks/`（TaskCompleted、TeammateIdle、PostCompact、PreToolUse scope/git identity）

## Git Identity

This project uses: xliCoder <primeshift@163.com> with SSH host github.com.
Always verify identity before push/pull/clone operations.
