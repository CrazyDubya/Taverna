"""Tests for the event formatter system."""

import pytest
from unittest.mock import MagicMock
from core.event_formatter import EventFormatter
from core.npc import NPC


def test_event_formatter_initialization():
    """Test that the event formatter initializes correctly."""
    formatter = EventFormatter()
    assert formatter.recent_events == []
    assert 'rent_success' in formatter._event_templates
    assert 'sleep_success' in formatter._event_templates
    assert 'gamble_win' in formatter._event_templates
    assert 'npc_spawn' in formatter._event_templates


def test_add_event():
    """Test adding events to the formatter."""
    formatter = EventFormatter()
    formatter.add_event('rent_success', amount=5, room_id=101)

    assert len(formatter.recent_events) == 1
    event = formatter.recent_events[0]
    assert event['type'] == 'rent_success'
    assert event['data'] == {'amount': 5, 'room_id': 101}
    assert 'timestamp' in event


def test_get_formatted_events():
    """Test getting formatted event messages."""
    formatter = EventFormatter()
    formatter.add_event('rent_success', amount=5, room_id=101)
    formatter.add_event('npc_spawn', npc_name='Gandalf', npc_id='npc_1')

    formatted = formatter.get_formatted_events()

    assert len(formatted) == 2
    assert any('5' in msg and 'gold' in msg for msg in formatted)
    assert any('Gandalf' in msg for msg in formatted)

    # Events should be cleared after getting them
    assert len(formatter.recent_events) == 0


def test_clear_events():
    """Test clearing events."""
    formatter = EventFormatter()
    formatter.add_event('rent_success', amount=5, room_id=101)

    assert len(formatter.recent_events) == 1
    formatter.clear_events()
    assert len(formatter.recent_events) == 0


def test_npc_event_formatting():
    """Test formatting of NPC-related events."""
    formatter = EventFormatter()
    npc = MagicMock()
    npc.name = 'Gandalf'
    npc.id = 'npc_1'

    # Test NPC spawn
    formatter.add_event('npc_spawn', npc_name=npc.name, npc_id=npc.id, location='tavern')
    formatted = formatter.get_formatted_events()
    assert any('Gandalf' in msg for msg in formatted)

    # Test NPC depart
    formatter.add_event('npc_depart', npc_name=npc.name, npc_id=npc.id, reason='tired')
    formatted = formatter.get_formatted_events()
    assert any('Gandalf' in msg for msg in formatted)
    # Check for any departure-related words in the message
    assert any(any(word in msg.lower()
               for word in ['leave', 'depart', 'out', 'goes']) for msg in formatted)


def test_gambling_event_formatting():
    """Test formatting of gambling-related events."""
    formatter = EventFormatter()

    # Test gambling win
    formatter.add_event('gamble_win', amount=10, game='dice')
    formatted = formatter.get_formatted_events()
    assert any('10' in msg and 'gold' in msg for msg in formatted)
    assert any('dice' in msg for msg in formatted)

    # Test gambling loss
    formatter.add_event('gamble_lose', amount=5, game='blackjack')
    formatted = formatter.get_formatted_events()
    assert any('5' in msg and 'gold' in msg for msg in formatted)
    assert any('blackjack' in msg.lower() for msg in formatted)
