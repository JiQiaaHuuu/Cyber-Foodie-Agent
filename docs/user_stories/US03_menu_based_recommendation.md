# US03 基于真实菜单数据推荐

## Card

作为学生，我希望系统根据食堂真实菜单数据进行推荐，以便结果更接近校园实际可获得的菜品。

## INVEST

| 原则 | 说明 |
| --- | --- |
| Independent | 菜单数据以 JSON 读取，可独立维护。 |
| Negotiable | 菜品数量、标签体系和评分权重可迭代。 |
| Valuable | 推荐结果更真实，便于课堂展示。 |
| Estimable | 涉及菜单 Schema、读取、评分和测试。 |
| Small | 当前不接数据库，仅维护本地 JSON。 |
| Testable | 可检查菜单数量、字段完整性和标签匹配。 |

## Conversation

- 菜单保存在 `src/data/real_menu.json`。
- 每道菜含名称、来源、价格、分类、标签、天气适配、供应时段、热度和描述。
- 系统不会在页面提前展示完整候选菜单。
- Agent 会读取菜单，并只展示自己最终分配到的主推菜。

## Confirmation

```gherkin
Feature: 真实菜单推荐
  Scenario: 菜单数据参与主推菜分配
    Given 菜单 JSON 至少包含 30 道带标签菜品
    When 用户提交偏好
    Then 系统应读取菜单进行评分
    And 两个 Agent 应获得不同主推菜
    And 最终推荐应来自两个主推菜之一
```

## 1. 故事级用例 / 边界图

```mermaid
flowchart LR
    User[学生] --> Pref[偏好输入]
    Pref --> Menu[真实菜单 JSON]
    Menu --> Rank[菜品评分排序]
    Rank --> AgentDish[Agent 主推菜]
    AgentDish --> Report[最终推荐]
```

## 2. 故事级组件 / 数据流图

```mermaid
flowchart TB
    JSON[real_menu.json] --> Load[load_menu]
    Load --> Validate[字段完整性]
    Validate --> BaseScore[用户需求基础分]
    AgentTerms[Agent 关键词] --> StyleScore[风格加权分]
    BaseScore --> Total[综合分]
    StyleScore --> Total
    Total --> Signature[固定主推菜]
```

## 3. 故事级领域类与数据契约图

```mermaid
classDiagram
    class MenuItem {
        +string name
        +string source
        +int price
        +string category
        +list tags
        +list weather_fit
        +list available_time
        +int popularity
        +string desc
    }
    class FoodPreference {
        +string taste
        +int budget
        +string weather
        +string avoid
        +string scene
    }
    class SignatureDishAssignment {
        +string agent_key
        +string menu_item_name
    }
    MenuItem --> SignatureDishAssignment
    FoodPreference --> SignatureDishAssignment
```

## 4. 故事级数据实体关系 / 持久化模型

```mermaid
erDiagram
    MENU_ITEM {
        string name PK
        string source
        int price
        string category
        string_array tags
    }
    MENU_TAG {
        string menu_item_name FK
        string tag
    }
    ASSIGNMENT {
        string agent_key
        string menu_item_name FK
        int score
    }
    MENU_ITEM ||--o{ MENU_TAG : has
    MENU_ITEM ||--o{ ASSIGNMENT : selected_as
```

## 5. 故事级端到端时序交互图

```mermaid
sequenceDiagram
    participant BE as 后端
    participant MS as MenuService
    participant AS as AgentService
    BE->>MS: load_menu()
    MS-->>BE: 菜单列表
    BE->>MS: choose_candidates(prefs)
    MS-->>AS: 候选菜品
    AS->>AS: agent_dish_score
    AS-->>BE: signature_dishes
```

## 6. 故事级微观状态转换与活动流程图

```mermaid
stateDiagram-v2
    [*] --> MenuLoading
    MenuLoading --> MenuReady
    MenuReady --> Scoring
    Scoring --> Assigned
    Assigned --> HiddenFromPage
    HiddenFromPage --> AgentDebate
    MenuLoading --> DataError
```
