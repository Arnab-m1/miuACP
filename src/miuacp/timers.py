"""
µACP Timers & Scheduling State Management

This module handles all timer and scheduling state including:
- Retransmission timers
- Heartbeat/PING timers
- Session expiration timers
- Priority queues for scheduling outgoing messages
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import heapq


class TimerType(Enum):
    """Timer types."""
    RETRANSMISSION = "retransmission"
    HEARTBEAT = "heartbeat"
    SESSION_EXPIRY = "session_expiry"
    CLEANUP = "cleanup"
    CUSTOM = "custom"


class TimerState(Enum):
    """Timer states."""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    RUNNING = "running"


class MessagePriority(Enum):
    """Message priorities for scheduling."""
    CRITICAL = 0      # Highest priority
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BULK = 4          # Lowest priority


@dataclass
class Timer:
    """Timer information."""
    timer_id: str
    timer_type: TimerType
    state: TimerState
    created: float
    expires: float
    interval: float  # For recurring timers
    callback: Optional[Callable] = None
    callback_args: Tuple = field(default_factory=tuple)
    callback_kwargs: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    recurring: bool = False
    max_executions: Optional[int] = None
    execution_count: int = 0
    last_execution: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduledMessage:
    """Message scheduled for transmission."""
    message_id: str
    priority: MessagePriority
    created: float
    scheduled_time: float
    message_data: Dict[str, Any]
    destination: str
    retry_count: int = 0
    max_retries: int = 3
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionTimer:
    """Session expiration timer."""
    session_id: str
    agent_id: str
    created: float
    expires: float
    last_activity: float
    timeout: float
    callback: Optional[Callable] = None
    context: Dict[str, Any] = field(default_factory=dict)


class UACPTimers:
    """µACP timer and scheduling state management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Timer management
        self.timers: Dict[str, Timer] = {}
        self.timer_queue: List[Tuple[float, str]] = []  # (expires, timer_id)
        self.type_timers: Dict[TimerType, Set[str]] = defaultdict(set)
        
        # Message scheduling
        self.scheduled_messages: Dict[str, ScheduledMessage] = {}
        self.priority_queues: Dict[MessagePriority, List[str]] = defaultdict(list)
        self.message_schedule: List[Tuple[float, str]] = []  # (scheduled_time, message_id)
        
        # Session timers
        self.session_timers: Dict[str, SessionTimer] = {}
        self.agent_sessions: Dict[str, Set[str]] = defaultdict(set)
        
        # Configuration
        self.max_timers = self.config.get('max_timers', 10000)
        self.max_scheduled_messages = self.config.get('max_scheduled_messages', 10000)
        self.max_session_timers = self.config.get('max_session_timers', 1000)
        
        self.default_retransmission_timeout = self.config.get('default_retransmission_timeout', 30.0)
        self.default_heartbeat_interval = self.config.get('default_heartbeat_interval', 60.0)
        self.default_session_timeout = self.config.get('default_session_timeout', 300.0)
        self.default_cleanup_interval = self.config.get('default_cleanup_interval', 300.0)
        
        # State tracking
        self.last_cleanup = time.time()
        self.cleanup_interval = 60.0
        self.stats = {
            'timers_created': 0,
            'timers_expired': 0,
            'timers_cancelled': 0,
            'messages_scheduled': 0,
            'messages_sent': 0,
            'sessions_created': 0,
            'sessions_expired': 0,
            'heartbeats_sent': 0,
            'retransmissions': 0
        }
        
        # Background tasks
        self._running = False
        self._timer_task: Optional[asyncio.Task] = None
        self._scheduler_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the timer manager."""
        if self._running:
            return
        
        self._running = True
        self._timer_task = asyncio.create_task(self._timer_loop())
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the timer manager."""
        self._running = False
        
        for task in [self._timer_task, self._scheduler_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    # === Timer Management ===
    
    def create_timer(self, timer_type: TimerType, timeout: float,
                     callback: Optional[Callable] = None,
                     callback_args: Tuple = (), callback_kwargs: Optional[Dict[str, Any]] = None,
                     recurring: bool = False, interval: Optional[float] = None,
                     max_executions: Optional[int] = None,
                     context: Optional[Dict[str, Any]] = None) -> str:
        """Create a new timer."""
        if len(self.timers) >= self.max_timers:
            # Remove oldest timer
            oldest = min(self.timers.values(), key=lambda t: t.created)
            self._remove_timer(oldest.timer_id)
        
        timer_id = str(uuid.uuid4())
        now = time.time()
        
        if interval is None:
            interval = timeout
        
        timer = Timer(
            timer_id=timer_id,
            timer_type=timer_type,
            state=TimerState.ACTIVE,
            created=now,
            expires=now + timeout,
            interval=interval,
            callback=callback,
            callback_args=callback_args,
            callback_kwargs=callback_kwargs or {},
            recurring=recurring,
            max_executions=max_executions,
            context=context or {}
        )
        
        self.timers[timer_id] = timer
        self.type_timers[timer_type].add(timer_id)
        heapq.heappush(self.timer_queue, (timer.expires, timer_id))
        
        self.stats['timers_created'] += 1
        return timer_id
    
    def create_retransmission_timer(self, message_id: str, timeout: float,
                                   callback: Optional[Callable] = None,
                                   context: Optional[Dict[str, Any]] = None) -> str:
        """Create a retransmission timer."""
        return self.create_timer(
            timer_type=TimerType.RETRANSMISSION,
            timeout=timeout,
            callback=callback,
            context={'message_id': message_id, **context} if context else {'message_id': message_id}
        )
    
    def create_heartbeat_timer(self, agent_id: str, interval: float,
                              callback: Optional[Callable] = None,
                              context: Optional[Dict[str, Any]] = None) -> str:
        """Create a heartbeat timer."""
        return self.create_timer(
            timer_type=TimerType.HEARTBEAT,
            timeout=interval,
            callback=callback,
            recurring=True,
            interval=interval,
            context={'agent_id': agent_id, **context} if context else {'agent_id': agent_id}
        )
    
    def create_session_timer(self, session_id: str, timeout: float,
                            callback: Optional[Callable] = None,
                            context: Optional[Dict[str, Any]] = None) -> str:
        """Create a session expiration timer."""
        return self.create_timer(
            timer_type=TimerType.SESSION_EXPIRY,
            timeout=timeout,
            callback=callback,
            context={'session_id': session_id, **context} if context else {'session_id': session_id}
        )
    
    def cancel_timer(self, timer_id: str) -> bool:
        """Cancel a timer."""
        return self._remove_timer(timer_id, TimerState.CANCELLED)
    
    def pause_timer(self, timer_id: str) -> bool:
        """Pause a timer."""
        if timer_id in self.timers:
            timer = self.timers[timer_id]
            if timer.state == TimerState.ACTIVE:
                timer.state = TimerState.PAUSED
                return True
        return False
    
    def resume_timer(self, timer_id: str) -> bool:
        """Resume a paused timer."""
        if timer_id in self.timers:
            timer = self.timers[timer_id]
            if timer.state == TimerState.PAUSED:
                timer.state = TimerState.ACTIVE
                # Recalculate expiration time
                now = time.time()
                timer.expires = now + timer.interval
                heapq.heappush(self.timer_queue, (timer.expires, timer_id))
                return True
        return False
    
    def _remove_timer(self, timer_id: str, final_state: TimerState = TimerState.CANCELLED) -> bool:
        """Remove a timer."""
        if timer_id in self.timers:
            timer = self.timers[timer_id]
            
            # Remove from type index
            self.type_timers[timer.timer_type].discard(timer_id)
            
            # Update stats
            if final_state == TimerState.CANCELLED:
                self.stats['timers_cancelled'] += 1
            
            del self.timers[timer_id]
            return True
        
        return False
    
    def get_timer(self, timer_id: str) -> Optional[Timer]:
        """Get timer by ID."""
        return self.timers.get(timer_id)
    
    def get_timers_by_type(self, timer_type: TimerType) -> List[Timer]:
        """Get all timers of a specific type."""
        timer_ids = self.type_timers.get(timer_type, set())
        return [self.timers[timer_id] for timer_id in timer_ids 
                if timer_id in self.timers]
    
    # === Message Scheduling ===
    
    def schedule_message(self, message_data: Dict[str, Any], destination: str,
                        priority: MessagePriority = MessagePriority.NORMAL,
                        delay: float = 0.0, retry_count: int = 0,
                        max_retries: int = 3, context: Optional[Dict[str, Any]] = None) -> str:
        """Schedule a message for transmission."""
        if len(self.scheduled_messages) >= self.max_scheduled_messages:
            # Remove lowest priority message
            lowest_priority = max(MessagePriority, key=lambda p: p.value)
            for p in MessagePriority:
                if self.priority_queues[p]:
                    lowest_priority = p
                    break
            
            if self.priority_queues[lowest_priority]:
                oldest_msg_id = self.priority_queues[lowest_priority].pop(0)
                if oldest_msg_id in self.scheduled_messages:
                    del self.scheduled_messages[oldest_msg_id]
        
        message_id = str(uuid.uuid4())
        now = time.time()
        scheduled_time = now + delay
        
        scheduled_message = ScheduledMessage(
            message_id=message_id,
            priority=priority,
            created=now,
            scheduled_time=scheduled_time,
            message_data=message_data,
            destination=destination,
            retry_count=retry_count,
            max_retries=max_retries,
            context=context or {}
        )
        
        self.scheduled_messages[message_id] = scheduled_message
        self.priority_queues[priority].append(message_id)
        heapq.heappush(self.message_schedule, (scheduled_time, message_id))
        
        self.stats['messages_scheduled'] += 1
        return message_id
    
    def get_next_message(self) -> Optional[ScheduledMessage]:
        """Get the next message ready for transmission."""
        now = time.time()
        
        while self.message_schedule and self.message_schedule[0][0] <= now:
            scheduled_time, message_id = heapq.heappop(self.message_schedule)
            
            if message_id in self.scheduled_messages:
                message = self.scheduled_messages[message_id]
                
                # Remove from priority queue
                if message_id in self.priority_queues[message.priority]:
                    self.priority_queues[message.priority].remove(message_id)
                
                # Remove from scheduled messages
                del self.scheduled_messages[message_id]
                
                self.stats['messages_sent'] += 1
                return message
        
        return None
    
    def cancel_scheduled_message(self, message_id: str) -> bool:
        """Cancel a scheduled message."""
        if message_id in self.scheduled_messages:
            message = self.scheduled_messages[message_id]
            
            # Remove from priority queue
            if message_id in self.priority_queues[message.priority]:
                self.priority_queues[message.priority].remove(message_id)
            
            # Remove from message schedule
            self.message_schedule = [(t, mid) for t, mid in self.message_schedule if mid != message_id]
            heapq.heapify(self.message_schedule)
            
            del self.scheduled_messages[message_id]
            return True
        
        return False
    
    def get_scheduled_message(self, message_id: str) -> Optional[ScheduledMessage]:
        """Get scheduled message by ID."""
        return self.scheduled_messages.get(message_id)
    
    def get_messages_by_priority(self, priority: MessagePriority) -> List[ScheduledMessage]:
        """Get all scheduled messages of a specific priority."""
        message_ids = self.priority_queues.get(priority, [])
        return [self.scheduled_messages[msg_id] for msg_id in message_ids 
                if msg_id in self.scheduled_messages]
    
    # === Session Timer Management ===
    
    def create_session_timer(self, session_id: str, agent_id: str, timeout: float,
                            callback: Optional[Callable] = None,
                            context: Optional[Dict[str, Any]] = None) -> str:
        """Create a session timer."""
        if len(self.session_timers) >= self.max_session_timers:
            # Remove oldest session timer
            oldest = min(self.session_timers.values(), key=lambda s: s.created)
            self._remove_session_timer(oldest.session_id)
        
        now = time.time()
        
        session_timer = SessionTimer(
            session_id=session_id,
            agent_id=agent_id,
            created=now,
            expires=now + timeout,
            last_activity=now,
            timeout=timeout,
            callback=callback,
            context=context or {}
        )
        
        self.session_timers[session_id] = session_timer
        self.agent_sessions[agent_id].add(session_id)
        
        self.stats['sessions_created'] += 1
        return session_id
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session activity timestamp."""
        if session_id in self.session_timers:
            session_timer = self.session_timers[session_id]
            now = time.time()
            session_timer.last_activity = now
            session_timer.expires = now + session_timer.timeout
            return True
        return False
    
    def extend_session(self, session_id: str, additional_time: float) -> bool:
        """Extend session timeout."""
        if session_id in self.session_timers:
            session_timer = self.session_timers[session_id]
            session_timer.expires += additional_time
            return True
        return False
    
    def _remove_session_timer(self, session_id: str) -> bool:
        """Remove a session timer."""
        if session_id in self.session_timers:
            session_timer = self.session_timers[session_id]
            
            # Remove from agent sessions
            if session_timer.agent_id in self.agent_sessions:
                self.agent_sessions[session_timer.agent_id].discard(session_id)
                if not self.agent_sessions[session_timer.agent_id]:
                    del self.agent_sessions[session_timer.agent_id]
            
            del self.session_timers[session_id]
            return True
        
        return False
    
    def get_session_timer(self, session_id: str) -> Optional[SessionTimer]:
        """Get session timer by ID."""
        return self.session_timers.get(session_id)
    
    def get_agent_sessions(self, agent_id: str) -> List[SessionTimer]:
        """Get all sessions for an agent."""
        session_ids = self.agent_sessions.get(agent_id, set())
        return [self.session_timers[session_id] for session_id in session_ids 
                if session_id in self.session_timers]
    
    # === Background Tasks ===
    
    async def _timer_loop(self):
        """Background timer loop."""
        while self._running:
            try:
                await asyncio.sleep(0.1)  # Check timers every 100ms
                self._process_expired_timers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in timer loop: {e}")
    
    async def _scheduler_loop(self):
        """Background scheduler loop."""
        while self._running:
            try:
                await asyncio.sleep(0.1)  # Check scheduler every 100ms
                self._process_scheduled_messages()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
    
    def _process_expired_timers(self):
        """Process expired timers."""
        now = time.time()
        
        while self.timer_queue and self.timer_queue[0][0] <= now:
            expires, timer_id = heapq.heappop(self.timer_queue)
            
            if timer_id in self.timers:
                timer = self.timers[timer_id]
                
                if timer.expires <= now and timer.state == TimerState.ACTIVE:
                    # Execute callback if available
                    if timer.callback:
                        try:
                            timer.state = TimerState.RUNNING
                            timer.last_execution = now
                            timer.execution_count += 1
                            
                            # Execute callback
                            if timer.callback_args and timer.callback_kwargs:
                                timer.callback(*timer.callback_args, **timer.callback_kwargs)
                            elif timer.callback_args:
                                timer.callback(*timer.callback_args)
                            elif timer.callback_kwargs:
                                timer.callback(**timer.callback_kwargs)
                            else:
                                timer.callback()
                            
                            # Update stats based on timer type
                            if timer.timer_type == TimerType.HEARTBEAT:
                                self.stats['heartbeats_sent'] += 1
                            elif timer.timer_type == TimerType.RETRANSMISSION:
                                self.stats['retransmissions'] += 1
                            
                        except Exception as e:
                            print(f"Error executing timer callback: {e}")
                        finally:
                            timer.state = TimerState.ACTIVE
                    
                    # Handle recurring timers
                    if timer.recurring and (timer.max_executions is None or 
                                          timer.execution_count < timer.max_executions):
                        # Reschedule
                        timer.expires = now + timer.interval
                        heapq.heappush(self.timer_queue, (timer.expires, timer_id))
                    else:
                        # Mark as expired and remove
                        timer.state = TimerState.EXPIRED
                        self.stats['timers_expired'] += 1
                        self._remove_timer(timer_id)
    
    def _process_scheduled_messages(self):
        """Process scheduled messages."""
        # This is called by the scheduler loop to check for ready messages
        # The actual message processing is done by get_next_message()
        pass
    
    def _cleanup_expired(self):
        """Clean up expired entries."""
        now = time.time()
        
        # Clean up expired session timers
        expired_sessions = [
            session_id for session_id, session in self.session_timers.items()
            if now > session.expires
        ]
        
        for session_id in expired_sessions:
            session = self.session_timers[session_id]
            if session.callback:
                try:
                    session.callback(session_id, session.agent_id, session.context)
                except Exception as e:
                    print(f"Error executing session expiry callback: {e}")
            
            self._remove_session_timer(session_id)
            self.stats['sessions_expired'] += 1
        
        self.last_cleanup = now
    
    # === Statistics and Export ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get timer statistics."""
        return {
            **self.stats,
            'current_timers': len(self.timers),
            'current_scheduled_messages': len(self.scheduled_messages),
            'current_session_timers': len(self.session_timers),
            'timer_queue_size': len(self.timer_queue),
            'message_schedule_size': len(self.message_schedule),
            'last_cleanup': self.last_cleanup
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export current timer state."""
        return {
            'timers': {
                timer_id: {
                    'type': timer.timer_type.value,
                    'state': timer.state.value,
                    'created': timer.created,
                    'expires': timer.expires,
                    'recurring': timer.recurring,
                    'execution_count': timer.execution_count
                }
                for timer_id, timer in self.timers.items()
            },
            'scheduled_messages': {
                msg_id: {
                    'priority': msg.priority.value,
                    'scheduled_time': msg.scheduled_time,
                    'destination': msg.destination,
                    'retry_count': msg.retry_count
                }
                for msg_id, msg in self.scheduled_messages.items()
            },
            'session_timers': {
                session_id: {
                    'agent_id': session.agent_id,
                    'created': session.created,
                    'expires': session.expires,
                    'last_activity': session.last_activity
                }
                for session_id, session in self.session_timers.items()
            },
            'stats': self.get_stats()
        }
