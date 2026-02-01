"""
Event Bus for Agent Communication
"""
import asyncio
from typing import Callable, Dict, List

class EventBus:
    def __init__(self):
        self.listeners: Dict[str, List[tuple]] = {}
    
    def subscribe(self, event_type: str, callback: Callable, priority: int = 0):
        """
        Register a function with priority.
        Lower priority number = runs first
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append((priority, callback))
        # Sort by priority
        self.listeners[event_type].sort(key=lambda x: x[0])
        print(f"[EVENT_BUS] Agent subscribed to '{event_type}' with priority {priority}")
    
    async def emit(self, event_type: str, data: dict):
        """Execute listeners in priority order with delays between them"""
        
        if event_type in self.listeners:
            print(f"[EVENT_BUS] Emitting '{event_type}' to {len(self.listeners[event_type])} agents")
            
            for priority, callback in self.listeners[event_type]:
                try:
                    await callback(data)
                    # Delay between agents to avoid rate limiting
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"[WARNING] Agent failed but continuing: {e}")

# Global instance
bus = EventBus()