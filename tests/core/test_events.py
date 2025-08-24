"""
Tests for event system
"""

import pytest
from unittest.mock import Mock
from src.core.events import EventBus, Event, EventType


class TestEventSystem:
    """Test event system functionality"""
    
    def test_event_creation(self):
        """Test event creation"""
        event = Event.create(EventType.CLUSTER_CHANGED, "test", cluster="test-cluster")
        
        assert event.type == EventType.CLUSTER_CHANGED
        assert event.source == "test"
        assert event.data["cluster"] == "test-cluster"
        assert event.timestamp > 0
    
    def test_event_bus_subscribe_emit(self):
        """Test event subscription and emission"""
        event_bus = EventBus()
        mock_handler = Mock()
        
        # Subscribe to event
        event_bus.subscribe(EventType.CLUSTER_CHANGED, mock_handler)
        
        # Emit event
        event = Event.create(EventType.CLUSTER_CHANGED, "test", cluster="test-cluster")
        event_bus.emit(event)
        
        # Verify handler was called
        mock_handler.assert_called_once_with(event)
    
    def test_event_bus_multiple_subscribers(self):
        """Test multiple subscribers for same event"""
        event_bus = EventBus()
        mock_handler1 = Mock()
        mock_handler2 = Mock()
        
        # Subscribe both handlers
        event_bus.subscribe(EventType.CLUSTER_CHANGED, mock_handler1)
        event_bus.subscribe(EventType.CLUSTER_CHANGED, mock_handler2)
        
        # Emit event
        event = Event.create(EventType.CLUSTER_CHANGED, "test")
        event_bus.emit(event)
        
        # Verify both handlers were called
        mock_handler1.assert_called_once_with(event)
        mock_handler2.assert_called_once_with(event)
    
    def test_event_bus_unsubscribe(self):
        """Test event unsubscription"""
        event_bus = EventBus()
        mock_handler = Mock()
        
        # Subscribe and then unsubscribe
        event_bus.subscribe(EventType.CLUSTER_CHANGED, mock_handler)
        event_bus.unsubscribe(EventType.CLUSTER_CHANGED, mock_handler)
        
        # Emit event
        event = Event.create(EventType.CLUSTER_CHANGED, "test")
        event_bus.emit(event)
        
        # Verify handler was not called
        mock_handler.assert_not_called()
    
    def test_event_bus_emit_sync(self):
        """Test synchronous event emission"""
        event_bus = EventBus()
        mock_handler = Mock()
        
        event_bus.subscribe(EventType.CLUSTER_CHANGED, mock_handler)
        event_bus.emit_sync(EventType.CLUSTER_CHANGED, "test", cluster="test-cluster")
        
        # Verify handler was called with correct data
        assert mock_handler.call_count == 1
        event = mock_handler.call_args[0][0]
        assert event.type == EventType.CLUSTER_CHANGED
        assert event.data["cluster"] == "test-cluster"