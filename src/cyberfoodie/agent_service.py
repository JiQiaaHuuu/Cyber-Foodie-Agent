from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, Iterable, List

from .deepseek_client import call_deepseek
from .menu_service import choose_candidates, load_menu, normalize_words, score_dish


DEFAULT_AGENTS = {
    "agent_a": {
        "name": "川湘火辣派",
        "tagline": "偏川菜湘菜，强调辣、香、下饭和满足感",
        "style": "偏川菜湘菜，直接热烈，强调辣、香、下饭、解馋和满足感",
        "color": "#d9472f",
    },
    "agent_b": {
        "name": "粤式清养派",
        "tagline": "偏粤菜清淡，强调汤水、均衡和低负担",
        "style": "偏粤菜清淡，冷静细致，强调汤水、营养均衡、高蛋白和低负担",
        "color": "#2a8c6a",
    },
}

STYLE_KEYWORDS = {
    "川湘火辣": {"primary": ["川菜", "湘菜"], "secondary": ["辣", "麻辣", "香辣", "重口", "下饭", "解馋", "满足"]},
    "粤式清养": {"primary": ["粤菜"], "secondary": ["清淡", "养生", "热汤", "高蛋白", "低负担", "养胃", "滋补"]},
    "西北碳水": {"primary": ["西北"], "secondary": ["面食", "碳水", "牛肉", "饱腹", "热汤", "省钱"]},
    "江浙甜鲜": {"primary": ["江浙"], "secondary": ["酸甜", "甜咸", "鲜香", "清爽", "低负担"]},
    "日韩简餐": {"primary": ["日式", "韩式"], "secondary": ["拌饭", "泡菜", "微辣", "轻食", "蔬菜"]},
    "东北硬菜": {"primary": ["东北"], "secondary": ["猪肉", "鸡肉", "热乎", "重口", "满足", "饱腹"]},
    "云南汤粉": {"primary": ["云南"], "secondary": ["米线", "酸辣", "热汤", "菌菇", "开胃"]},
    "省钱效率": {"primary": ["省钱"], "secondary": ["快餐", "面食", "小吃", "饱腹", "早餐", "夜宵"]},
}


def build_agents(body: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    agents = json.loads(json.dumps(DEFAULT_AGENTS, ensure_ascii=False))
    custom = body.get("agents") if isinstance(body.get("agents"), dict) else {}

    for key in ("agent_a", "agent_b"):
        item = custom.get(key, {}) if isinstance(custom.get(key), dict) else {}
        name = str(item.get("name") or "").strip()
        style = str(item.get("style") or "").strip()
        if name:
            agents[key]["name"] = name
        if style:
            agents[key]["style"] = style
            agents[key]["tagline"] = style[:34]
    return agents


def style_terms(agent: Dict[str, str]) -> Dict[str, List[str]]:
    text = f"{agent.get('name', '')} {agent.get('style', '')}"
    primary_terms: List[str] = []
    secondary_terms: List[str] = []
    for trigger, groups in STYLE_KEYWORDS.items():
        if trigger in text or any(token in text for token in groups["primary"]):
            primary_terms.extend(groups["primary"])
            secondary_terms.extend(groups["secondary"])

    for token in normalize_words(text):
        if len(token) >= 2:
            secondary_terms.append(token)
    return {
        "primary": list(dict.fromkeys(primary_terms)),
        "secondary": list(dict.fromkeys(secondary_terms)),
    }


def agent_dish_score(dish: Dict[str, Any], prefs: Dict[str, Any], agent: Dict[str, str]) -> int:
    tags = dish.get("tags", [])
    haystack = " ".join([dish.get("name", ""), dish.get("desc", ""), dish.get("source", ""), *tags])
    score = score_dish(dish, prefs)
    terms = style_terms(agent)
    for term in terms["primary"]:
        if term in tags:
            score += 42
        elif term and term in haystack:
            score += 26
    for term in terms["secondary"]:
        if term in tags:
            score += 14
        elif term and term in haystack:
            score += 7
    return score


def assign_signature_dishes(menu: List[Dict[str, Any]], prefs: Dict[str, Any], agents: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    assignments: Dict[str, Dict[str, Any]] = {}
    used_names = set()
    for agent_key in ("agent_a", "agent_b"):
        ranked = sorted(menu, key=lambda item: agent_dish_score(item, prefs, agents[agent_key]), reverse=True)
        selected = next((item for item in ranked if item["name"] not in used_names), ranked[0])
        assignments[agent_key] = selected
        used_names.add(selected["name"])
    return assignments


def fallback_speech(agent_key: str, round_no: int, prefs: Dict[str, Any], signature_dishes: Dict[str, Dict[str, Any]]) -> str:
    dish = signature_dishes[agent_key]
    source = dish.get("source", "校园档口")
    budget = prefs.get("budget", "不限")
    weather = prefs.get("weather", "当前天气")
    taste = prefs.get("taste", "综合口味")

    if agent_key == "agent_a":
        points = [
            f"第{round_no}轮我坚持{dish['name']}。{taste}需求要先满足，{source}这份{dish['price']}元，吃完有状态继续学习。",
            f"预算{budget}元内要看满足感，{dish['name']}价格合适，{dish['desc']}，比犹豫半天更实际。",
            f"{weather}天更需要打开胃口，{dish['name']}的标签是{','.join(dish.get('tags', []))}，适合作为主推。",
        ]
    else:
        points = [
            f"第{round_no}轮我继续推荐{dish['name']}。它来自{source}，{dish['desc']}，更适合把下午状态稳住。",
            f"预算{budget}元内不只看爽感，{dish['name']}价格{dish['price']}元，搭配更均衡。",
            f"{weather}天要考虑身体负担，{dish['name']}更稳，作为长期选择不容易踩雷。",
        ]
    return points[(round_no - 1) % len(points)]


def agent_turn(
    agent_key: str,
    round_no: int,
    prefs: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    signature_dishes: Dict[str, Dict[str, Any]],
    transcript: List[Dict[str, Any]],
    agents: Dict[str, Dict[str, str]],
) -> Dict[str, Any]:
    agent = agents[agent_key]
    signature = signature_dishes[agent_key]
    opponent_key = "agent_b" if agent_key == "agent_a" else "agent_a"
    opponent_dish = signature_dishes[opponent_key]
    menu_text = "\n".join(
        f"- {item['name']}：{item['price']}元，来源{item.get('source', '校园档口')}，标签{','.join(item.get('tags', []))}，{item['desc']}"
        for item in candidates
    )
    history = "\n".join(f"{item['agent']}：{item['content']}" for item in transcript[-4:])
    messages = [
        {
            "role": "system",
            "content": (
                f"你是{agent['name']}，你的性格和立场是：{agent['style']}。"
                f"你的固定主推菜是{signature['name']}，来自{signature.get('source', '校园档口')}。"
                f"对方主推菜是{opponent_dish['name']}。每次只输出一段中文发言，90字以内，"
                "必须始终坚持自己的固定主推菜，不能改推其他菜，可以补充新理由或反驳对方。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"用户偏好：{json.dumps(prefs, ensure_ascii=False)}\n"
                f"真实菜单：\n{menu_text}\n"
                f"最近辩论：\n{history or '暂无'}\n"
                f"现在是第{round_no}轮，请围绕你的固定主推菜{signature['name']}发言。"
            ),
        },
    ]
    try:
        content = call_deepseek(messages)
        source = "deepseek"
    except Exception:
        content = fallback_speech(agent_key, round_no, prefs, signature_dishes)
        source = "local"

    return {
        "round": round_no,
        "agent": agent["name"],
        "agent_key": agent_key,
        "dish_name": signature["name"],
        "dish_source": signature.get("source", "校园档口"),
        "content": content,
        "source": source,
        "time": time.strftime("%H:%M:%S"),
    }


def normalize_report(report: Dict[str, Any]) -> None:
    score = report.get("score")
    if not isinstance(score, dict):
        report["score"] = {"口味匹配": 80, "预算匹配": 80, "天气适配": 80, "综合稳定": 80}
        return

    values = [float(value) for value in score.values() if isinstance(value, (int, float))]
    ten_point_scale = bool(values) and max(values) <= 10
    for key, value in list(score.items()):
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = 80
        if ten_point_scale:
            number *= 10
        score[key] = max(0, min(100, round(number)))


def fallback_judgement(prefs: Dict[str, Any], signature_dishes: Dict[str, Dict[str, Any]], agents: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    dishes = list(signature_dishes.values())
    ranked = sorted(dishes, key=lambda item: score_dish(item, prefs), reverse=True)
    winner = ranked[0]
    runner = ranked[1] if len(ranked) > 1 else ranked[0]
    winner_key = next(key for key, dish in signature_dishes.items() if dish["name"] == winner["name"])
    return {
        "winner_agent": agents[winner_key]["name"],
        "recommended_dish": winner["name"],
        "backup_dish": runner["name"],
        "score": {
            "口味匹配": min(95, 70 + score_dish(winner, prefs) // 4),
            "预算匹配": 92 if winner["price"] <= int(prefs.get("budget") or 25) else 62,
            "天气适配": 88 if prefs.get("weather") in winner.get("weather_fit", []) else 72,
            "综合稳定": 86,
        },
        "reasons": [
            f"{winner['name']}来自{winner.get('source', '校园档口')}，价格{winner['price']}元，与当前预算匹配。",
            f"菜品特点是{winner['desc']}，适合“{prefs.get('scene', '日常用餐')}”场景。",
            "辩论过程同时比较了口味满足、身体负担、天气适配和性价比。",
        ],
        "risk": "真实供应会受档口营业和库存影响，忌口仍需以现场配料为准。",
        "summary": f"建议选择{winner['name']}，备选{runner['name']}。",
    }


def judge(prefs: Dict[str, Any], signature_dishes: Dict[str, Dict[str, Any]], transcript: List[Dict[str, Any]], agents: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    prompt = {
        "preferences": prefs,
        "signature_dishes": {key: {"agent": agents[key]["name"], "dish": dish} for key, dish in signature_dishes.items()},
        "agents": agents,
        "transcript": transcript,
        "required_schema": {
            "winner_agent": "获胜Agent名称",
            "recommended_dish": "最终推荐菜名",
            "backup_dish": "备选菜名",
            "score": {"口味匹配": 0, "预算匹配": 0, "天气适配": 0, "综合稳定": 0},
            "reasons": ["三条推荐理由"],
            "risk": "一句风险提示",
            "summary": "一句最终建议",
        },
    }
    messages = [
        {
            "role": "system",
            "content": (
                "你是公正裁判。只输出严格 JSON，不要 Markdown，不要代码块。评分必须是0到100。"
                "最终推荐菜和备选菜只能从两个 Agent 的固定主推菜中选择，不能引入第三道菜。"
            ),
        },
        {"role": "user", "content": "根据以下辩论生成结构化选餐战报：\n" + json.dumps(prompt, ensure_ascii=False)},
    ]
    try:
        raw = call_deepseek(messages, temperature=0.4)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?|```$", "", cleaned, flags=re.MULTILINE).strip()
        report = json.loads(cleaned)
        normalize_report(report)
        report["source"] = "deepseek"
        return report
    except Exception:
        report = fallback_judgement(prefs, signature_dishes, agents)
        report["source"] = "local"
        return report


def debate_events(prefs: Dict[str, Any], agents: Dict[str, Dict[str, str]]) -> Iterable[Dict[str, Any]]:
    menu = load_menu()
    candidates = choose_candidates(menu, prefs)
    signature_dishes = assign_signature_dishes(menu, prefs, agents)
    transcript: List[Dict[str, Any]] = []

    yield {"type": "start", "agents": agents, "preferences": prefs, "signature_dishes": signature_dishes}
    for round_no in range(1, 4):
        for agent_key in ("agent_a", "agent_b"):
            yield {"type": "status", "message": f"第{round_no}轮 {agents[agent_key]['name']} 发言中"}
            speech = agent_turn(agent_key, round_no, prefs, candidates, signature_dishes, transcript, agents)
            transcript.append(speech)
            yield {"type": "speech", "speech": speech}

    yield {"type": "status", "message": "裁判生成战报中"}
    yield {"type": "report", "report": judge(prefs, signature_dishes, transcript, agents)}
    yield {"type": "done"}


def run_debate(prefs: Dict[str, Any], agents: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    transcript = []
    signature_dishes = {}
    report = {}
    for event in debate_events(prefs, agents):
        if event["type"] == "start":
            signature_dishes = event["signature_dishes"]
        elif event["type"] == "speech":
            transcript.append(event["speech"])
        elif event["type"] == "report":
            report = event["report"]
    return {
        "agents": agents,
        "preferences": prefs,
        "signature_dishes": signature_dishes,
        "transcript": transcript,
        "report": report,
    }


def parse_preferences(body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "taste": str(body.get("taste") or "辣").strip(),
        "budget": int(body.get("budget") or 25),
        "weather": str(body.get("weather") or "晴").strip(),
        "avoid": str(body.get("avoid") or "无").strip(),
        "scene": str(body.get("scene") or "普通午餐").strip(),
        "mood": str(body.get("mood") or "想吃得满足").strip(),
    }
