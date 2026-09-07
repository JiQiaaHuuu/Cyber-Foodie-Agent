# CyberFoodie Agent

CyberFoodie Agent 是一个面向大学生“今天吃什么”场景的 AI 原生应用。系统根据口味、预算、天气、忌口和就餐场景，从真实菜单 JSON 中为两个不同菜系/性格的 Agent 分配固定主推菜，再通过 DeepSeek 生成实时辩论和最终结构化选餐战报。

## 功能特性

- 实时流式辩论：后端通过 NDJSON 逐条推送 Agent 发言，前端即时展示。
- 固定主推菜：每个 Agent 开赛前锁定一道菜，三轮辩论保持同一立场。
- 自定义 Agent：支持自定义两个 Agent 的名称和性格提示词。
- 真实菜单数据：读取 `src/data/real_menu.json`，包含 33 道多菜系食堂菜品与标签。
- DeepSeek 接入：默认调用 `deepseek-chat`，失败时自动使用本地兜底。
- 工程化文档：包含系统级三大模型、6 大架构图、User Story 精细化建模和 Sprint 报告。

## 快速启动

```powershell
& "D:\anaconda\envs\langgraph\python.exe" .\app.py
```

打开浏览器访问：

```text
http://127.0.0.1:8000
```

## 环境变量

复制 `.env.example` 并配置真实 Key，或在工作区上级目录保留本地 `api key.txt`：

```text
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/chat/completions
PORT=8000
```

真实 API Key 不应提交到 GitHub。

## 仓库拓扑

```text
.
├── .github/
│   ├── workflows/ci.yml
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── system_design.md
│   ├── user_stories/
│   ├── sprint1_report.md
│   ├── sprint2_report.md
│   ├── sprint3_report.md
│   └── sprint4_report.md
├── src/
│   ├── cyberfoodie/
│   ├── static/
│   └── data/
├── tests/
├── eval/
├── AGENTS.md
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 文档入口

- [系统级架构设计规约](docs/system_design.md)
- [US01 实时 AI 干饭辩论](docs/user_stories/US01_realtime_food_debate.md)
- [US02 自定义菜系 Agent](docs/user_stories/US02_custom_agents.md)
- [US03 基于真实菜单数据推荐](docs/user_stories/US03_menu_based_recommendation.md)
- [Sprint 1 迭代报告](docs/sprint1_report.md)
- [Sprint 2 迭代报告](docs/sprint2_report.md)
- [Sprint 3 迭代报告](docs/sprint3_report.md)
- [Sprint 4 迭代报告](docs/sprint4_report.md)

## 本地验证

```powershell
& "D:\anaconda\envs\langgraph\python.exe" -m compileall app.py src tests
& "D:\anaconda\envs\langgraph\python.exe" -m unittest discover -s tests
```
