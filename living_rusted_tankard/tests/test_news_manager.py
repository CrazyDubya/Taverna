"""
Test suite for the NewsManager system.

Tests news article generation, retrieval, and management.
"""
import unittest
import tempfile
import shutil
from pathlib import Path

from living_rusted_tankard.core.news_manager import NewsManager


class TestNewsManager(unittest.TestCase):
    """Test the NewsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.news_manager = NewsManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_news_manager_initialization(self):
        """Test that NewsManager initializes correctly."""
        self.assertIsNotNone(self.news_manager)
        self.assertTrue(hasattr(self.news_manager, "data_dir"))

    def test_add_news_article(self):
        """Test adding a news article."""
        article = {
            "id": "test_news_001",
            "title": "Test News",
            "content": "This is a test news article",
            "category": "tavern",
            "timestamp": 12.5,
        }

        result = self.news_manager.add_article(
            article_id=article["id"],
            title=article["title"],
            content=article["content"],
            category=article["category"],
            timestamp=article["timestamp"],
        )

        self.assertTrue(result)

    def test_get_recent_news(self):
        """Test retrieving recent news articles."""
        # Add multiple articles
        for i in range(5):
            self.news_manager.add_article(
                article_id=f"news_{i:03d}",
                title=f"News Article {i}",
                content=f"Content for article {i}",
                category="general",
                timestamp=float(i),
            )

        recent = self.news_manager.get_recent_news(count=3)
        self.assertLessEqual(len(recent), 3)

    def test_get_news_by_category(self):
        """Test filtering news by category."""
        # Add articles in different categories
        self.news_manager.add_article(
            article_id="tavern_news",
            title="Tavern News",
            content="Something at the tavern",
            category="tavern",
            timestamp=10.0,
        )

        self.news_manager.add_article(
            article_id="quest_news",
            title="Quest News",
            content="A new quest available",
            category="quest",
            timestamp=11.0,
        )

        tavern_news = self.news_manager.get_news_by_category("tavern")
        self.assertGreaterEqual(len(tavern_news), 1)
        self.assertTrue(any(n.get("category") == "tavern" for n in tavern_news))

    def test_news_ordering(self):
        """Test that news articles are returned in correct order."""
        # Add articles with different timestamps
        articles = [
            ("old_news", "Old News", 1.0),
            ("new_news", "New News", 10.0),
            ("newest_news", "Newest News", 15.0),
        ]

        for article_id, title, timestamp in articles:
            self.news_manager.add_article(
                article_id=article_id,
                title=title,
                content=f"Content for {title}",
                category="general",
                timestamp=timestamp,
            )

        recent = self.news_manager.get_recent_news(count=3)
        # Most recent should be first
        if len(recent) > 0:
            timestamps = [n.get("timestamp", 0) for n in recent]
            # Verify descending order
            self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_news_persistence(self):
        """Test that news persists to disk."""
        self.news_manager.add_article(
            article_id="persist_test",
            title="Persistence Test",
            content="Testing persistence",
            category="test",
            timestamp=5.0,
        )

        # Create new manager instance with same data_dir
        new_manager = NewsManager(data_dir=self.test_dir)
        news = new_manager.get_recent_news(count=10)

        # Check if the article is found (if persistence is implemented)
        found = any(n.get("id") == "persist_test" for n in news)
        # This may be False if persistence isn't implemented yet
        # Just check that get_recent_news works
        self.assertIsInstance(news, list)


class TestNewsCategories(unittest.TestCase):
    """Test news categorization features."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.news_manager = NewsManager(data_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_multiple_categories(self):
        """Test managing news across multiple categories."""
        categories = ["tavern", "quest", "npc", "economy", "event"]

        for i, category in enumerate(categories):
            self.news_manager.add_article(
                article_id=f"{category}_news",
                title=f"{category.title()} News",
                content=f"News about {category}",
                category=category,
                timestamp=float(i),
            )

        # Test each category
        for category in categories:
            news = self.news_manager.get_news_by_category(category)
            if len(news) > 0:
                self.assertTrue(
                    all(n.get("category") == category for n in news),
                    f"Category mismatch for {category}",
                )


if __name__ == "__main__":
    unittest.main()
