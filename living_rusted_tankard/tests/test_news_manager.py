"""
Test suite for the NewsManager system.

Tests news item loading, filtering, and retrieval.
"""
import unittest
import tempfile
import shutil
import json
from pathlib import Path

from living_rusted_tankard.core.news_manager import NewsManager, NewsItem


class TestNewsManager(unittest.TestCase):
    """Test the NewsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.create_test_news_file()
        self.news_manager = NewsManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_news_file(self):
        """Create a test news.json file."""
        news_data = {
            "news_items": [
                {
                    "id": "tavern_news_001",
                    "text": "The tavern is bustling with activity tonight.",
                    "source_types": ["bartender", "patron"],
                },
                {
                    "id": "quest_news_001",
                    "text": "There's a bounty posted for wolf pelts.",
                    "source_types": ["guard", "merchant"],
                    "conditions": {"min_day": 5},
                },
            ]
        }

        news_file = Path(self.test_dir) / "news.json"
        with open(news_file, "w") as f:
            json.dump(news_data, f)

    def test_news_manager_initialization(self):
        """Test that NewsManager initializes correctly."""
        self.assertIsNotNone(self.news_manager)
        self.assertIsInstance(self.news_manager.news_items, list)

    def test_news_items_loaded(self):
        """Test that news items are loaded from file."""
        self.assertGreater(len(self.news_manager.news_items), 0)
        self.assertEqual(len(self.news_manager.news_items), 2)

    def test_get_relevant_news(self):
        """Test getting relevant news for an NPC type."""
        # Get news for bartender
        relevant = self.news_manager.get_relevant_news(
            npc_type_str="bartender", current_day=1
        )
        
        self.assertGreater(len(relevant), 0)
        self.assertTrue(any(item.id == "tavern_news_001" for item in relevant))

    def test_news_filtering_by_npc_type(self):
        """Test that news is filtered by NPC type."""
        # Bartender should see tavern news
        bartender_news = self.news_manager.get_relevant_news(
            npc_type_str="bartender", current_day=1
        )
        self.assertTrue(any("tavern" in item.text.lower() for item in bartender_news))

        # Guard should see quest news
        guard_news = self.news_manager.get_relevant_news(
            npc_type_str="guard", current_day=10
        )
        self.assertTrue(any("bounty" in item.text.lower() for item in guard_news))

    def test_news_day_condition(self):
        """Test that news respects day conditions."""
        # Day 1 - should not see quest news (requires min_day: 5)
        early_news = self.news_manager.get_relevant_news(
            npc_type_str="guard", current_day=1
        )
        quest_news = [item for item in early_news if "bounty" in item.text.lower()]
        self.assertEqual(len(quest_news), 0)

        # Day 10 - should see quest news
        later_news = self.news_manager.get_relevant_news(
            npc_type_str="guard", current_day=10
        )
        quest_news = [item for item in later_news if "bounty" in item.text.lower()]
        self.assertGreater(len(quest_news), 0)

    def test_get_random_news_snippet(self):
        """Test getting a random news snippet."""
        snippet = self.news_manager.get_random_news_snippet(
            npc_type_str="bartender", current_day=1
        )
        
        self.assertIsNotNone(snippet)
        self.assertIsInstance(snippet, NewsItem)

    def test_random_news_excludes_recently_shared(self):
        """Test that random news excludes recently shared IDs."""
        recently_shared = ["tavern_news_001"]
        
        snippet = self.news_manager.get_random_news_snippet(
            npc_type_str="bartender",
            current_day=1,
            recently_shared_ids=recently_shared,
        )
        
        if snippet:  # May be None if all news was recently shared
            self.assertNotIn(snippet.id, recently_shared)


class TestNewsItem(unittest.TestCase):
    """Test the NewsItem class."""

    def test_news_item_creation(self):
        """Test creating a news item."""
        item = NewsItem(
            id="test_news",
            text="Test news content",
            source_types=["bartender"],
        )

        self.assertEqual(item.id, "test_news")
        self.assertEqual(item.text, "Test news content")
        self.assertIn("bartender", item.source_types)

    def test_news_item_with_conditions(self):
        """Test news item with conditions."""
        from living_rusted_tankard.core.news_manager import NewsItemCondition

        conditions = NewsItemCondition(min_day=10, requires_event="festival")
        item = NewsItem(
            id="event_news",
            text="Festival news",
            source_types=["patron"],
            conditions=conditions,
        )

        self.assertIsNotNone(item.conditions)
        self.assertEqual(item.conditions.min_day, 10)
        self.assertEqual(item.conditions.requires_event, "festival")


if __name__ == "__main__":
    unittest.main()
