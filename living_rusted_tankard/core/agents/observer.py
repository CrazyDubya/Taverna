"""
Agent Observer - Tools for studying deep agent behavior.

Provides:
- Real-time monitoring of agent internal state
- Decision trace logging
- Behavioral pattern analysis
- Emergence detection

This is essential for understanding and debugging agent behavior.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import time
import json
from pathlib import Path

from .agent import DeepAgent


@dataclass
class DecisionTrace:
    """
    Record of a single decision made by an agent.

    Captures the full context: what the agent perceived, believed,
    felt, needed, and why they chose the action they did.
    """

    timestamp: float
    game_time: float

    # What led to this decision
    active_needs: List[str]
    emotional_state: Dict[str, Any]
    active_goal: Optional[str]
    beliefs_considered: List[str]
    memories_recalled: List[str]

    # The decision
    action_taken: str
    reasoning: str

    # The outcome
    outcome: Optional[Dict[str, Any]] = None
    outcome_timestamp: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "game_time": self.game_time,
            "active_needs": self.active_needs,
            "emotional_state": self.emotional_state,
            "active_goal": self.active_goal,
            "beliefs_considered": self.beliefs_considered,
            "memories_recalled": self.memories_recalled,
            "action_taken": self.action_taken,
            "reasoning": self.reasoning,
            "outcome": self.outcome,
            "outcome_timestamp": self.outcome_timestamp,
        }


class AgentObserver:
    """
    Observer for studying agent behavior over time.

    Records decision traces, internal state changes, and
    emergent patterns.
    """

    def __init__(self, agent: DeepAgent, log_dir: Optional[Path] = None):
        self.agent = agent
        self.log_dir = log_dir or Path("./agent_logs")
        self.log_dir.mkdir(exist_ok=True)

        # Decision history
        self.decision_traces: List[DecisionTrace] = []

        # State snapshots
        self.state_snapshots: List[Dict[str, Any]] = []
        self.snapshot_interval = 10  # Snapshot every 10 decisions

        # Session start
        self.session_start = time.time()

    def record_decision(
        self,
        action_taken: str,
        reasoning: str,
        beliefs_considered: Optional[List[str]] = None,
        memories_recalled: Optional[List[str]] = None,
    ) -> DecisionTrace:
        """Record a decision made by the agent."""
        state = self.agent.get_internal_state_summary()

        trace = DecisionTrace(
            timestamp=time.time(),
            game_time=self.agent.game_time,
            active_needs=state["urgent_needs"],
            emotional_state=state["emotional_state"],
            active_goal=state["active_goal"],
            beliefs_considered=beliefs_considered or [],
            memories_recalled=memories_recalled or [],
            action_taken=action_taken,
            reasoning=reasoning,
        )

        self.decision_traces.append(trace)

        # Periodic snapshots
        if len(self.decision_traces) % self.snapshot_interval == 0:
            self.take_snapshot()

        return trace

    def record_outcome(self, trace_index: int, outcome: Dict[str, Any]) -> None:
        """Record the outcome of a decision."""
        if 0 <= trace_index < len(self.decision_traces):
            self.decision_traces[trace_index].outcome = outcome
            self.decision_traces[trace_index].outcome_timestamp = time.time()

    def take_snapshot(self) -> Dict[str, Any]:
        """Take a complete snapshot of agent state."""
        snapshot = {
            "timestamp": time.time(),
            "game_time": self.agent.game_time,
            "state": self.agent.get_internal_state_summary(),
            "full_state": self.agent.to_dict(),
        }

        self.state_snapshots.append(snapshot)
        return snapshot

    def get_recent_decisions(self, count: int = 10) -> List[DecisionTrace]:
        """Get the most recent decisions."""
        return self.decision_traces[-count:]

    def analyze_decision_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in decision-making.

        Returns insights about how the agent behaves.
        """
        if not self.decision_traces:
            return {"error": "No decisions recorded yet"}

        total_decisions = len(self.decision_traces)

        # Count decisions by active goal
        decisions_by_goal = {}
        for trace in self.decision_traces:
            goal = trace.active_goal or "idle"
            decisions_by_goal[goal] = decisions_by_goal.get(goal, 0) + 1

        # Count decisions by dominant emotion
        decisions_by_emotion = {}
        for trace in self.decision_traces:
            emotion = trace.emotional_state.get("dominant_emotion", "neutral")
            decisions_by_emotion[emotion] = decisions_by_emotion.get(emotion, 0) + 1

        # Identify need-driven vs goal-driven decisions
        need_driven = sum(
            1 for trace in self.decision_traces if len(trace.active_needs) > 0
        )

        # Success rate (if outcomes recorded)
        outcomes_recorded = sum(
            1 for trace in self.decision_traces if trace.outcome is not None
        )
        successful_outcomes = sum(
            1
            for trace in self.decision_traces
            if trace.outcome and trace.outcome.get("success", False)
        )

        return {
            "total_decisions": total_decisions,
            "decisions_by_goal": decisions_by_goal,
            "decisions_by_emotion": decisions_by_emotion,
            "need_driven_ratio": need_driven / total_decisions if total_decisions > 0 else 0,
            "outcomes_recorded": outcomes_recorded,
            "success_rate": (
                successful_outcomes / outcomes_recorded if outcomes_recorded > 0 else 0
            ),
        }

    def detect_behavioral_loops(self, window: int = 10) -> List[Dict[str, Any]]:
        """
        Detect if the agent is stuck in repetitive behavior.

        Returns list of detected loops.
        """
        loops = []

        if len(self.decision_traces) < window * 2:
            return loops

        # Simple pattern detection: same action repeated
        recent_actions = [trace.action_taken for trace in self.decision_traces[-window:]]

        # Check for exact repetition
        unique_actions = len(set(recent_actions))
        if unique_actions <= 2:  # Only 1-2 unique actions in window
            loops.append(
                {
                    "type": "action_repetition",
                    "actions": list(set(recent_actions)),
                    "frequency": window / unique_actions,
                    "severity": "high" if unique_actions == 1 else "medium",
                }
            )

        return loops

    def generate_narrative_summary(self, window: int = 20) -> str:
        """
        Generate human-readable summary of recent agent behavior.

        This tells a story about what the agent has been doing.
        """
        recent = self.get_recent_decisions(window)

        if not recent:
            return f"{self.agent.name} has not made any decisions yet."

        # Get the agent's current state
        state = self.agent.get_internal_state_summary()

        # Build narrative
        narrative = []

        narrative.append(f"=== {self.agent.name}'s Recent Story ===\n")

        narrative.append(f"Current Mood: {state['emotional_state']['mood']}")
        narrative.append(f"Wellbeing: {state['wellbeing']:.0%}")

        if state['active_goal']:
            narrative.append(f"Currently Pursuing: {state['active_goal']}")

        if state['urgent_needs']:
            narrative.append(
                f"Pressing Needs: {', '.join(state['urgent_needs'])}"
            )

        narrative.append(f"\nLast {len(recent)} Actions:")

        for i, trace in enumerate(recent[-10:], 1):  # Show last 10
            emotion = trace.emotional_state.get("dominant_emotion", "neutral")
            narrative.append(
                f"{i}. While feeling {emotion}, {self.agent.name} decided to:"
            )
            narrative.append(f"   {trace.reasoning}")
            narrative.append(f"   Action: {trace.action_taken}")

            if trace.outcome:
                success = "successfully" if trace.outcome.get("success") else "unsuccessfully"
                narrative.append(f"   Outcome: {success} completed")

            narrative.append("")

        # Analyze patterns
        patterns = self.analyze_decision_patterns()
        most_common_goal = max(
            patterns["decisions_by_goal"].items(), key=lambda x: x[1]
        )[0]

        narrative.append(f"\nBehavioral Patterns:")
        narrative.append(
            f"- Most Common Goal: {most_common_goal} "
            f"({patterns['decisions_by_goal'][most_common_goal]} times)"
        )
        narrative.append(
            f"- Need-Driven Decisions: {patterns['need_driven_ratio']:.0%}"
        )

        if patterns['outcomes_recorded'] > 0:
            narrative.append(
                f"- Success Rate: {patterns['success_rate']:.0%} "
                f"({patterns['outcomes_recorded']} outcomes tracked)"
            )

        # Check for loops
        loops = self.detect_behavioral_loops()
        if loops:
            narrative.append("\n⚠️  Behavioral Concerns:")
            for loop in loops:
                narrative.append(
                    f"- Repetitive behavior detected: {loop['type']} ({loop['severity']} severity)"
                )

        return "\n".join(narrative)

    def save_session_log(self, filename: Optional[str] = None) -> Path:
        """Save complete session log to file."""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{self.agent.name}_session_{timestamp}.json"

        filepath = self.log_dir / filename

        session_data = {
            "agent_name": self.agent.name,
            "agent_id": self.agent.agent_id,
            "session_start": self.session_start,
            "session_end": time.time(),
            "total_decisions": len(self.decision_traces),
            "decision_traces": [trace.to_dict() for trace in self.decision_traces],
            "state_snapshots": self.state_snapshots,
            "analysis": self.analyze_decision_patterns(),
            "narrative_summary": self.generate_narrative_summary(),
        }

        with open(filepath, "w") as f:
            json.dump(session_data, f, indent=2)

        return filepath

    def print_internal_monologue(self, action: str, reasoning: str) -> None:
        """
        Print agent's internal monologue (for debugging/observation).

        Shows what the agent is thinking when they make a decision.
        """
        state = self.agent.get_internal_state_summary()

        print(f"\n{'='*60}")
        print(f"💭 {self.agent.name}'s Internal Monologue")
        print(f"{'='*60}")

        print(f"\nFeeling: {state['emotional_state']['mood']}")

        if state['emotional_state']['dominant_emotion']:
            print(f"Dominant Emotion: {state['emotional_state']['dominant_emotion']}")

        if state['urgent_needs']:
            print(f"Urgent Needs: {', '.join(state['urgent_needs'])}")

        print(f"\nActive Goal: {state['active_goal'] or 'None (idle)'}")

        print(f"\nThinking: {reasoning}")
        print(f"Decision: {action}")

        print(f"{'='*60}\n")


def create_observer_for_sarah(sarah: DeepAgent) -> AgentObserver:
    """
    Create an observer specifically configured for Sarah.

    Returns configured observer ready to track her decisions.
    """
    observer = AgentObserver(sarah, log_dir=Path("./sarah_logs"))

    # Record initial state
    observer.take_snapshot()

    print(f"Observer created for {sarah.name}")
    print(f"Logs will be saved to: {observer.log_dir}")
    print(f"Initial snapshot taken at game time {sarah.game_time:.2f}")

    return observer


# Demo usage
if __name__ == "__main__":
    from .sarah import create_sarah

    print("Creating Sarah and observer...")
    sarah = create_sarah()
    observer = create_observer_for_sarah(sarah)

    print("\nSimulating 20 decision cycles...\n")

    game_state = {
        "location": "tavern_main_hall",
        "agents_present": ["gene_bartender", "player"],
        "recent_events": [],
    }

    for i in range(20):
        # Sarah's cognitive cycle
        action = sarah.cognitive_cycle(game_state)

        if action:
            # Determine reasoning
            active_goal = sarah.goals.get_active_goal()
            reasoning = f"To work toward: {active_goal.description}" if active_goal else "Idle behavior"

            # Record decision
            trace_index = len(observer.decision_traces)
            observer.record_decision(
                action_taken=action.command,
                reasoning=reasoning,
            )

            # Print internal monologue occasionally
            if i % 5 == 0:
                observer.print_internal_monologue(action.command, reasoning)

            # Simulate outcome
            success = True  # Assume success for demo
            outcome = {
                "success": success,
                "description": "Action completed",
            }

            sarah.process_outcome(action, outcome, success)
            observer.record_outcome(trace_index, outcome)

        # Simulate time passing
        sarah.game_time += 0.5

    print("\n" + "="*60)
    print("OBSERVATION SUMMARY")
    print("="*60)

    print(observer.generate_narrative_summary())

    # Save session log
    log_path = observer.save_session_log()
    print(f"\nSession log saved to: {log_path}")

    print("\nAnalysis:")
    analysis = observer.analyze_decision_patterns()
    print(json.dumps(analysis, indent=2))
