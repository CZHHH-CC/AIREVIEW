# JDReview · AI 简历推荐系统

招聘方输入岗位需求(JD)，AI 阅读简历库后**排序推荐候选人并给出推荐理由与差距分析**。
AI 引擎可在**阿里云百炼(通义千问)** 与 **Ollama(本地)** 之间一键切换。

## 架构

```
backend/   FastAPI 后端
  app/
    config.py       读取 .env，选择 AI 提供方
    llm.py          OpenAI 兼容客户端（百炼 / Ollama 共用）
    recommender.py  核心：JD + 简历 → AI 排序 + 理由
    store.py        简历存储（JSON 文件，适合小规模）
    main.py         API + 托管前端
  data/resumes.json 简历库（含 8 份示例）
frontend/
  index.html        Vue 3 单页（CDN，无需构建），由后端托管
```

> 小规模(几十~几百份)直接把简历送进模型上下文，无需向量库。
> 数据量增长到上千份后，可在 `recommender.py` 前加一层关键词/向量召回再交给 AI 精排。

## 快速开始

### 1. 安装依赖
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. 配置 AI 引擎
```bash
copy .env.example .env        # Windows（Linux/Mac 用 cp）
```
编辑 `.env`：

**用百炼：** 设 `LLM_PROVIDER=bailian`，填入 `DASHSCOPE_API_KEY`
（在 https://bailian.console.aliyun.com 创建）。

**用 Ollama：** 设 `LLM_PROVIDER=ollama`，先 `ollama pull qwen2.5` 启动本地服务。

### 3. 启动
```bash
uvicorn app.main:app --reload --port 8000
# 或在项目根目录运行 run.bat
```
浏览器打开 http://localhost:8000

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/config` | 当前 AI 提供方/模型 |
| GET  | `/api/resumes` | 简历列表 |
| POST | `/api/resumes` | 新增简历 |
| DELETE | `/api/resumes/{id}` | 删除简历 |
| POST | `/api/recommend` | 传 `{jd, top_n}` 返回推荐结果 |

## 容器化部署（Docker）

```bash
# 1. 准备环境变量（密钥不会进镜像，运行时注入）
copy backend\.env.example backend\.env   # 填好 DASHSCOPE_API_KEY 或切 ollama

# 2. 构建并启动
docker compose up -d --build
# 打开 http://localhost:8000
```

**用容器内的 Ollama（无需百炼密钥）：**
```bash
docker compose --profile ollama up -d --build
docker compose exec ollama ollama pull qwen2.5
# backend/.env 设: LLM_PROVIDER=ollama  OLLAMA_BASE_URL=http://ollama:11434/v1
docker compose restart app
```

简历库通过 volume 挂载到 `./backend/data`，容器重建数据不丢。

## 切换引擎

只改 `.env` 里的 `LLM_PROVIDER`，无需改代码——百炼和 Ollama 都走 OpenAI 兼容协议。
