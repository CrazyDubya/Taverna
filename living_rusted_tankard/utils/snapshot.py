"""
Snapshot utilities for debugging The Living Rusted Tankard game.
Provides functionality to display and log game state snapshots.
"""
import json
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path

class GameSnapshot:
    """Class to handle game state snapshots for debugging."""
    
    def __init__(self, save_dir: str = 'snapshots'):
        """Initialize with save directory."""
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
    
    def capture(self, state: Dict[str, Any], command: Optional[str] = None) -> str:
        """
        Capture a snapshot of the game state.
        
        Args:
            state: Current game state
            command: Command that triggered this snapshot (optional)
            
        Returns:
            Formatted string representation of the snapshot
        """
        # Create a simplified view of the state
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'state': self._simplify_state(state)
        }
        
        # Format for console output
        output = self._format_snapshot(snapshot)
        
        # Save to file
        self._save_snapshot(snapshot)
        
        return output
    
    def _simplify_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simplified version of the game state for display."""
        simplified = {}
        
        # Extract key state information
        if 'player' in state:
            simplified['player'] = {
                'gold': state['player'].get('gold', 0),
                'has_room': state['player'].get('has_room', False),
                'tiredness': state['player'].get('tiredness', 0)
            }
        
        if 'time' in state:
            simplified['time'] = state['time']
            
        if 'location' in state:
            simplified['location'] = state['location']
            
        if 'npcs' in state:
            simplified['npcs'] = [
                {'name': npc.get('name', 'Unknown'), 'present': npc.get('present', False)}
                for npc in state.get('npcs', [])
            ]
            
        return simplified
    
    def _format_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Format the snapshot for console output."""
        lines = [
            "\n=== GAME SNAPSHOT ===",
            f"Time: {snapshot['timestamp']}"
        ]
        
        if snapshot.get('command'):
            lines.append(f"Command: {snapshot['command']}")
            
        state = snapshot['state']
        
        if 'time' in state:
            lines.append(f"\n🕒 Game Time: {state['time']:.1f} hours")
            
        if 'player' in state:
            player = state['player']
            lines.extend([
                "\n👤 Player State:",
                f"  Gold: {player.get('gold', 0)}",
                f"  Has Room: {'✅' if player.get('has_room') else '❌'}",
                f"  Tiredness: {player.get('tiredness', 0)}/10"
            ])
            
        if 'location' in state:
            lines.append(f"\n🏠 Location: {state['location']}")
            
        if 'npcs' in state and state['npcs']:
            lines.append("\n👥 NPCs Present:")
            for npc in state['npcs']:
                if npc.get('present'):
                    lines.append(f"  - {npc.get('name')}")
                    
        lines.append("=" * 20 + "\n")
        return "\n".join(lines)
    
    def _save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Save the snapshot to a file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.save_dir / f"snapshot_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(snapshot, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save snapshot: {e}")

# Global instance for easy access
snapshot_taker = GameSnapshot()
