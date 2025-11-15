"""
Narrative Persistence System.
Saves and loads all narrative state to ensure continuity across game sessions.
"""

import json
import pickle
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import gzip

logger = logging.getLogger(__name__)


class SerializationFormat(Enum):
    """Different serialization formats for narrative data."""

    JSON = "json"  # Human-readable, version-safe
    PICKLE = "pickle"  # Python-native, compact
    COMPRESSED = "compressed"  # Gzipped JSON for space efficiency


class NarrativePersistenceManager:
    """Manages saving and loading of all narrative system state."""

    def __init__(self, save_directory: str = "narrative_saves"):
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(exist_ok=True)

        # Save configuration
        self.auto_save_interval = 300.0  # 5 minutes
        self.last_auto_save = time.time()
        self.max_save_files = 10  # Keep this many backups

        # Serialization settings
        self.default_format = SerializationFormat.COMPRESSED
        self.include_debug_info = False

        # Component state tracking
        self.components_to_save: Dict[str, Any] = {}
        self.save_enabled = True

    def register_component(self, component_name: str, component_instance: Any):
        """Register a narrative component for automatic saving."""
        self.components_to_save[component_name] = component_instance
        logger.debug(f"Registered narrative component: {component_name}")

    def save_all_narrative_state(self, session_id: str, save_format: SerializationFormat = None) -> bool:
        """Save all registered narrative components."""
        if not self.save_enabled:
            return False

        save_format = save_format or self.default_format
        timestamp = int(time.time())
        filename = f"narrative_state_{session_id}_{timestamp}.{save_format.value}"
        filepath = self.save_directory / filename

        try:
            # Collect all component states
            narrative_state = {
                "metadata": {
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "save_format": save_format.value,
                    "version": "1.0",
                    "components": list(self.components_to_save.keys()),
                },
                "components": {},
            }

            # Save each component
            for component_name, component in self.components_to_save.items():
                try:
                    component_state = self._serialize_component(component, component_name)
                    narrative_state["components"][component_name] = component_state
                    logger.debug(f"Serialized component: {component_name}")
                except Exception as e:
                    logger.error(f"Failed to serialize component {component_name}: {e}")
                    narrative_state["components"][component_name] = {"error": str(e), "timestamp": timestamp}

            # Write to file
            success = self._write_narrative_file(narrative_state, filepath, save_format)

            if success:
                logger.info(f"Saved narrative state to {filepath}")
                self._cleanup_old_saves(session_id)
                return True
            else:
                logger.error(f"Failed to write narrative state to {filepath}")
                return False

        except Exception as e:
            logger.error(f"Error saving narrative state: {e}")
            return False

    def load_narrative_state(self, session_id: str, specific_timestamp: Optional[int] = None) -> bool:
        """Load narrative state from the most recent save or specific timestamp."""
        try:
            # Find the save file to load
            if specific_timestamp:
                pattern = f"narrative_state_{session_id}_{specific_timestamp}.*"
            else:
                pattern = f"narrative_state_{session_id}_*"

            matching_files = list(self.save_directory.glob(pattern))

            if not matching_files:
                logger.warning(f"No narrative save files found for session {session_id}")
                return False

            # Sort by timestamp (newest first)
            if not specific_timestamp:
                matching_files.sort(key=lambda f: self._extract_timestamp_from_filename(f.name), reverse=True)

            load_file = matching_files[0]
            logger.info(f"Loading narrative state from {load_file}")

            # Determine format from file extension
            save_format = SerializationFormat(load_file.suffix.lstrip("."))

            # Load the narrative state
            narrative_state = self._read_narrative_file(load_file, save_format)

            if not narrative_state:
                logger.error(f"Failed to read narrative state from {load_file}")
                return False

            # Restore each component
            loaded_components = 0
            for component_name, component_state in narrative_state.get("components", {}).items():
                if component_name in self.components_to_save:
                    try:
                        self._deserialize_component(
                            self.components_to_save[component_name], component_state, component_name
                        )
                        loaded_components += 1
                        logger.debug(f"Restored component: {component_name}")
                    except Exception as e:
                        logger.error(f"Failed to restore component {component_name}: {e}")
                else:
                    logger.warning(f"Component {component_name} not registered for loading")

            logger.info(f"Loaded {loaded_components} narrative components")
            return loaded_components > 0

        except Exception as e:
            logger.error(f"Error loading narrative state: {e}")
            return False

    def _serialize_component(self, component: Any, component_name: str) -> Dict[str, Any]:
        """Serialize a narrative component to a dictionary."""
        component_data = {"component_type": type(component).__name__, "timestamp": time.time()}

        # Handle different component types
        if component_name == "character_memory_manager":
            component_data["memories"] = {}
            for npc_id, memory in component.character_memories.items():
                component_data["memories"][npc_id] = memory.to_dict()

        elif component_name == "character_state_manager":
            component_data["states"] = {}
            for npc_id, state in component.character_states.items():
                component_data["states"][npc_id] = self._serialize_character_state(state)

        elif component_name == "personality_manager":
            component_data["personalities"] = {}
            for npc_id, personality in component.personalities.items():
                component_data["personalities"][npc_id] = self._serialize_personality(personality)

        elif component_name == "schedule_manager":
            component_data["schedules"] = {}
            for npc_id, schedule in component.schedules.items():
                component_data["schedules"][npc_id] = self._serialize_schedule(schedule)

        elif component_name == "reputation_network":
            component_data["npc_reputations"] = {}
            for npc_id, reputation in component.npc_reputations.items():
                component_data["npc_reputations"][npc_id] = self._serialize_reputation(reputation)

            component_data["social_connections"] = {}
            for connection_key, connection in component.social_connections.items():
                component_data["social_connections"][str(connection_key)] = self._serialize_social_connection(
                    connection
                )

        elif component_name == "conversation_manager":
            component_data["conversation_memories"] = {}
            for npc_id, conv_memory in component.conversation_memories.items():
                component_data["conversation_memories"][npc_id] = self._serialize_conversation_memory(conv_memory)

        elif component_name == "story_orchestrator":
            component_data["story_threads"] = {}
            for thread_id, thread in component.story_threads.items():
                component_data["story_threads"][thread_id] = self._serialize_story_thread(thread)

            component_data["current_arc"] = (
                self._serialize_narrative_arc(component.current_arc) if component.current_arc else None
            )
            component_data["overall_tension"] = component.overall_tension
            component_data["current_pacing"] = component.current_pacing.value
            component_data["player_engagement_score"] = component.player_engagement_score

            # Save recent story moments
            component_data["story_moments"] = [
                self._serialize_story_moment(moment) for moment in component.story_moments[-50:]
            ]

        elif component_name == "quest_generator":
            component_data["active_quests"] = {}
            for quest_id, quest in component.active_quests.items():
                component_data["active_quests"][quest_id] = self._serialize_quest(quest)

            component_data["completed_quests"] = {}
            for quest_id, quest in component.completed_quests.items():
                component_data["completed_quests"][quest_id] = self._serialize_quest(quest)

            component_data["statistics"] = {
                "total_quests_generated": component.total_quests_generated,
                "total_quests_completed": component.total_quests_completed,
                "player_quest_preferences": component.player_quest_preferences,
            }

        elif component_name == "consequence_engine":
            component_data["tracked_actions"] = {}
            for action_id, action in component.tracked_actions.items():
                component_data["tracked_actions"][action_id] = self._serialize_tracked_action(action)

            component_data["pending_consequences"] = {}
            for consequence_id, consequence in component.pending_consequences.items():
                component_data["pending_consequences"][consequence_id] = self._serialize_consequence(consequence)

            component_data["statistics"] = {
                "total_actions_tracked": component.total_actions_tracked,
                "total_consequences_triggered": component.total_consequences_triggered,
            }

        else:
            # Generic serialization for unknown components
            try:
                if hasattr(component, "__dict__"):
                    component_data["attributes"] = self._serialize_object_dict(component.__dict__)
                else:
                    component_data["value"] = str(component)
            except Exception as e:
                logger.warning(f"Could not serialize component {component_name}: {e}")
                component_data["error"] = str(e)

        return component_data

    def _deserialize_component(self, component: Any, component_data: Dict[str, Any], component_name: str):
        """Deserialize component data back into the component instance."""

        if component_name == "character_memory_manager":
            component.character_memories.clear()
            for npc_id, memory_data in component_data.get("memories", {}).items():
                from .character_memory import CharacterMemory

                component.character_memories[npc_id] = CharacterMemory.from_dict(memory_data)

        elif component_name == "character_state_manager":
            component.character_states.clear()
            for npc_id, state_data in component_data.get("states", {}).items():
                state = self._deserialize_character_state(state_data)
                if state:
                    component.character_states[npc_id] = state

        elif component_name == "personality_manager":
            component.personalities.clear()
            for npc_id, personality_data in component_data.get("personalities", {}).items():
                personality = self._deserialize_personality(personality_data)
                if personality:
                    component.personalities[npc_id] = personality

        elif component_name == "schedule_manager":
            component.schedules.clear()
            for npc_id, schedule_data in component_data.get("schedules", {}).items():
                schedule = self._deserialize_schedule(schedule_data)
                if schedule:
                    component.schedules[npc_id] = schedule

        elif component_name == "reputation_network":
            component.npc_reputations.clear()
            for npc_id, reputation_data in component_data.get("npc_reputations", {}).items():
                reputation = self._deserialize_reputation(reputation_data)
                if reputation:
                    component.npc_reputations[npc_id] = reputation

            component.social_connections.clear()
            for connection_key_str, connection_data in component_data.get("social_connections", {}).items():
                connection = self._deserialize_social_connection(connection_data)
                if connection:
                    # Convert string key back to tuple
                    connection_key = eval(connection_key_str)  # Safe since we control the format
                    component.social_connections[connection_key] = connection

        elif component_name == "conversation_manager":
            component.conversation_memories.clear()
            for npc_id, conv_data in component_data.get("conversation_memories", {}).items():
                conv_memory = self._deserialize_conversation_memory(conv_data)
                if conv_memory:
                    component.conversation_memories[npc_id] = conv_memory

        elif component_name == "story_orchestrator":
            component.story_threads.clear()
            for thread_id, thread_data in component_data.get("story_threads", {}).items():
                thread = self._deserialize_story_thread(thread_data)
                if thread:
                    component.story_threads[thread_id] = thread

            if component_data.get("current_arc"):
                component.current_arc = self._deserialize_narrative_arc(component_data["current_arc"])

            component.overall_tension = component_data.get("overall_tension", 0.0)
            component.player_engagement_score = component_data.get("player_engagement_score", 0.5)

            # Restore pacing enum
            from .story_orchestrator import PacingMode

            pacing_value = component_data.get("current_pacing", "steady")
            component.current_pacing = PacingMode(pacing_value)

            # Restore story moments
            component.story_moments.clear()
            for moment_data in component_data.get("story_moments", []):
                moment = self._deserialize_story_moment(moment_data)
                if moment:
                    component.story_moments.append(moment)

        elif component_name == "quest_generator":
            component.active_quests.clear()
            for quest_id, quest_data in component_data.get("active_quests", {}).items():
                quest = self._deserialize_quest(quest_data)
                if quest:
                    component.active_quests[quest_id] = quest

            component.completed_quests.clear()
            for quest_id, quest_data in component_data.get("completed_quests", {}).items():
                quest = self._deserialize_quest(quest_data)
                if quest:
                    component.completed_quests[quest_id] = quest

            # Restore statistics
            stats = component_data.get("statistics", {})
            component.total_quests_generated = stats.get("total_quests_generated", 0)
            component.total_quests_completed = stats.get("total_quests_completed", 0)
            component.player_quest_preferences = stats.get("player_quest_preferences", {})

        elif component_name == "consequence_engine":
            component.tracked_actions.clear()
            for action_id, action_data in component_data.get("tracked_actions", {}).items():
                action = self._deserialize_tracked_action(action_data)
                if action:
                    component.tracked_actions[action_id] = action

            component.pending_consequences.clear()
            for consequence_id, consequence_data in component_data.get("pending_consequences", {}).items():
                consequence = self._deserialize_consequence(consequence_data)
                if consequence:
                    component.pending_consequences[consequence_id] = consequence

            # Restore statistics
            stats = component_data.get("statistics", {})
            component.total_actions_tracked = stats.get("total_actions_tracked", 0)
            component.total_consequences_triggered = stats.get("total_consequences_triggered", 0)

        else:
            # Generic deserialization
            if "attributes" in component_data and hasattr(component, "__dict__"):
                self._deserialize_object_dict(component.__dict__, component_data["attributes"])

    # Serialization helper methods for specific data types
    def _serialize_character_state(self, state) -> Dict[str, Any]:
        """Serialize a character state object."""
        return {
            "npc_id": state.npc_id,
            "npc_name": state.npc_name,
            "mood": state.mood.value,
            "energy": state.energy,
            "stress": state.stress,
            "concerns": [self._serialize_concern(concern) for concern in state.concerns],
            "goals": [self._serialize_goal(goal) for goal in state.goals],
            "is_busy": state.is_busy,
            "busy_reason": state.busy_reason,
            "busy_until": state.busy_until.timestamp() if state.busy_until else None,
        }

    def _deserialize_character_state(self, data: Dict[str, Any]):
        """Deserialize character state data."""
        try:
            from .character_state import CharacterState, Mood
            from datetime import datetime

            state = CharacterState(data["npc_id"], data["npc_name"], {})
            state.mood = Mood(data["mood"])
            state.energy = data["energy"]
            state.stress = data["stress"]
            state.is_busy = data["is_busy"]
            state.busy_reason = data["busy_reason"]

            if data["busy_until"]:
                state.busy_until = datetime.fromtimestamp(data["busy_until"])

            # Restore concerns and goals (simplified for now)
            # Full implementation would need to recreate Concern and Goal objects

            return state
        except Exception as e:
            logger.error(f"Error deserializing character state: {e}")
            return None

    def _serialize_concern(self, concern) -> Dict[str, Any]:
        """Serialize a concern object."""
        return {
            "type": concern.type.value,
            "description": concern.description,
            "intensity": concern.intensity,
            "source": concern.source,
            "created_at": concern.created_at.timestamp(),
            "expires_at": concern.expires_at.timestamp() if concern.expires_at else None,
        }

    def _serialize_goal(self, goal) -> Dict[str, Any]:
        """Serialize a goal object."""
        return {
            "description": goal.description,
            "priority": goal.priority,
            "progress": goal.progress,
            "required_actions": goal.required_actions,
            "blockers": goal.blockers,
            "created_at": goal.created_at.timestamp(),
        }

    def _serialize_object_dict(self, obj_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Generic serialization for object dictionaries."""
        serialized = {}
        for key, value in obj_dict.items():
            try:
                if isinstance(value, (str, int, float, bool, type(None))):
                    serialized[key] = value
                elif isinstance(value, (list, tuple)):
                    serialized[key] = [self._serialize_value(item) for item in value]
                elif isinstance(value, dict):
                    serialized[key] = {k: self._serialize_value(v) for k, v in value.items()}
                elif hasattr(value, "__dict__"):
                    serialized[key] = self._serialize_object_dict(value.__dict__)
                else:
                    serialized[key] = str(value)
            except Exception:
                serialized[key] = f"<could not serialize {type(value).__name__}>"
        return serialized

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a single value."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, Enum):
            return value.value
        elif hasattr(value, "timestamp"):  # datetime-like objects
            return value.timestamp()
        else:
            return str(value)

    def _deserialize_object_dict(self, target_dict: Dict[str, Any], source_dict: Dict[str, Any]):
        """Generic deserialization for object dictionaries."""
        for key, value in source_dict.items():
            if key in target_dict:
                target_dict[key] = value

    # Placeholder methods for complex object serialization
    # These would need full implementations based on the actual object structures

    def _serialize_personality(self, personality) -> Dict[str, Any]:
        return {"npc_id": personality.npc_id, "npc_name": personality.npc_name}

    def _deserialize_personality(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_schedule(self, schedule) -> Dict[str, Any]:
        return {"npc_id": schedule.npc_id, "npc_name": schedule.npc_name}

    def _deserialize_schedule(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_reputation(self, reputation) -> Dict[str, Any]:
        return {"npc_id": reputation.npc_id, "npc_name": reputation.npc_name}

    def _deserialize_reputation(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_social_connection(self, connection) -> Dict[str, Any]:
        return {"npc1_id": connection.npc1_id, "npc2_id": connection.npc2_id}

    def _deserialize_social_connection(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_conversation_memory(self, conv_memory) -> Dict[str, Any]:
        return {"npc_id": conv_memory.npc_id, "npc_name": conv_memory.npc_name}

    def _deserialize_conversation_memory(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_story_thread(self, thread) -> Dict[str, Any]:
        return {"thread_id": thread.thread_id, "title": thread.title}

    def _deserialize_story_thread(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_narrative_arc(self, arc) -> Dict[str, Any]:
        return {"arc_id": arc.arc_id, "title": arc.title}

    def _deserialize_narrative_arc(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_story_moment(self, moment) -> Dict[str, Any]:
        return {
            "moment_id": moment.moment_id,
            "timestamp": moment.timestamp,
            "description": moment.description,
            "emotional_impact": moment.emotional_impact,
        }

    def _deserialize_story_moment(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_quest(self, quest) -> Dict[str, Any]:
        return {"quest_id": quest.quest_id, "title": quest.title}

    def _deserialize_quest(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_tracked_action(self, action) -> Dict[str, Any]:
        return {"action_id": action.action_id, "timestamp": action.timestamp, "description": action.description}

    def _deserialize_tracked_action(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _serialize_consequence(self, consequence) -> Dict[str, Any]:
        return {"consequence_id": consequence.consequence_id, "description": consequence.description}

    def _deserialize_consequence(self, data: Dict[str, Any]):
        return None  # Would need full implementation

    def _write_narrative_file(self, data: Dict[str, Any], filepath: Path, save_format: SerializationFormat) -> bool:
        """Write narrative data to file in the specified format."""
        try:
            if save_format == SerializationFormat.JSON:
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2, default=str)

            elif save_format == SerializationFormat.PICKLE:
                with open(filepath, "wb") as f:
                    pickle.dump(data, f)

            elif save_format == SerializationFormat.COMPRESSED:
                json_data = json.dumps(data, default=str).encode("utf-8")
                with gzip.open(filepath, "wb") as f:
                    f.write(json_data)

            return True
        except Exception as e:
            logger.error(f"Error writing narrative file {filepath}: {e}")
            return False

    def _read_narrative_file(self, filepath: Path, save_format: SerializationFormat) -> Optional[Dict[str, Any]]:
        """Read narrative data from file."""
        try:
            if save_format == SerializationFormat.JSON:
                with open(filepath, "r") as f:
                    return json.load(f)

            elif save_format == SerializationFormat.PICKLE:
                with open(filepath, "rb") as f:
                    return pickle.load(f)

            elif save_format == SerializationFormat.COMPRESSED:
                with gzip.open(filepath, "rb") as f:
                    json_data = f.read().decode("utf-8")
                    return json.loads(json_data)

            return None
        except Exception as e:
            logger.error(f"Error reading narrative file {filepath}: {e}")
            return None

    def _extract_timestamp_from_filename(self, filename: str) -> int:
        """Extract timestamp from narrative save filename."""
        try:
            parts = filename.split("_")
            timestamp_part = parts[2].split(".")[0]  # Remove extension
            return int(timestamp_part)
        except (IndexError, ValueError):
            return 0

    def _cleanup_old_saves(self, session_id: str):
        """Remove old save files, keeping only the most recent ones."""
        pattern = f"narrative_state_{session_id}_*"
        matching_files = list(self.save_directory.glob(pattern))

        if len(matching_files) > self.max_save_files:
            # Sort by timestamp and remove oldest
            matching_files.sort(key=lambda f: self._extract_timestamp_from_filename(f.name))
            files_to_remove = matching_files[: -self.max_save_files]

            for file_to_remove in files_to_remove:
                try:
                    file_to_remove.unlink()
                    logger.debug(f"Removed old save file: {file_to_remove}")
                except Exception as e:
                    logger.warning(f"Could not remove old save file {file_to_remove}: {e}")

    def should_auto_save(self) -> bool:
        """Check if it's time for an automatic save."""
        return (time.time() - self.last_auto_save) >= self.auto_save_interval

    def get_save_file_list(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available save files."""
        if session_id:
            pattern = f"narrative_state_{session_id}_*"
        else:
            pattern = "narrative_state_*"

        save_files = []
        for filepath in self.save_directory.glob(pattern):
            try:
                timestamp = self._extract_timestamp_from_filename(filepath.name)
                save_files.append(
                    {
                        "filename": filepath.name,
                        "timestamp": timestamp,
                        "age_hours": (time.time() - timestamp) / 3600.0,
                        "size_bytes": filepath.stat().st_size,
                    }
                )
            except Exception as e:
                logger.warning(f"Could not process save file {filepath}: {e}")

        # Sort by timestamp (newest first)
        save_files.sort(key=lambda x: x["timestamp"], reverse=True)
        return save_files

    def delete_save_file(self, filename: str) -> bool:
        """Delete a specific save file."""
        filepath = self.save_directory / filename
        try:
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted save file: {filename}")
                return True
            else:
                logger.warning(f"Save file not found: {filename}")
                return False
        except Exception as e:
            logger.error(f"Error deleting save file {filename}: {e}")
            return False
