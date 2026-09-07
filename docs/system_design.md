# CyberFoodie Agent 系统级架构设计规约

## 1. 系统概述

CyberFoodie Agent 面向大学生日常“今天吃什么”的决策困难场景。系统读取真实菜单 JSON，结合用户的口味、预算、天气、忌口、就餐场景和心情输入，为两个不同菜系/性格的 AI Agent 分配固定主推菜。随后两个 Agent 进行三轮实时辩论，最后由裁判 Agent 输出结构化选餐战报。

系统边界包含前端页面、Python 后端服务、菜单数据文件、DeepSeek 外部大模型 API 和本地兜底逻辑。当前版本不依赖数据库，菜单以 JSON 文件持久化，辩论会话以内存对象维护。

## 2. 功能模型

### 2.1 系统顶层用例图

```mermaid
flowchart LR
    User[用户/学生]
    LLM[外部大模型 API<br>DeepSeek]
    Timer[定时/演示触发器]
    System((CyberFoodie Agent))

    User -->|输入口味、预算、天气、忌口| System
    User -->|自定义 Agent 名称与性格| System
    Timer -->|触发健康检查或演示请求| System
    System -->|请求 Agent 发言与裁判战报| LLM
    LLM -->|返回辩论内容与 JSON 战报| System
    System -->|实时展示辩论| User
    System -->|输出最终推荐| User
```

### 2.2 系统数据流图

```mermaid
flowchart TB
    A[用户偏好表单] --> B[HTTP Server]
    B --> C[偏好解析与校验]
    C --> D[菜单服务<br>读取 real_menu.json]
    D --> E[菜品基础评分]
    C --> F[Agent 配置解析]
    E --> G[主推菜分配器]
    F --> G
    G --> H[辩论编排器]
    H --> I[DeepSeek Client]
    I --> J[DeepSeek API]
    J --> H
    H --> K[NDJSON 流式事件]
    K --> L[前端实时对话区]
    H --> M[裁判 Agent]
    M --> N[结构化战报]
    N --> L
    I -.异常.-> O[本地兜底生成器]
    O --> H
```

## 3. 数据模型

### 3.1 系统领域类图

```mermaid
classDiagram
    class FoodPreference {
        +str taste
        +int budget
        +str weather
        +str avoid
        +str scene
        +str mood
    }
    class AgentProfile {
        +str name
        +str tagline
        +str style
        +str color
    }
    class MenuItem {
        +str name
        +str source
        +int price
        +str category
        +list tags
        +list weather_fit
        +list available_time
        +int popularity
        +str desc
    }
    class DebateSpeech {
        +int round
        +str agent
        +str dish_name
        +str content
        +str source
        +str time
    }
    class BattleReport {
        +str winner_agent
        +str recommended_dish
        +str backup_dish
        +dict score
        +list reasons
        +str risk
        +str summary
    }
    class MenuService {
        +load_menu()
        +score_dish()
        +choose_candidates()
    }
    class AgentService {
        +build_agents()
        +assign_signature_dishes()
        +debate_events()
        +judge()
    }
    class DeepSeekClient {
        +call_deepseek()
    }

    FoodPreference --> AgentService
    AgentProfile --> AgentService
    MenuItem --> MenuService
    MenuService --> AgentService
    AgentService --> DeepSeekClient
    AgentService --> DebateSpeech
    AgentService --> BattleReport
```

### 3.2 ER Diagram / Schema

```mermaid
erDiagram
    MENU_ITEM {
        string name PK
        string source
        int price
        string category
        string_array tags
        string_array weather_fit
        string_array available_time
        int popularity
        string desc
    }
    AGENT_PROFILE {
        string key PK
        string name
        string style
        string tagline
        string color
    }
    FOOD_PREFERENCE {
        string session_id PK
        string taste
        int budget
        string weather
        string avoid
        string scene
        string mood
    }
    DEBATE_SPEECH {
        string session_id FK
        int round
        string agent_key FK
        string dish_name FK
        string content
        string source
        string time
    }
    BATTLE_REPORT {
        string session_id PK
        string winner_agent
        string recommended_dish FK
        string backup_dish FK
        json score
        json reasons
        string risk
        string summary
    }

    FOOD_PREFERENCE ||--o{ DEBATE_SPEECH : produces
    AGENT_PROFILE ||--o{ DEBATE_SPEECH : speaks
    MENU_ITEM ||--o{ DEBATE_SPEECH : supports
    FOOD_PREFERENCE ||--|| BATTLE_REPORT : summarized_by
    MENU_ITEM ||--o{ BATTLE_REPORT : selected_in
```

说明：当前实现以 JSON 文件和内存对象承载以上 Schema。若后续接入数据库，可将 `MENU_ITEM` 作为菜品表，`FOOD_PREFERENCE`、`DEBATE_SPEECH`、`BATTLE_REPORT` 作为会话记录表，并为 `session_id`、`agent_key`、`dish_name` 建立索引。

核心数据契约在 `src/cyberfoodie/schemas.py` 中以 dataclass 表达，可平滑迁移为 Pydantic BaseModel。

## 4. 动态 / 行为模型

### 4.1 端到端核心时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant FE as 前端页面
    participant BE as Python 后端
    participant MS as MenuService
    participant AS as AgentService
    participant DS as DeepSeekClient
    participant API as DeepSeek API

    U->>FE: 填写偏好与 Agent 性格
    FE->>BE: POST /api/debate-stream
    BE->>AS: parse_preferences + build_agents
    AS->>MS: load_menu + choose_candidates
    AS->>AS: assign_signature_dishes
    BE-->>FE: start 事件
    loop 3轮 x 2 Agent
        AS->>DS: 请求固定主推菜发言
        DS->>API: Chat Completions
        API-->>DS: Agent 发言
        DS-->>AS: 文本结果
        BE-->>FE: speech 事件
    end
    AS->>DS: 请求裁判 JSON 战报
    DS->>API: Chat Completions
    API-->>DS: 结构化战报
    BE-->>FE: report 事件
    BE-->>FE: done 事件
```

### 4.2 系统生命周期状态机图

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> PARSING: 用户提交表单
    PARSING --> SELECTING: 参数合法
    SELECTING --> DEBATING: 分配固定主推菜
    DEBATING --> JUDGING: 完成全部发言
    JUDGING --> SUCCESS: 战报生成成功
    PARSING --> FAILED: 请求体非法
    SELECTING --> FAILED: 菜单为空或数据异常
    DEBATING --> FALLBACK: LLM 发言失败
    JUDGING --> FALLBACK: 裁判 JSON 失败
    FALLBACK --> DEBATING: 本地生成发言
    FALLBACK --> SUCCESS: 本地生成战报
    SUCCESS --> IDLE: 用户再次开赛
    FAILED --> IDLE: 用户修正输入
```

## 5. 关键架构约束

- 菜单数据必须来自 `src/data/real_menu.json`，页面不提前暴露候选全集。
- 每个 Agent 在辩论开始前锁定一个固定主推菜，三轮中不得改变立场。
- 裁判 Agent 的推荐范围限定在两个固定主推菜内。
- DeepSeek 调用失败时必须进入本地兜底流程，保证演示稳定。
- 前端使用流式 NDJSON 响应逐条展示发言。
