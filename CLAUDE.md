
## 1. 项目概述

ReadFlow 是一个**流式阅读记忆体（Reading Memory System）**——不是帮你读书的 AI，而是陪你读书的记忆体。它跟随用户的阅读节奏，动态管理记忆层，支持发散式头脑风暴。

**核心特性**：
- 📚 支持 EPUB/PDF/Markdown 书籍阅读，按章节动态向量化
- 🌐 支持网页内容捕获（含认证穿透：知识星球、公众号等）
- 🧠 三层记忆架构：L1 感知层（热向量）、L2 笔记层（事实提取）、L3 知识层（概念图谱）
- 🤖 内置 One API，用户可自由配置 OpenAI/DeepSeek/Claude/本地模型等渠道
- ⚡ 异步向量化 + 睡眠/唤醒机制，解决 RAG 数据量衰减问题

---

## 2. 技术栈

### 后端（Python）
| 组件 | 选型 | 用途 |
|------|------|------|
| Web 框架 | **FastAPI 0.110+** | ASGI 异步服务、自动 OpenAPI、原生 SSE 支持 |
| ORM | **SQLAlchemy 2.0** + Alembic | 异步数据库操作、迁移管理 |
| DB 驱动 | **asyncpg** | PostgreSQL 高性能异步驱动 |
| 缓存 | **redis-py (async)** | 热向量索引、Cookie 临时存储、额度计数 |
| 消息队列 | **aio-pika** + Celery | RabbitMQ 异步消费、后台任务调度 |
| HTTP 客户端 | **httpx (async)** | One API 调用、网页抓取 |
| 配置管理 | **Pydantic Settings** | 类型安全的环境变量解析 |
| 向量数据库 | **pymilvus** | Milvus 向量存储与 ANN 检索 |
| LLM SDK | **openai-python (async)** | 官方 SDK，支持流式/结构化输出 |
| 本地 Embedding | **sentence-transformers** | 可选本地 BGE-M3 推理 |
| 图谱（v0.3） | **neo4j-python-driver** | Neo4j 异步驱动 |

### 前端
| 组件 | 选型 |
|------|------|
| 框架 | React 18 + TypeScript + Vite |
| 状态管理 | Zustand |
| UI 组件 | Ant Design 5 |
| EPUB 渲染 | EPUB.js v0.3 |
| PDF 渲染 | PDF.js v4.x |

### 浏览器插件
| 组件 | 选型 |
|------|------|
| 标准 | Chrome Extension Manifest V3 |
| 内容提取 | Readability.js + 自定义规则 |

### 基础设施
| 组件 | 选型 |
|------|------|
| 数据库 | PostgreSQL 16 |
| 向量库 | Milvus 2.3.x Standalone |
| 消息队列 | RabbitMQ 3.12 |
| 缓存 | Redis 7 |
| 对象存储 | MinIO |
| 模型网关 | One API（内置） |
| 部署 | Docker + Docker Compose |
| ASGI 服务器 | Uvicorn |

---

## 3. 项目结构

```
readflow/
├── api/                          # FastAPI 后端服务
│   ├── app/
│   │   ├── main.py               # FastAPI 应用入口
│   │   ├── config.py             # Pydantic Settings 配置
│   │   ├── dependencies.py       # FastAPI Depends 依赖注入
│   │   ├── exceptions.py         # 全局异常定义
│   │   ├── middleware/
│   │   │   ├── jwt.py            # JWT 认证中间件
│   │   │   ├── rate_limit.py     # 限流中间件
│   │   │   └── error_handler.py  # 全局错误处理
│   │   ├── routers/
│   │   │   ├── auth.py           # M9: 认证路由
│   │   │   ├── reader.py         # M1: 阅读器路由
│   │   │   ├── parse.py          # M3: 解析路由
│   │   │   ├── chat.py           # M7: 对话路由
│   │   │   ├── memory.py         # M6: 记忆层路由
│   │   │   ├── channels.py       # M8: One API 渠道路由
│   │   │   ├── usage.py          # M8: 额度管理路由
│   │   │   ├── tasks.py          # M4: 任务状态路由
│   │   │   └── capture.py        # M10: 内容捕获路由
│   │   ├── services/
│   │   │   ├── parse_service.py       # M3: 解析服务
│   │   │   ├── chunk_service.py       # M3: 分块服务
│   │   │   ├── vector_service.py      # M5: 向量检索服务
│   │   │   ├── chat_service.py        # M7: 对话服务
│   │   │   ├── context_builder.py     # M7: 上下文组装
│   │   │   ├── spark_service.py       # M7: 火花模式
│   │   │   ├── model_router.py        # M7+M8: 模型路由
│   │   │   ├── fact_extractor.py      # M6: 事实提取
│   │   │   ├── fact_service.py        # M6: 事实服务
│   │   │   ├── channel_service.py     # M8: 渠道服务
│   │   │   ├── usage_service.py       # M8: 额度服务
│   │   │   ├── capture_gateway.py     # M10: 捕获网关
│   │   │   └── auth_service.py        # M9: 认证服务
│   │   ├── models/
│   │   │   ├── base.py           # SQLAlchemy 基类
│   │   │   ├── user.py           # User/Team/TeamMember
│   │   │   ├── content.py        # ContentSource/Chapter/Chunk
│   │   │   ├── memory.py         # Highlight/Fact
│   │   │   ├── chat.py           # ChatMessage
│   │   │   ├── channel.py        # Channel/TaskModelMapping
│   │   │   └── usage.py          # TokenUsageLog
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── content.py
│   │   │   ├── chat.py
│   │   │   ├── channel.py
│   │   │   └── usage.py
│   │   ├── core/
│   │   │   ├── one_api_client.py     # One API 统一客户端
│   │   │   ├── milvus_client.py      # Milvus 封装
│   │   │   ├── redis_client.py       # Redis 封装
│   │   │   └── rabbitmq_client.py    # RabbitMQ 封装
│   │   └── tasks/
│   │       └── vec_task.py       # Celery 向量化任务
│   ├── alembic/                  # 数据库迁移
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── e2e/
│   │   └── resources/            # 测试数据
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── web/                          # React 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── Reader/           # EPUB/PDF 阅读器
│   │   │   ├── ChatPanel/        # AI 侧边栏
│   │   │   ├── Highlight/      # 高亮组件
│   │   │   └── Settings/       # 设置页面
│   │   ├── stores/
│   │   │   ├── readerStore.ts
│   │   │   └── chatStore.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
│
├── extension/                    # Chrome 插件
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   ├── popup.html
│   ├── popup.js
│   ├── readability.js
│   ├── rules/                    # 平台提取规则
│   └── icons/
│
├── docs/
├── docker-compose.yml
├── Makefile
└── claude.md                     # 本文件
```

---

## 4. 编码规范

### 4.1 Python 规范

- **格式化**：Black，行宽 100，使用单引号
- **Import 排序**：isort（profile = black）
- **类型注解**：全部使用 Python 3.10+ 语法（`str | None` 而非 `Optional[str]`）
- **异步**：所有 IO 操作必须 async，禁止同步阻塞调用
- **错误处理**：自定义业务异常继承 HTTPException，统一在 middleware 转换

```python
# Good
async def get_user(user_id: str) -> User | None:
    return await db.get(User, user_id)

# Bad
def get_user(user_id: str) -> Optional[User]:  # 不要用 Optional
    return db.get(User, user_id)  # 不要同步
```

### 4.2 FastAPI 规范

- **路由**：使用 APIRouter，前缀 `/api/v1/`
- **依赖注入**：使用 `Depends(get_current_user)` 获取当前用户
- **响应模型**：所有接口必须声明 `response_model`
- **流式 SSE**：使用 `StreamingResponse`，事件类型 `message/citation/done/error`

```python
from fastapi import APIRouter, Depends
from typing import Annotated

router = APIRouter(prefix='/api/v1/chat')

@router.post('', response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)]
) -> ChatResponse:
    ...
```

### 4.3 SQLAlchemy 2.0 规范

- **声明式基类**：使用 `Mapped[]` + `mapped_column()`
- **异步会话**：使用 `async_sessionmaker` + `async_scoped_session`
- **关系**：避免懒加载，显式使用 `selectinload`

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # 关系显式声明
    channels: Mapped[list['Channel']] = relationship(back_populates='user')
```

### 4.4 配置管理

使用 Pydantic Settings，环境变量自动解析：

```python
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, RedisDsn

class Settings(BaseSettings):
    database_url: PostgresDsn
    redis_url: RedisDsn
    rabbitmq_url: str
    milvus_uri: str
    one_api_url: str
    secret_key: str
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
```

---

## 5. 关键模块开发指南

### 5.1 向量化任务（M4）

**原则**：异步、可重试、可观测

```python
# api/app/tasks/vec_task.py
from celery import Celery
from app.services.vector_service import vector_service
from app.core.one_api_client import one_api_client

app = Celery('readflow', broker=settings.rabbitmq_url)

@app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_vec_task(self, task_id: str):
    try:
        task = await task_service.get(task_id)
        chunks = task.chunks
        
        # 批量 Embedding，每批 50 个
        for batch in chunks[::50]:
            texts = [c.text for c in batch]
            embeddings = await one_api_client.embed(
                texts, model=task.embedding_model
            )
            await vector_service.insert(task.source_id, batch, embeddings)
        
        await task_service.complete(task_id)
        
    except Exception as exc:
        if self.request.retries < 3:
            raise self.retry(exc=exc)
        await task_service.fail(task_id, str(exc))
```

### 5.2 对话服务（M7）

**原则**：上下文组装 -> 模型路由 -> 流式响应

```python
# api/app/services/chat_service.py
async def stream_chat(
    user_id: str, source_id: str, 
    current_chunk_id: str, question: str
):
    # 1. 组装上下文
    ctx = await context_builder.build(
        user_id, source_id, current_chunk_id, question
    )
    
    # 2. 模型路由
    channel_id = await model_router.route(TaskType.CHAT_QA, user_id)
    
    # 3. 流式调用
    async for chunk in one_api_client.stream_chat(ctx, channel_id):
        yield chunk
    
    # 4. 异步提取事实到 L2
    await fact_extractor.extract_from_dialogue(
        user_id, source_id, question, ctx
    )
```

### 5.3 模型路由（M7+M8）

**原则**：任务类型 -> 用户配置 -> 健康检查 -> 故障转移

```python
# api/app/services/model_router.py
class ModelRouter:
    async def route(self, task_type: TaskType, user_id: str) -> str:
        mapping = await user_config_service.get_mapping(user_id, task_type)
        
        # 检查主渠道
        if await self._is_healthy(mapping.default_channel_id):
            return mapping.default_channel_id
        
        # 故障转移
        for fallback_id in mapping.fallback_channel_ids:
            if await self._is_healthy(fallback_id):
                logger.warning(f'Fallback: {fallback_id}')
                return fallback_id
        
        raise ModelUnavailableException()
```

### 5.4 记忆层提取（M6）

**原则**：异步、轻量模型、结构化输出

```python
# api/app/services/fact_extractor.py
async def extract_from_highlight(
    user_id: str, source_id: str, 
    chunk_id: str, text: str, note: str | None
):
    prompt = f'''从以下阅读笔记中提取核心事实，以JSON格式返回：
原文：{text}
用户笔记：{note or '无'}

要求：
- 提取1-3个关键事实
- 每个事实包含：subject、predicate、object、confidence
'''
    response = await one_api_client.chat(
        model='deepseek-chat',  # 轻量模型
        messages=[{'role': 'user', 'content': prompt}],
        response_format={'type': 'json_object'}
    )
    
    facts = parse_facts(response)
    await fact_repository.save_all(facts)
    
    # 向量化存入 L2
    embeddings = await one_api_client.embed([f.to_text() for f in facts])
    await vector_service.insert_l2(user_id, facts, embeddings)
```

### 5.5 内容捕获网关（M10）

**原则**：最小权限、临时存储、立即清理

```python
# api/app/services/capture_gateway.py
class CaptureGateway:
    async def receive_web(self, request: CaptureWebRequest) -> str:
        # 1. 校验大小
        if len(request.html) > 10 * 1024 * 1024:
            raise ContentTooLargeException()
        
        # 2. 提取 Cookie（5分钟 TTL）
        cookie = None
        if request.cookie_encrypted:
            cookie = await decrypt_cookie(request.cookie_encrypted)
        
        # 3. 创建解析任务
        task_id = await parse_service.create_task(request, cookie)
        
        # 4. 立即清理 Cookie
        if request.cookie_encrypted:
            await redis.delete(f'capture:cookie:{request.request_id}')
        
        # 5. 审计日志
        await audit_log.log('CAPTURE', request.user_id, request.url)
        
        return task_id
```

---

## 6. 常用命令

```bash
# 开发环境启动
docker-compose up -d                    # 启动所有基础设施
uvicorn app.main:app --reload --port 8000 # 启动 FastAPI 开发服务器
celery -A app.tasks worker --loglevel=info # 启动 Celery Worker

# 数据库迁移
alembic revision --autogenerate -m "init"
alembic upgrade head
alembic downgrade -1

# 测试
pytest                                    # 运行所有测试
pytest tests/unit -v                      # 仅单元测试
pytest tests/integration -v               # 仅集成测试
pytest --cov=app --cov-report=html        # 覆盖率报告

# 代码检查
black app/ tests/ --check
isort app/ tests/ --check-only
mypy app/                                 # 类型检查（如有配置）

# 构建部署
docker build -t readflow-api ./api
docker build -t readflow-web ./web
docker-compose -f docker-compose.yml up -d
```

---

## 7. 环境变量

```bash
# .env 示例
DATABASE_URL=postgresql+asyncpg://readflow:changeme@localhost:5432/readflow
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://readflow:changeme@localhost:5672/
MILVUS_URI=http://localhost:19530
ONE_API_URL=http://localhost:3000
SECRET_KEY=your-secret-key-here
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=readflow
MINIO_SECRET_KEY=changeme
```

---

## 8. 注意事项

### 8.1 异步原则
- **所有数据库操作必须 async**：使用 `await session.execute(...)`，禁止 `session.query(...)`
- **所有 HTTP 调用必须 async**：使用 `httpx.AsyncClient`，禁止 `requests`
- **所有 Redis 操作必须 async**：使用 `redis.asyncio`，禁止 `redis.Redis`
- **Celery Worker 内调用 async 函数**：使用 `asyncio.run(...)` 或 `async_to_sync`

### 8.2 向量数据库
- **Milvus 连接**：使用 `MilvusClient`（非旧版 `connections.connect`）
- **集合字段**：`text` 字段限制 4096 字符，超长截断
- **分区策略**：按 `user_id` 做 Partition Key，避免跨用户数据泄露
- **睡眠机制**：24 小时未访问自动标记睡眠，唤醒时从冷存储重建

### 8.3 One API 集成
- **渠道配置**：API Key 使用 AES-256-GCM 加密存储，前端永不返回明文
- **任务映射**：每个用户独立配置，支持 `embedding/chat_qa/chat_code/chat_summary/spark_mode`
- **额度扣减**：使用 Redis Lua 脚本保证原子性，余额不足自动停用渠道
- **故障转移**：主渠道失败时自动切换 fallback，30 秒内完成

### 8.4 安全
- **JWT**：HS256 签名，access token 有效期 24 小时
- **Cookie**：插件传输 Cookie 使用临时对称密钥加密，TTL 5 分钟
- **限流**：网页捕获每用户每分钟 10 次，文本捕获每分钟 20 次
- **SQL 注入**：SQLAlchemy 2.0 参数化查询，禁止字符串拼接 SQL

### 8.5 前端-后端协作
- **阅读位置**：前端节流 3 秒后发送，后端 Redis Hash 存储
- **高亮**：前端通过 EPUB.js/PDF.js 获取 CFI/页码，后端存储 chunk_id 关联
- **流式对话**：FastAPI `StreamingResponse` + 前端 `EventSource`，事件类型：`message`/`citation`/`done`/`error`
- **任务状态**：向量化任务状态通过 WebSocket 或轮询通知前端

---

## 9. 迭代路线

| 阶段 | 周期 | 核心交付 |
|------|------|----------|
| **MVP** | 6周 | 单文档阅读 + 基础 RAG 问答 + One API 最简版 + L2 记忆 |
| **v0.2** | +4周 | 浏览器插件 + 认证穿透 + 额度管理 + 团队基础 |
| **v0.3** | +4周 | L3 知识图谱 + 多源关联 + 网页对比阅读 |
| **v0.4** | +4周 | 苏格拉底模式 + 自动摘要流 + 阅读仪表盘 |

---

## 10. 参考文档

- [ReadFlow PRD v0.3](./docs/PRD.md)
- [ReadFlow 技术方案](./docs/architecture/tech_schedule.md)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [One API 文档](https://github.com/songquanpeng/one-api)
- [Milvus Python SDK](https://milvus.io/docs/python.md)

---

*本文档跟随项目迭代更新。最后更新：2026-06-29*