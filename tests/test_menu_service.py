import unittest

from src.cyberfoodie.menu_service import load_menu, score_dish


class MenuServiceTest(unittest.TestCase):
    def test_real_menu_has_rich_tagged_items(self):
        menu = load_menu()
        self.assertGreaterEqual(len(menu), 30)
        for item in menu:
            self.assertIn("name", item)
            self.assertIn("source", item)
            self.assertIn("price", item)
            self.assertGreaterEqual(len(item.get("tags", [])), 5)

    def test_scoring_prefers_budget_and_taste_match(self):
        spicy = {
            "name": "测试辣饭",
            "price": 20,
            "tags": ["辣", "米饭"],
            "weather_fit": ["雨"],
            "available_time": ["午餐"],
            "popularity": 10,
        }
        plain = {
            "name": "测试清淡饭",
            "price": 35,
            "tags": ["清淡"],
            "weather_fit": ["晴"],
            "available_time": ["晚餐"],
            "popularity": 10,
        }
        prefs = {"taste": "辣", "budget": 25, "weather": "雨", "scene": "午餐", "avoid": "无"}
        self.assertGreater(score_dish(spicy, prefs), score_dish(plain, prefs))


if __name__ == "__main__":
    unittest.main()
