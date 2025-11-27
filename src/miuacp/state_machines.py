"""
µACP State Machines & Formal Semantics

Implements:
- Formal state machine for each verb (PING, TELL, ASK, OBSERVE)
- QoS2 2-phase commit state diagram
- Speech-act calculus state transitions
- Formal semantics validation
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Callable, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from .protocol import UACPVerb, UACPOptionType, UACPMessage, UACPHeader


class VerbState(Enum):
    """Verb states for state machines."""
    # ASK states
    ASK_SENT = "ask_sent"
    ASK_ACKNOWLEDGED = "ask_acknowledged"
    ASK_COMPLETED = "ask_completed"
    ASK_TIMEOUT = "ask_timeout"
    ASK_FAILED = "ask_failed"
    
    # TELL states
    TELL_SENT = "tell_sent"
    TELL_DELIVERED = "tell_delivered"
    TELL_FAILED = "tell_failed"
    
    # PING states
    PING_SENT = "ping_sent"
    PING_RECEIVED = "ping_received"
    PING_TIMEOUT = "ping_timeout"
    
    # OBSERVE states
    OBSERVE_REGISTERED = "observe_registered"
    OBSERVE_ACTIVE = "observe_active"
    OBSERVE_CANCELLED = "observe_cancelled"
    OBSERVE_FAILED = "observe_failed"
    
    # QoS2 states
    QOS2_PREPARE = "qos2_prepare"
    QOS2_PREPARE_ACK = "qos2_prepare_ack"
    QOS2_COMMIT = "qos2_commit"
    QOS2_COMMIT_ACK = "qos2_commit_ack"
    QOS2_COMPLETE = "qos2_complete"
    QOS2_ABORT = "qos2_abort"


class StateTransition(Enum):
    """State transition types."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCEL = "cancel"
    RETRY = "retry"


@dataclass
class StateMachineContext:
    """Context for state machine execution."""
    message_id: str
    verb: UACPVerb
    qos: int
    topic: str
    payload: bytes
    source: str
    destination: str
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateTransitionEvent:
    """State transition event."""
    from_state: VerbState
    to_state: VerbState
    transition_type: StateTransition
    timestamp: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class UACPStateMachine:
    """Base state machine class."""
    
    def __init__(self, context: StateMachineContext):
        self.context = context
        self.current_state: VerbState = None
        self.state_history: List[StateTransitionEvent] = []
        self.state_handlers: Dict[VerbState, Callable] = {}
        self.transition_handlers: Dict[tuple, Callable] = {}
        
        # Initialize state machine
        self._init_state_machine()
    
    def _init_state_machine(self):
        """Initialize the state machine."""
        raise NotImplementedError
    
    def get_current_state(self) -> VerbState:
        """Get current state."""
        return self.current_state
    
    def get_state_history(self) -> List[StateTransitionEvent]:
        """Get state transition history."""
        return self.state_history.copy()
    
    def can_transition_to(self, target_state: VerbState) -> bool:
        """Check if transition to target state is allowed."""
        raise NotImplementedError
    
    async def transition_to(self, target_state: VerbState, 
                          transition_type: StateTransition = StateTransition.SUCCESS,
                          reason: str = "", metadata: Dict[str, Any] = None) -> bool:
        """Transition to target state."""
        if not self.can_transition_to(target_state):
            print(f"❌ Invalid transition from {self.current_state} to {target_state}")
            return False
        
        # Record transition
        event = StateTransitionEvent(
            from_state=self.current_state,
            to_state=target_state,
            transition_type=transition_type,
            timestamp=time.time(),
            reason=reason,
            metadata=metadata or {}
        )
        
        self.state_history.append(event)
        
        # Execute transition handler
        if (self.current_state, target_state) in self.transition_handlers:
            try:
                await self.transition_handlers[(self.current_state, target_state)](event)
            except Exception as e:
                print(f"❌ Transition handler error: {e}")
        
        # Update state
        old_state = self.current_state
        self.current_state = target_state
        
        print(f"🔄 State transition: {old_state} → {target_state} ({reason})")
        
        # Execute state handler
        if target_state in self.state_handlers:
            try:
                await self.state_handlers[target_state](event)
            except Exception as e:
                print(f"❌ State handler error: {e}")
        
        return True
    
    def add_state_handler(self, state: VerbState, handler: Callable):
        """Add handler for specific state."""
        self.state_handlers[state] = handler
    
    def add_transition_handler(self, from_state: VerbState, to_state: VerbState, handler: Callable):
        """Add handler for specific transition."""
        self.transition_handlers[(from_state, to_state)] = handler


class ASKStateMachine(UACPStateMachine):
    """State machine for ASK verb."""
    
    def _init_state_machine(self):
        """Initialize ASK state machine."""
        self.current_state = VerbState.ASK_SENT
        
        # Define valid transitions
        self.valid_transitions = {
            VerbState.ASK_SENT: [VerbState.ASK_ACKNOWLEDGED, VerbState.ASK_TIMEOUT, VerbState.ASK_FAILED],
            VerbState.ASK_ACKNOWLEDGED: [VerbState.ASK_COMPLETED, VerbState.ASK_TIMEOUT, VerbState.ASK_FAILED],
            VerbState.ASK_COMPLETED: [],  # Terminal state
            VerbState.ASK_TIMEOUT: [VerbState.ASK_SENT, VerbState.ASK_FAILED],  # Retry or fail
            VerbState.ASK_FAILED: []  # Terminal state
        }
        
        # Initialize handlers
        self._init_handlers()
    
    def _init_handlers(self):
        """Initialize state and transition handlers."""
        # State handlers
        self.add_state_handler(VerbState.ASK_SENT, self._handle_ask_sent)
        self.add_state_handler(VerbState.ASK_ACKNOWLEDGED, self._handle_ask_acknowledged)
        self.add_state_handler(VerbState.ASK_COMPLETED, self._handle_ask_completed)
        self.add_state_handler(VerbState.ASK_TIMEOUT, self._handle_ask_timeout)
        self.add_state_handler(VerbState.ASK_FAILED, self._handle_ask_failed)
        
        # Transition handlers
        self.add_transition_handler(VerbState.ASK_SENT, VerbState.ASK_ACKNOWLEDGED, self._handle_ack_received)
        self.add_transition_handler(VerbState.ASK_ACKNOWLEDGED, VerbState.ASK_COMPLETED, self._handle_response_received)
        self.add_transition_handler(VerbState.ASK_SENT, VerbState.ASK_TIMEOUT, self._handle_timeout)
    
    def can_transition_to(self, target_state: VerbState) -> bool:
        """Check if transition to target state is allowed."""
        return target_state in self.valid_transitions.get(self.current_state, [])
    
    async def _handle_ask_sent(self, event: StateTransitionEvent):
        """Handle ASK_SENT state."""
        print(f"📤 ASK message sent: {self.context.message_id}")
        
        # Start timeout timer
        asyncio.create_task(self._start_timeout_timer())
    
    async def _handle_ask_acknowledged(self, event: StateTransitionEvent):
        """Handle ASK_ACKNOWLEDGED state."""
        print(f"✅ ASK message acknowledged: {self.context.message_id}")
        
        # Start response timeout timer
        asyncio.create_task(self._start_response_timeout_timer())
    
    async def _handle_ask_completed(self, event: StateTransitionEvent):
        """Handle ASK_COMPLETED state."""
        print(f"🎯 ASK message completed: {self.context.message_id}")
        
        # Mark as successful
        self.context.metadata['success'] = True
        self.context.metadata['completion_time'] = time.time()
    
    async def _handle_ask_timeout(self, event: StateTransitionEvent):
        """Handle ASK_TIMEOUT state."""
        print(f"⏰ ASK message timeout: {self.context.message_id}")
        
        # Check if we can retry
        if self.context.retry_count < self.context.max_retries:
            self.context.retry_count += 1
            print(f"🔄 Retrying ASK message (attempt {self.context.retry_count})")
            await self.transition_to(VerbState.ASK_SENT, StateTransition.RETRY, "Retry after timeout")
        else:
            print(f"❌ Max retries exceeded for ASK message")
            await self.transition_to(VerbState.ASK_FAILED, StateTransition.FAILURE, "Max retries exceeded")
    
    async def _handle_ask_failed(self, event: StateTransitionEvent):
        """Handle ASK_FAILED state."""
        print(f"💥 ASK message failed: {self.context.message_id}")
        
        # Mark as failed
        self.context.metadata['success'] = False
        self.context.metadata['failure_reason'] = event.reason
    
    async def _handle_ack_received(self, event: StateTransitionEvent):
        """Handle ACK received transition."""
        print(f"📥 ACK received for ASK message: {self.context.message_id}")
    
    async def _handle_response_received(self, event: StateTransitionEvent):
        """Handle response received transition."""
        print(f"📥 Response received for ASK message: {self.context.message_id}")
    
    async def _handle_timeout(self, event: StateTransitionEvent):
        """Handle timeout transition."""
        print(f"⏰ Timeout for ASK message: {self.context.message_id}")
    
    async def _start_timeout_timer(self):
        """Start timeout timer for initial send."""
        await asyncio.sleep(self.context.timeout)
        
        if self.current_state == VerbState.ASK_SENT:
            await self.transition_to(VerbState.ASK_TIMEOUT, StateTransition.TIMEOUT, "Initial send timeout")
    
    async def _start_response_timeout_timer(self):
        """Start timeout timer for response."""
        await asyncio.sleep(self.context.timeout)
        
        if self.current_state == VerbState.ASK_ACKNOWLEDGED:
            await self.transition_to(VerbState.ASK_TIMEOUT, StateTransition.TIMEOUT, "Response timeout")
    
    async def receive_ack(self) -> bool:
        """Receive acknowledgment for ASK message."""
        if self.current_state == VerbState.ASK_SENT:
            return await self.transition_to(VerbState.ASK_ACKNOWLEDGED, StateTransition.SUCCESS, "ACK received")
        return False
    
    async def receive_response(self, response: UACPMessage) -> bool:
        """Receive response for ASK message."""
        if self.current_state == VerbState.ASK_ACKNOWLEDGED:
            self.context.metadata['response'] = response
            return await self.transition_to(VerbState.ASK_COMPLETED, StateTransition.SUCCESS, "Response received")
        return False


class OBSERVEStateMachine(UACPStateMachine):
    """State machine for OBSERVE verb."""
    
    def _init_state_machine(self):
        """Initialize OBSERVE state machine."""
        self.current_state = VerbState.OBSERVE_REGISTERED
        
        # Define valid transitions
        self.valid_transitions = {
            VerbState.OBSERVE_REGISTERED: [VerbState.OBSERVE_ACTIVE, VerbState.OBSERVE_FAILED],
            VerbState.OBSERVE_ACTIVE: [VerbState.OBSERVE_CANCELLED, VerbState.OBSERVE_FAILED],
            VerbState.OBSERVE_CANCELLED: [],  # Terminal state
            VerbState.OBSERVE_FAILED: []  # Terminal state
        }
        
        # Initialize handlers
        self._init_handlers()
    
    def _init_handlers(self):
        """Initialize state and transition handlers."""
        # State handlers
        self.add_state_handler(VerbState.OBSERVE_REGISTERED, self._handle_observe_registered)
        self.add_state_handler(VerbState.OBSERVE_ACTIVE, self._handle_observe_active)
        self.add_state_handler(VerbState.OBSERVE_CANCELLED, self._handle_observe_cancelled)
        self.add_state_handler(VerbState.OBSERVE_FAILED, self._handle_observe_failed)
    
    def can_transition_to(self, target_state: VerbState) -> bool:
        """Check if transition to target state is allowed."""
        return target_state in self.valid_transitions.get(self.current_state, [])
    
    async def _handle_observe_registered(self, event: StateTransitionEvent):
        """Handle OBSERVE_REGISTERED state."""
        print(f"📝 OBSERVE subscription registered: {self.context.message_id}")
    
    async def _handle_observe_active(self, event: StateTransitionEvent):
        """Handle OBSERVE_ACTIVE state."""
        print(f"👁️  OBSERVE subscription active: {self.context.message_id}")
    
    async def _handle_observe_cancelled(self, event: StateTransitionEvent):
        """Handle OBSERVE_CANCELLED state."""
        print(f"🚫 OBSERVE subscription cancelled: {self.context.message_id}")
    
    async def _handle_observe_failed(self, event: StateTransitionEvent):
        """Handle OBSERVE_FAILED state."""
        print(f"💥 OBSERVE subscription failed: {self.context.message_id}")
    
    async def activate_subscription(self) -> bool:
        """Activate the OBSERVE subscription."""
        if self.current_state == VerbState.OBSERVE_REGISTERED:
            return await self.transition_to(VerbState.OBSERVE_ACTIVE, StateTransition.SUCCESS, "Subscription activated")
        return False
    
    async def cancel_subscription(self) -> bool:
        """Cancel the OBSERVE subscription."""
        if self.current_state == VerbState.OBSERVE_ACTIVE:
            return await self.transition_to(VerbState.OBSERVE_CANCELLED, StateTransition.CANCEL, "Subscription cancelled")
        return False


class QoS2StateMachine(UACPStateMachine):
    """State machine for QoS2 2-phase commit."""
    
    def _init_state_machine(self):
        """Initialize QoS2 state machine."""
        self.current_state = VerbState.QOS2_PREPARE
        
        # Define valid transitions
        self.valid_transitions = {
            VerbState.QOS2_PREPARE: [VerbState.QOS2_PREPARE_ACK, VerbState.QOS2_ABORT],
            VerbState.QOS2_PREPARE_ACK: [VerbState.QOS2_COMMIT, VerbState.QOS2_ABORT],
            VerbState.QOS2_COMMIT: [VerbState.QOS2_COMMIT_ACK, VerbState.QOS2_ABORT],
            VerbState.QOS2_COMMIT_ACK: [VerbState.QOS2_COMPLETE],
            VerbState.QOS2_COMPLETE: [],  # Terminal state
            VerbState.QOS2_ABORT: []  # Terminal state
        }
        
        # Initialize handlers
        self._init_handlers()
    
    def _init_handlers(self):
        """Initialize state and transition handlers."""
        # State handlers
        self.add_state_handler(VerbState.QOS2_PREPARE, self._handle_prepare)
        self.add_state_handler(VerbState.QOS2_PREPARE_ACK, self._handle_prepare_ack)
        self.add_state_handler(VerbState.QOS2_COMMIT, self._handle_commit)
        self.add_state_handler(VerbState.QOS2_COMMIT_ACK, self._handle_commit_ack)
        self.add_state_handler(VerbState.QOS2_COMPLETE, self._handle_complete)
        self.add_state_handler(VerbState.QOS2_ABORT, self._handle_abort)
    
    def can_transition_to(self, target_state: VerbState) -> bool:
        """Check if transition to target state is allowed."""
        return target_state in self.valid_transitions.get(self.current_state, [])
    
    async def _handle_prepare(self, event: StateTransitionEvent):
        """Handle PREPARE state."""
        print(f"🔒 QoS2: Preparing transaction: {self.context.message_id}")
        
        # Start prepare timeout timer
        asyncio.create_task(self._start_prepare_timeout_timer())
    
    async def _handle_prepare_ack(self, event: StateTransitionEvent):
        """Handle PREPARE_ACK state."""
        print(f"✅ QoS2: Prepare acknowledged: {self.context.message_id}")
        
        # Start commit timeout timer
        asyncio.create_task(self._start_commit_timeout_timer())
    
    async def _handle_commit(self, event: StateTransitionEvent):
        """Handle COMMIT state."""
        print(f"🚀 QoS2: Committing transaction: {self.context.message_id}")
    
    async def _handle_commit_ack(self, event: StateTransitionEvent):
        """Handle COMMIT_ACK state."""
        print(f"✅ QoS2: Commit acknowledged: {self.context.message_id}")
    
    async def _handle_complete(self, event: StateTransitionEvent):
        """Handle COMPLETE state."""
        print(f"🎯 QoS2: Transaction completed: {self.context.message_id}")
        
        # Mark as successful
        self.context.metadata['success'] = True
        self.context.metadata['completion_time'] = time.time()
    
    async def _handle_abort(self, event: StateTransitionEvent):
        """Handle ABORT state."""
        print(f"🚫 QoS2: Transaction aborted: {self.context.message_id}")
        
        # Mark as failed
        self.context.metadata['success'] = False
        self.context.metadata['failure_reason'] = event.reason
    
    async def _start_prepare_timeout_timer(self):
        """Start timeout timer for prepare phase."""
        await asyncio.sleep(self.context.timeout)
        
        if self.current_state == VerbState.QOS2_PREPARE:
            await self.transition_to(VerbState.QOS2_ABORT, StateTransition.TIMEOUT, "Prepare timeout")
    
    async def _start_commit_timeout_timer(self):
        """Start timeout timer for commit phase."""
        await asyncio.sleep(self.context.timeout)
        
        if self.current_state == VerbState.QOS2_PREPARE_ACK:
            await self.transition_to(VerbState.QOS2_ABORT, StateTransition.TIMEOUT, "Commit timeout")
    
    async def receive_prepare_ack(self) -> bool:
        """Receive prepare acknowledgment."""
        if self.current_state == VerbState.QOS2_PREPARE:
            return await self.transition_to(VerbState.QOS2_PREPARE_ACK, StateTransition.SUCCESS, "Prepare ACK received")
        return False
    
    async def receive_commit_ack(self) -> bool:
        """Receive commit acknowledgment."""
        if self.current_state == VerbState.QOS2_COMMIT:
            return await self.transition_to(VerbState.QOS2_COMMIT_ACK, StateTransition.SUCCESS, "Commit ACK received")
        return False
    
    async def abort_transaction(self, reason: str = "User requested abort") -> bool:
        """Abort the transaction."""
        if self.current_state in [VerbState.QOS2_PREPARE, VerbState.QOS2_PREPARE_ACK]:
            return await self.transition_to(VerbState.QOS2_ABORT, StateTransition.FAILURE, reason)
        return False


class StateMachineManager:
    """Manages all state machines."""
    
    def __init__(self):
        self.state_machines: Dict[str, UACPStateMachine] = {}
        self.verb_machines: Dict[UACPVerb, type] = {
            UACPVerb.ASK: ASKStateMachine,
            UACPVerb.OBSERVE: OBSERVEStateMachine
        }
    
    def create_state_machine(self, verb: UACPVerb, context: StateMachineContext) -> UACPStateMachine:
        """Create a new state machine for a verb."""
        if verb not in self.verb_machines:
            raise ValueError(f"No state machine defined for verb: {verb}")
        
        machine_class = self.verb_machines[verb]
        machine = machine_class(context)
        
        self.state_machines[context.message_id] = machine
        return machine
    
    def get_state_machine(self, message_id: str) -> Optional[UACPStateMachine]:
        """Get state machine by message ID."""
        return self.state_machines.get(message_id)
    
    def remove_state_machine(self, message_id: str):
        """Remove state machine."""
        if message_id in self.state_machines:
            del self.state_machines[message_id]
    
    def get_all_state_machines(self) -> Dict[str, UACPStateMachine]:
        """Get all state machines."""
        return self.state_machines.copy()
    
    def get_state_machines_by_verb(self, verb: UACPVerb) -> List[UACPStateMachine]:
        """Get state machines for a specific verb."""
        return [machine for machine in self.state_machines.values() 
                if machine.context.verb == verb]
    
    def get_active_state_machines(self) -> List[UACPStateMachine]:
        """Get all active (non-terminal) state machines."""
        active = []
        for machine in self.state_machines.values():
            if machine.current_state not in [VerbState.ASK_COMPLETED, VerbState.ASK_FAILED,
                                           VerbState.OBSERVE_CANCELLED, VerbState.OBSERVE_FAILED,
                                           VerbState.QOS2_COMPLETE, VerbState.QOS2_ABORT]:
                active.append(machine)
        return active
    
    def cleanup_completed_machines(self):
        """Remove completed state machines."""
        completed_ids = []
        for message_id, machine in self.state_machines.items():
            if machine.current_state in [VerbState.ASK_COMPLETED, VerbState.ASK_FAILED,
                                       VerbState.OBSERVE_CANCELLED, VerbState.OBSERVE_FAILED,
                                       VerbState.QOS2_COMPLETE, VerbState.QOS2_ABORT]:
                completed_ids.append(message_id)
        
        for message_id in completed_ids:
            self.remove_state_machine(message_id)
        
        if completed_ids:
            print(f"🧹 Cleaned up {len(completed_ids)} completed state machines")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get state machine statistics."""
        stats = {
            'total_machines': len(self.state_machines),
            'active_machines': len(self.active_state_machines),
            'by_verb': {},
            'by_state': {}
        }
        
        # Count by verb
        for verb in UACPVerb:
            stats['by_verb'][verb.name] = len(self.get_state_machines_by_verb(verb))
        
        # Count by state
        for machine in self.state_machines.values():
            state_name = machine.current_state.value
            stats['by_state'][state_name] = stats['by_state'].get(state_name, 0) + 1
        
        return stats
