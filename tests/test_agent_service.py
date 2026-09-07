import unittest

from src.cyberfoodie.agent_service import (
    assign_signature_dishes,
    build_agents,
    fallback_judgement,
    fallback_speech,
)
from src.cyberfoodie.menu_service import load_menu


class AgentServiceTest(unittest.TestCase):
    def test_signature_dishes_are_distinct_and_style_matched(self):
        prefs = {"taste": "咸香", "budget": 22, "weather": "晴", "avoid": "无", "scene": "晚自习前"}
        agents = build_agents(
            {
                "agents": {
                    "agent_a": {"name": "西北碳水派", "style": "偏西北面食，重视碳水、牛肉、饱腹和省钱"},
                    "agent_b": {"name": "江浙甜鲜派", "style": "偏江浙菜，喜欢酸甜、鲜香、清爽和低负担"},
                }
            }
        )
        signatures = assign_signature_dishes(load_menu(), prefs, agents)
        self.assertNotEqual(signatures["agent_a"]["name"], signatures["agent_b"]["name"])
        self.assertIn("西北", signatures["agent_a"]["tags"])
        self.assertIn("江浙", signatures["agent_b"]["tags"])

    def test_fallback_speech_keeps_same_signature_dish(self):
        prefs = {"taste": "辣", "budget": 25, "weather": "雨", "avoid": "无", "scene": "普通午餐"}
        agents = build_agents({})
        signatures = assign_signature_dishes(load_menu(), prefs, agents)
        dish_name = signatures["agent_a"]["name"]
        for round_no in range(1, 4):
            self.assertIn(dish_name, fallback_speech("agent_a", round_no, prefs, signatures))

    def test_fallback_judge_uses_only_signature_dishes(self):
        prefs = {"taste": "辣", "budget": 25, "weather": "雨", "avoid": "无", "scene": "普通午餐"}
        agents = build_agents({})
        signatures = assign_signature_dishes(load_menu(), prefs, agents)
        report = fallback_judgement(prefs, signatures, agents)
        allowed = {dish["name"] for dish in signatures.values()}
        self.assertIn(report["recommended_dish"], allowed)
        self.assertIn(report["backup_dish"], allowed)


if __name__ == "__main__":
    unittest.main()
