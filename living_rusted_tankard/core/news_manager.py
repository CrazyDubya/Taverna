from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from pathlib import Path
import json
import random

# Assuming NPCType is defined elsewhere, e.g., in core.npc
# from .npc import NPCType
# For now, we'll assume NPCType will be passed as a string from npc.py


class NewsItemCondition(BaseModel):
    min_day: Optional[int] = None
    requires_event: Optional[str] = None
    # Could add other conditions like player reputation, quest status, etc.


class NewsItem(BaseModel):
    id: str
    text: str
    source_types: List[str]  # List of NPCType strings
    conditions: Optional[NewsItemCondition] = None


class NewsManager(BaseModel):
    news_items: List[NewsItem] = Field(default_factory=list)

    class Config:
        # Allow setting attributes that aren't fields
        extra = "allow"

    def __init__(self, data_dir: Union[str, Path] = "data", **data: Any):
        super().__init__(**data)  # For Pydantic model fields if any are passed via data
        self._data_dir = Path(data_dir)
        self._loaded = False  # Initialize _loaded
        self._load_news_items()

    def _load_news_items(self) -> None:
        if self._loaded:  # Prevent reloading if already loaded
            return

        news_file = self._data_dir / "news.json"
        if not news_file.exists():
            print(f"Warning: News data file not found at {news_file}. No news items loaded.")
            self.news_items = []
            self._loaded = True
            return

        try:
            with open(news_file, "r") as f:
                data = json.load(f)

            loaded_items = []
            for item_data in data.get("news_items", []):
                # Parse conditions if present
                conditions_data = item_data.get("conditions")
                if conditions_data:
                    item_data["conditions"] = NewsItemCondition(**conditions_data)
                else:
                    item_data["conditions"] = None  # Ensure it's None if not present

                news_item = NewsItem(**item_data)
                loaded_items.append(news_item)
            self.news_items = loaded_items
            self._loaded = True
            # print(f"DEBUG: Loaded {len(self.news_items)} news items from {news_file}")
        except json.JSONDecodeError as e:
            print(f"Error decoding news items from {news_file}: {e}")
            self.news_items = []
        except Exception as e:  # Catch other Pydantic validation errors or general issues
            print(f"Unexpected error loading news items: {e}")
            self.news_items = []
        self._loaded = True

    def get_relevant_news(
        self, npc_type_str: str, current_day: int, active_events: Optional[List[str]] = None
    ) -> List[NewsItem]:
        """
        Filters news_items based on NPC type and game conditions.

        Args:
            npc_type_str: The type of the NPC asking for news (as a string).
            current_day: The current day in the game.
            active_events: A list of active global event strings.

        Returns:
            A list of suitable NewsItem objects.
        """
        if not self._loaded:  # Ensure data is loaded
            self._load_news_items()

        if active_events is None:
            active_events = []

        relevant_snippets = []
        for item in self.news_items:
            # Check source type
            if npc_type_str not in item.source_types:
                continue

            # Check conditions
            conditions_met = True
            if item.conditions:
                if item.conditions.min_day is not None and current_day < item.conditions.min_day:
                    conditions_met = False
                if item.conditions.requires_event and item.conditions.requires_event not in active_events:
                    conditions_met = False

            if conditions_met:
                relevant_snippets.append(item)

        return relevant_snippets

    def get_random_news_snippet(
        self,
        npc_type_str: str,
        current_day: int,
        active_events: Optional[List[str]] = None,
        recently_shared_ids: Optional[List[str]] = None,
    ) -> Optional[NewsItem]:
        """
        Gets a single random, relevant news snippet that hasn't been recently shared.
        """
        relevant_news = self.get_relevant_news(npc_type_str, current_day, active_events)

        if recently_shared_ids:
            available_news = [news for news in relevant_news if news.id not in recently_shared_ids]
        else:
            available_news = relevant_news

        if not available_news:
            return None

        return random.choice(available_news)


# Example Usage (for testing purposes)
# if __name__ == "__main__":
#     # Assume NPCType enum exists for this test or use strings directly
#     # class NPCType: MERCHANT = "MERCHANT"; PATRON = "PATRON"; GUARD = "GUARD"

#     # Create a dummy news.json in a 'data' subdirectory for testing
#     test_data_dir = Path("data")
#     test_data_dir.mkdir(exist_ok=True)
#     dummy_news_file = test_data_dir / "news.json"
#     with open(dummy_news_file, "w") as f:
#         json.dump({
#             "news_items": [
#                 {
#                   "id": "news_harvest_good_01",
#                   "text": "They say the harvest in the southern valleys was plentiful this year.",
#                   "source_types": ["MERCHANT", "PATRON"],
#                   "conditions": {"min_day": 1}
#                 },
#                 {
#                   "id": "news_bandit_increase_01",
#                   "text": "Roads are bad. Bandits.",
#                   "source_types": ["MERCHANT", "GUARD"],
#                   "conditions": {"min_day": 1, "requires_event": "bandit_activity_high"}
#                 }
#             ]
#         }, f)

#     news_mgr = NewsManager(data_dir=str(test_data_dir))
#     print(f"Loaded news items: {len(news_mgr.news_items)}")

#     # Test get_relevant_news
#     merchant_news_today = news_mgr.get_relevant_news(npc_type_str="MERCHANT", current_day=5, active_events=[])
#     print(f"\nMerchant news (day 5, no events): {[item.id for item in merchant_news_today]}") # Should be harvest

#     merchant_news_with_event = news_mgr.get_relevant_news(npc_type_str="MERCHANT", current_day=5, active_events=["bandit_activity_high"])
#     print(f"Merchant news (day 5, bandit event): {[item.id for item in merchant_news_with_event]}") # Should be harvest + bandit

#     guard_news_with_event = news_mgr.get_relevant_news(npc_type_str="GUARD", current_day=5, active_events=["bandit_activity_high"])
#     print(f"Guard news (day 5, bandit event): {[item.id for item in guard_news_with_event]}") # Should be bandit

#     # Test get_random_news_snippet
#     random_snippet = news_mgr.get_random_news_snippet(npc_type_str="MERCHANT", current_day=5, active_events=["bandit_activity_high"])
#     if random_snippet:
#         print(f"\nRandom snippet for Merchant (day 5, bandit event): {random_snippet.text}")

#     # Test with recently shared
#     shared = [random_snippet.id] if random_snippet else []
#     random_snippet_filtered = news_mgr.get_random_news_snippet(npc_type_str="MERCHANT", current_day=5, active_events=["bandit_activity_high"], recently_shared_ids=shared)
#     if random_snippet_filtered:
#          print(f"Another random snippet (excluding '{shared[0]}'): {random_snippet_filtered.text}")
#     else:
#         print(f"No other news for Merchant after sharing '{shared[0]}'.")

#     # Clean up dummy file
#     # dummy_news_file.unlink()
#     # test_data_dir.rmdir() # Only if empty and created by this test
# pass
