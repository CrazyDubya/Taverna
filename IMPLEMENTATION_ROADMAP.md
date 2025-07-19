# Implementation Roadmap: Three.js Integration

## Phase 1: Foundation (Week 1-2)

### 1.1 Template Integration
- [ ] Add `taverna_3d.html` to existing template system
- [ ] Update FastAPI routes to serve 3D interface option
- [ ] Create toggle between classic and 3D interfaces
- [ ] Ensure backward compatibility with existing users

### 1.2 Asset Preparation  
- [ ] Create 3D model library (GLB/GLTF format)
  - Tavern furniture (tables, chairs, bar)
  - Character models (bartender, patrons)
  - Environmental objects (fireplace, lanterns)
- [ ] Optimize textures for web delivery
- [ ] Implement progressive loading system

### 1.3 API Extensions
```python
# Add to living_rusted_tankard/core/api.py
@app.get("/3d-interface", response_class=HTMLResponse)
async def get_3d_interface():
    """Serve enhanced 3D interface"""
    return templates.TemplateResponse("taverna_3d.html", {"request": request})

@app.get("/api/scene-state")
async def get_scene_state(session_id: str):
    """Return 3D scene state for current game session"""
    game_state = get_game_state(session_id)
    return {
        "npcs": [{"id": npc.id, "position": npc.position, "model": npc.model} 
                for npc in game_state.npcs.present_npcs],
        "time_of_day": game_state.clock.current_time.hour,
        "weather": game_state.weather.current,
        "lighting": calculate_lighting_state(game_state)
    }
```

## Phase 2: Core Integration (Week 3-4)

### 2.1 Game State Synchronization
- [ ] Extend GameState to include 3D visualization data
- [ ] Real-time state updates via WebSocket
- [ ] Bidirectional command processing (text ↔ 3D)

```python
# Add to living_rusted_tankard/core/game_state.py
class Enhanced3DGameState(GameState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene_state = SceneState()
        self.visual_effects = VisualEffectsManager()
    
    def update_3d_scene(self):
        """Update 3D scene based on current game state"""
        self.scene_state.update_npcs(self.npcs.present_npcs)
        self.scene_state.update_lighting(self.clock.current_time)
        self.scene_state.update_weather(self.weather.current)
```

### 2.2 NPC Positioning System
- [ ] Add position coordinates to NPC models
- [ ] Implement movement patterns and schedules
- [ ] Create animation state machine for NPC actions

```python
# Extend living_rusted_tankard/core/npc.py
class Enhanced3DNPC(NPC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position = Position3D(x=0, y=0, z=0)
        self.model_id = "default_npc"
        self.animation_state = "idle"
        
    def move_to(self, target_position: Position3D):
        """Animate NPC movement in 3D space"""
        self.position = target_position
        self.animation_state = "walking"
```

### 2.3 Interactive Object System
- [ ] Define clickable areas for 3D objects
- [ ] Map 3D interactions to existing game commands
- [ ] Implement hover states and tooltips

```javascript
// Add to 3D template
class InteractiveObjectManager {
    constructor(scene, gameInterface) {
        this.objects = new Map();
        this.raycaster = new THREE.Raycaster();
        this.gameInterface = gameInterface;
    }
    
    registerObject(mesh, gameCommand) {
        this.objects.set(mesh.uuid, {
            mesh: mesh,
            command: gameCommand,
            originalMaterial: mesh.material.clone()
        });
    }
    
    handleClick(intersectedObject) {
        const objectData = this.objects.get(intersectedObject.uuid);
        if (objectData) {
            this.gameInterface.executeCommand(objectData.command);
        }
    }
}
```

## Phase 3: Advanced Features (Week 5-6)

### 3.1 Weather and Atmosphere System
- [ ] Dynamic lighting based on time/weather
- [ ] Particle systems for environmental effects
- [ ] Audio integration for ambient sounds

```python
# Add to living_rusted_tankard/core/
class WeatherSystem:
    def __init__(self):
        self.current_weather = "clear"
        self.transition_duration = 300  # seconds
        
    def change_weather(self, new_weather):
        """Gradually transition to new weather state"""
        return {
            "type": "weather_change",
            "from": self.current_weather,
            "to": new_weather,
            "duration": self.transition_duration,
            "effects": self.get_weather_effects(new_weather)
        }
    
    def get_weather_effects(self, weather):
        effects = {
            "rain": {"particles": "rain", "lighting": 0.6, "sound": "rain_ambient"},
            "storm": {"particles": "storm", "lighting": 0.3, "sound": "thunder"},
            "fog": {"particles": "fog", "lighting": 0.7, "sound": "wind_light"},
            "clear": {"particles": None, "lighting": 1.0, "sound": "tavern_ambient"}
        }
        return effects.get(weather, effects["clear"])
```

### 3.2 Performance Optimization
- [ ] Level-of-detail (LOD) system for 3D models
- [ ] Occlusion culling for hidden objects
- [ ] Quality settings for different devices

```javascript
// Performance optimization system
class PerformanceManager {
    constructor(renderer, scene) {
        this.renderer = renderer;
        this.scene = scene;
        this.qualityLevel = "medium";
        this.frameRate = new FrameRateMonitor();
    }
    
    adjustQuality() {
        const fps = this.frameRate.getAverageFPS();
        if (fps < 30 && this.qualityLevel === "high") {
            this.setQuality("medium");
        } else if (fps < 20 && this.qualityLevel === "medium") {
            this.setQuality("low");
        }
    }
    
    setQuality(level) {
        this.qualityLevel = level;
        const settings = this.getQualitySettings(level);
        this.renderer.setPixelRatio(settings.pixelRatio);
        this.renderer.shadowMap.enabled = settings.shadows;
        // Update particle counts, LOD levels, etc.
    }
}
```

## Phase 4: Polish and Optimization (Week 7-8)

### 4.1 Mobile Optimization
- [ ] Touch-friendly controls for mobile devices
- [ ] Adaptive UI scaling for different screen sizes
- [ ] Gesture support for camera movement

### 4.2 Advanced Interactions
- [ ] Multi-select for group commands
- [ ] Drag-and-drop for inventory management
- [ ] Context menus for complex interactions

### 4.3 Analytics Integration
```python
# Add to living_rusted_tankard/core/analytics.py
class VisualizationAnalytics:
    def track_3d_interaction(self, object_type, command, success):
        """Track how users interact with 3D elements"""
        event = {
            "type": "3d_interaction",
            "object": object_type,
            "command": command,
            "success": success,
            "timestamp": datetime.utcnow()
        }
        self.log_event(event)
    
    def track_performance_metrics(self, fps, memory_usage, load_time):
        """Monitor 3D performance across different devices"""
        metrics = {
            "fps": fps,
            "memory_mb": memory_usage,
            "load_time_ms": load_time,
            "user_agent": request.headers.get("User-Agent")
        }
        self.log_metrics(metrics)
```

## Integration Points

### 4.4 Existing System Connections
```python
# living_rusted_tankard/core/enhanced_game_state.py
class ThreeJSGameState(GameState):
    def process_command(self, command, source="text"):
        """Process commands from text input or 3D interaction"""
        result = super().process_command(command)
        
        # Add 3D visualization updates
        if source == "3d":
            result["visual_feedback"] = self.generate_3d_feedback(command)
        
        # Update scene state
        result["scene_updates"] = self.get_scene_updates()
        
        return result
    
    def generate_3d_feedback(self, command):
        """Generate visual effects for 3D commands"""
        if "gamble" in command:
            return {"type": "dice_animation", "duration": 2000}
        elif "talk" in command:
            return {"type": "speech_bubble", "npc_id": "bartender"}
        elif "fireplace" in command:
            return {"type": "healing_glow", "duration": 3000}
        return None
```

## Deployment Strategy

### 5.1 Rollout Plan
1. **Beta Testing**: Deploy to subset of users with feedback collection
2. **A/B Testing**: Compare engagement metrics between classic and 3D interfaces
3. **Gradual Migration**: Offer 3D as opt-in feature initially
4. **Performance Monitoring**: Track load times and error rates across devices

### 5.2 Fallback Strategy
- [ ] Feature detection for WebGL support
- [ ] Graceful degradation to classic interface
- [ ] Error recovery and user notification system

```javascript
// Feature detection and fallback
class CompatibilityChecker {
    static checkWebGLSupport() {
        try {
            const canvas = document.createElement('canvas');
            return !!(window.WebGLRenderingContext && 
                     canvas.getContext('webgl'));
        } catch (e) {
            return false;
        }
    }
    
    static checkDeviceCapabilities() {
        const memory = navigator.deviceMemory || 4; // GB
        const cores = navigator.hardwareConcurrency || 4;
        
        if (memory < 2 || cores < 2) {
            return "low";
        } else if (memory >= 4 && cores >= 4) {
            return "high";
        }
        return "medium";
    }
}
```

## Success Metrics

### 5.3 KPIs to Track
- **User Engagement**: Session duration, actions per session
- **Performance**: Load times, frame rates, error rates
- **Adoption**: 3D interface usage vs classic interface
- **User Satisfaction**: Feedback scores, retention rates

### 5.4 Monitoring Tools
```python
# Add monitoring dashboard
@app.get("/admin/3d-metrics")
async def get_3d_metrics():
    """Admin dashboard for 3D enhancement metrics"""
    return {
        "active_3d_users": count_active_3d_users(),
        "average_fps": get_average_fps(),
        "popular_interactions": get_interaction_stats(),
        "device_compatibility": get_device_stats()
    }
```

This roadmap provides a clear path from the current demo to a fully integrated, production-ready 3D enhancement that supercharges the Taverna experience while maintaining the core narrative gameplay that makes it special.