from collections import defaultdict
from typing import Dict,Type,List,Callable
from event import Event

class EventBus:
    """
    EventBus is a simple publish-subscribe event system that allows handlers to subscribe to specific event types,
    unsubscribe from them, and emit events to all registered handlers for a given event type.
    """
    
    def __init__(self):
        """
        Initialize subscribe dict
        key : event type (class)
        value : Functions list called when an event is emit
        """
        self._subscribers: Dict[Type, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable):
        """
        Subscribe a handler to an event type
        
        Args:
            event_type(Type) : Event class to listen 
            handler(Callable) : Function who receive the event 
        """
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: Type, handler: Callable):
        """
        Unsubscribe a handler to an event type
        
        Args:
            event_type(Type) : Event class to stop to listen
            handler(Callable) : Function to remove 
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def emit(self, event: Event):
        """
        Emit an event. All registered handler for provided event type will be executed.
        
        Args:
            event(Event) : An instance of Event object 
        """
        for handler in self._subscribers[type(event)]:
            handler(event)