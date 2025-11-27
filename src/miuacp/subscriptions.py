"""
µACP Subscription & Dialogue State Management

This module handles all subscription and dialogue state including:
- OBSERVE / subscription tables (topic → list of subscribers)
- Dialogue / conversation state (Conv-ID mappings)
- Pending correlation (ASK ↔ response Corr-ID)
- Contract/negotiation contexts (if multi-agent tasks span multiple messages)
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import re


class SubscriptionState(Enum):
    """Subscription states."""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    ERROR = "error"


class DialogueState(Enum):
    """Dialogue states."""
    INITIATED = "initiated"
    ACTIVE = "active"
    WAITING_RESPONSE = "waiting_response"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CorrelationState(Enum):
    """Correlation states."""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESPONDED = "responded"
    TIMEOUT = "timeout"
    FAILED = "failed"


class ContractState(Enum):
    """Contract/negotiation states."""
    PROPOSED = "proposed"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Subscription:
    """Subscription information."""
    subscription_id: str
    topic: str
    subscriber_id: str
    state: SubscriptionState
    created: float
    expires: Optional[float] = None
    last_activity: float = 0.0
    filters: Dict[str, Any] = field(default_factory=dict)
    qos: int = 0
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dialogue:
    """Dialogue/conversation state."""
    dialogue_id: str
    conv_id: str
    initiator_id: str
    participant_ids: Set[str]
    state: DialogueState
    created: float
    last_activity: float
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 300.0  # 5 minutes
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Correlation:
    """ASK-response correlation tracking."""
    correlation_id: str
    ask_message_id: str
    asker_id: str
    responder_id: str
    state: CorrelationState
    created: float
    timeout: float = 30.0  # 30 seconds
    retry_count: int = 0
    max_retries: int = 3
    last_retry: float = 0.0
    response_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Contract:
    """Contract/negotiation context."""
    contract_id: str
    contract_type: str
    initiator_id: str
    participant_ids: Set[str]
    state: ContractState
    created: float
    expires: float
    terms: Dict[str, Any] = field(default_factory=dict)
    commitments: List[Dict[str, Any]] = field(default_factory=list)
    last_activity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class UACPSubscriptions:
    """µACP subscription and dialogue state management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Subscription management
        self.subscriptions: Dict[str, Subscription] = {}
        self.topic_subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.subscriber_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Dialogue management
        self.dialogues: Dict[str, Dialogue] = {}
        self.conv_dialogues: Dict[str, str] = {}  # conv_id -> dialogue_id
        
        # Correlation management
        self.correlations: Dict[str, Correlation] = {}
        self.message_correlations: Dict[str, str] = {}  # message_id -> correlation_id
        
        # Contract management
        self.contracts: Dict[str, Contract] = {}
        self.agent_contracts: Dict[str, Set[str]] = defaultdict(set)
        
        # Configuration
        self.max_subscriptions = self.config.get('max_subscriptions', 10000)
        self.max_dialogues = self.config.get('max_dialogues', 1000)
        self.max_correlations = self.config.get('max_correlations', 10000)
        self.max_contracts = self.config.get('max_contracts', 1000)
        
        self.subscription_timeout = self.config.get('subscription_timeout', 3600.0)
        self.dialogue_timeout = self.config.get('dialogue_timeout', 300.0)
        self.correlation_timeout = self.config.get('correlation_timeout', 30.0)
        self.contract_timeout = self.config.get('contract_timeout', 1800.0)
        
        # State tracking
        self.last_cleanup = time.time()
        self.cleanup_interval = 60.0
        self.stats = {
            'subscriptions_created': 0,
            'subscriptions_cancelled': 0,
            'dialogues_created': 0,
            'dialogues_completed': 0,
            'correlations_created': 0,
            'correlations_completed': 0,
            'contracts_created': 0,
            'contracts_completed': 0,
            'messages_delivered': 0,
            'topic_matches': 0
        }
        
        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the subscription manager."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the subscription manager."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    # === Subscription Management ===
    
    def create_subscription(self, topic: str, subscriber_id: str, 
                           filters: Optional[Dict[str, Any]] = None,
                           qos: int = 0, callback: Optional[Callable] = None,
                           expires: Optional[float] = None) -> str:
        """Create a new subscription."""
        if len(self.subscriptions) >= self.max_subscriptions:
            # Remove oldest subscription
            oldest = min(self.subscriptions.values(), key=lambda s: s.created)
            self._remove_subscription(oldest.subscription_id)
        
        subscription_id = str(uuid.uuid4())
        now = time.time()
        
        subscription = Subscription(
            subscription_id=subscription_id,
            topic=topic,
            subscriber_id=subscriber_id,
            state=SubscriptionState.ACTIVE,
            created=now,
            expires=expires,
            last_activity=now,
            filters=filters or {},
            qos=qos,
            callback=callback
        )
        
        self.subscriptions[subscription_id] = subscription
        self.topic_subscribers[topic].add(subscription_id)
        self.subscriber_subscriptions[subscriber_id].add(subscription_id)
        
        self.stats['subscriptions_created'] += 1
        return subscription_id
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription."""
        return self._remove_subscription(subscription_id)
    
    def _remove_subscription(self, subscription_id: str) -> bool:
        """Remove a subscription."""
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            
            # Remove from topic subscribers
            if subscription.topic in self.topic_subscribers:
                self.topic_subscribers[subscription.topic].discard(subscription_id)
                if not self.topic_subscribers[subscription.topic]:
                    del self.topic_subscribers[subscription.topic]
            
            # Remove from subscriber subscriptions
            if subscription.subscriber_id in self.subscriber_subscriptions:
                self.subscriber_subscriptions[subscription.subscriber_id].discard(subscription_id)
                if not self.subscriber_subscriptions[subscription.subscriber_id]:
                    del self.subscriber_subscriptions[subscription.subscriber_id]
            
            del self.subscriptions[subscription_id]
            self.stats['subscriptions_cancelled'] += 1
            return True
        
        return False
    
    def get_subscribers_for_topic(self, topic: str) -> List[str]:
        """Get all subscribers for a topic (including wildcard matching)."""
        subscribers = set()
        
        # Direct match
        if topic in self.topic_subscribers:
            for sub_id in self.topic_subscribers[topic]:
                if sub_id in self.subscriptions:
                    subscription = self.subscriptions[sub_id]
                    if subscription.state == SubscriptionState.ACTIVE:
                        subscribers.add(subscription.subscriber_id)
        
        # Wildcard matching
        for sub_topic, sub_ids in self.topic_subscribers.items():
            if self._topic_matches(topic, sub_topic):
                for sub_id in sub_ids:
                    if sub_id in self.subscriptions:
                        subscription = self.subscriptions[sub_id]
                        if subscription.state == SubscriptionState.ACTIVE:
                            subscribers.add(subscription.subscriber_id)
        
        self.stats['topic_matches'] += 1
        return list(subscribers)
    
    def _topic_matches(self, message_topic: str, subscription_topic: str) -> bool:
        """Check if a message topic matches a subscription topic with wildcards."""
        # Convert wildcard patterns to regex
        pattern = subscription_topic.replace('+', '[^/]+').replace('#', '.*')
        return bool(re.match(pattern, message_topic))
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID."""
        return self.subscriptions.get(subscription_id)
    
    def get_subscriptions_for_subscriber(self, subscriber_id: str) -> List[Subscription]:
        """Get all subscriptions for a subscriber."""
        subscription_ids = self.subscriber_subscriptions.get(subscriber_id, set())
        return [self.subscriptions[sub_id] for sub_id in subscription_ids 
                if sub_id in self.subscriptions]
    
    # === Dialogue Management ===
    
    def create_dialogue(self, conv_id: str, initiator_id: str, 
                        participant_ids: Set[str], timeout: float = 300.0,
                        context: Optional[Dict[str, Any]] = None) -> str:
        """Create a new dialogue."""
        if len(self.dialogues) >= self.max_dialogues:
            # Remove oldest dialogue
            oldest = min(self.dialogues.values(), key=lambda d: d.created)
            del self.dialogues[oldest.dialogue_id]
            if oldest.conv_id in self.conv_dialogues:
                del self.conv_dialogues[oldest.conv_id]
        
        dialogue_id = str(uuid.uuid4())
        now = time.time()
        
        dialogue = Dialogue(
            dialogue_id=dialogue_id,
            conv_id=conv_id,
            initiator_id=initiator_id,
            participant_ids=participant_ids,
            state=DialogueState.INITIATED,
            created=now,
            last_activity=now,
            timeout=timeout,
            context=context or {}
        )
        
        self.dialogues[dialogue_id] = dialogue
        self.conv_dialogues[conv_id] = dialogue_id
        
        self.stats['dialogues_created'] += 1
        return dialogue_id
    
    def update_dialogue_state(self, dialogue_id: str, new_state: DialogueState,
                             message: Optional[Dict[str, Any]] = None) -> bool:
        """Update dialogue state."""
        if dialogue_id in self.dialogues:
            dialogue = self.dialogues[dialogue_id]
            dialogue.state = new_state
            dialogue.last_activity = time.time()
            
            if message:
                dialogue.messages.append(message)
            
            if new_state in [DialogueState.COMPLETED, DialogueState.TIMEOUT, DialogueState.FAILED]:
                self.stats['dialogues_completed'] += 1
            
            return True
        
        return False
    
    def get_dialogue(self, dialogue_id: str) -> Optional[Dialogue]:
        """Get dialogue by ID."""
        return self.dialogues.get(dialogue_id)
    
    def get_dialogue_by_conv_id(self, conv_id: str) -> Optional[Dialogue]:
        """Get dialogue by conversation ID."""
        dialogue_id = self.conv_dialogues.get(conv_id)
        return self.dialogues.get(dialogue_id) if dialogue_id else None
    
    def add_message_to_dialogue(self, dialogue_id: str, message: Dict[str, Any]) -> bool:
        """Add a message to a dialogue."""
        if dialogue_id in self.dialogues:
            dialogue = self.dialogues[dialogue_id]
            dialogue.messages.append(message)
            dialogue.last_activity = time.time()
            self.stats['messages_delivered'] += 1
            return True
        
        return False
    
    # === Correlation Management ===
    
    def create_correlation(self, ask_message_id: str, asker_id: str, 
                          responder_id: str, timeout: float = 30.0) -> str:
        """Create a new correlation for ASK-response tracking."""
        if len(self.correlations) >= self.max_correlations:
            # Remove oldest correlation
            oldest = min(self.correlations.values(), key=lambda c: c.created)
            del self.correlations[oldest.correlation_id]
            if oldest.ask_message_id in self.message_correlations:
                del self.message_correlations[oldest.ask_message_id]
        
        correlation_id = str(uuid.uuid4())
        now = time.time()
        
        correlation = Correlation(
            correlation_id=correlation_id,
            ask_message_id=ask_message_id,
            asker_id=asker_id,
            responder_id=responder_id,
            state=CorrelationState.PENDING,
            created=now,
            timeout=timeout
        )
        
        self.correlations[correlation_id] = correlation
        self.message_correlations[ask_message_id] = correlation_id
        
        self.stats['correlations_created'] += 1
        return correlation_id
    
    def update_correlation_state(self, correlation_id: str, new_state: CorrelationState,
                                response_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update correlation state."""
        if correlation_id in self.correlations:
            correlation = self.correlations[correlation_id]
            correlation.state = new_state
            
            if response_data:
                correlation.response_data = response_data
            
            if new_state in [CorrelationState.RESPONDED, CorrelationState.TIMEOUT, CorrelationState.FAILED]:
                self.stats['correlations_completed'] += 1
            
            return True
        
        return False
    
    def get_correlation(self, correlation_id: str) -> Optional[Correlation]:
        """Get correlation by ID."""
        return self.correlations.get(correlation_id)
    
    def get_correlation_by_message(self, message_id: str) -> Optional[Correlation]:
        """Get correlation by message ID."""
        correlation_id = self.message_correlations.get(message_id)
        return self.correlations.get(correlation_id) if correlation_id else None
    
    def retry_correlation(self, correlation_id: str) -> bool:
        """Retry a correlation."""
        if correlation_id in self.correlations:
            correlation = self.correlations[correlation_id]
            if correlation.retry_count < correlation.max_retries:
                correlation.retry_count += 1
                correlation.last_retry = time.time()
                correlation.state = CorrelationState.PENDING
                return True
        
        return False
    
    # === Contract Management ===
    
    def create_contract(self, contract_type: str, initiator_id: str,
                        participant_ids: Set[str], terms: Dict[str, Any],
                        expires: float) -> str:
        """Create a new contract/negotiation context."""
        if len(self.contracts) >= self.max_contracts:
            # Remove oldest contract
            oldest = min(self.contracts.values(), key=lambda c: c.created)
            del self.contracts[oldest.contract_id]
            self._remove_contract_from_agents(oldest.contract_id)
        
        contract_id = str(uuid.uuid4())
        now = time.time()
        
        contract = Contract(
            contract_id=contract_id,
            contract_type=contract_type,
            initiator_id=initiator_id,
            participant_ids=participant_ids,
            state=ContractState.PROPOSED,
            created=now,
            expires=expires,
            terms=terms
        )
        
        self.contracts[contract_id] = contract
        self._add_contract_to_agents(contract_id, participant_ids)
        
        self.stats['contracts_created'] += 1
        return contract_id
    
    def update_contract_state(self, contract_id: str, new_state: ContractState,
                             commitment: Optional[Dict[str, Any]] = None) -> bool:
        """Update contract state."""
        if contract_id in self.contracts:
            contract = self.contracts[contract_id]
            contract.state = new_state
            contract.last_activity = time.time()
            
            if commitment:
                contract.commitments.append(commitment)
            
            if new_state in [ContractState.COMPLETED, ContractState.REJECTED, ContractState.CANCELLED, ContractState.EXPIRED]:
                self.stats['contracts_completed'] += 1
            
            return True
        
        return False
    
    def get_contract(self, contract_id: str) -> Optional[Contract]:
        """Get contract by ID."""
        return self.contracts.get(contract_id)
    
    def get_contracts_for_agent(self, agent_id: str) -> List[Contract]:
        """Get all contracts for an agent."""
        contract_ids = self.agent_contracts.get(agent_id, set())
        return [self.contracts[contract_id] for contract_id in contract_ids 
                if contract_id in self.contracts]
    
    def _add_contract_to_agents(self, contract_id: str, agent_ids: Set[str]):
        """Add contract reference to agents."""
        for agent_id in agent_ids:
            self.agent_contracts[agent_id].add(contract_id)
    
    def _remove_contract_from_agents(self, contract_id: str):
        """Remove contract reference from agents."""
        for agent_ids in self.agent_contracts.values():
            agent_ids.discard(contract_id)
    
    # === Background Tasks ===
    
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
    
    def _cleanup_expired(self):
        """Clean up expired entries."""
        now = time.time()
        
        # Clean up expired subscriptions
        expired_subscriptions = [
            sub_id for sub_id, subscription in self.subscriptions.items()
            if subscription.expires and now > subscription.expires
        ]
        
        for sub_id in expired_subscriptions:
            self._remove_subscription(sub_id)
        
        # Clean up expired dialogues
        expired_dialogues = [
            dialogue_id for dialogue_id, dialogue in self.dialogues.items()
            if now - dialogue.last_activity > dialogue.timeout
        ]
        
        for dialogue_id in expired_dialogues:
            dialogue = self.dialogues[dialogue_id]
            if dialogue.conv_id in self.conv_dialogues:
                del self.conv_dialogues[dialogue.conv_id]
            del self.dialogues[dialogue_id]
        
        # Clean up expired correlations
        expired_correlations = [
            corr_id for corr_id, correlation in self.correlations.items()
            if now - correlation.created > correlation.timeout
        ]
        
        for corr_id in expired_correlations:
            correlation = self.correlations[corr_id]
            if correlation.ask_message_id in self.message_correlations:
                del self.message_correlations[correlation.ask_message_id]
            del self.correlations[corr_id]
        
        # Clean up expired contracts
        expired_contracts = [
            contract_id for contract_id, contract in self.contracts.items()
            if now > contract.expires
        ]
        
        for contract_id in expired_contracts:
            contract = self.contracts[contract_id]
            self._remove_contract_from_agents(contract_id)
            del self.contracts[contract_id]
        
        self.last_cleanup = now
    
    # === Statistics and Export ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get subscription statistics."""
        return {
            **self.stats,
            'current_subscriptions': len(self.subscriptions),
            'current_dialogues': len(self.dialogues),
            'current_correlations': len(self.correlations),
            'current_contracts': len(self.contracts),
            'active_topics': len(self.topic_subscribers),
            'last_cleanup': self.last_cleanup
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export current subscription state."""
        return {
            'subscriptions': {
                sub_id: {
                    'topic': sub.topic,
                    'subscriber_id': sub.subscriber_id,
                    'state': sub.state.value,
                    'created': sub.created,
                    'expires': sub.expires,
                    'filters': sub.filters,
                    'qos': sub.qos
                }
                for sub_id, sub in self.subscriptions.items()
            },
            'dialogues': {
                dialogue_id: {
                    'conv_id': dialogue.conv_id,
                    'initiator_id': dialogue.initiator_id,
                    'participant_ids': list(dialogue.participant_ids),
                    'state': dialogue.state.value,
                    'created': dialogue.created,
                    'message_count': len(dialogue.messages)
                }
                for dialogue_id, dialogue in self.dialogues.items()
            },
            'correlations': {
                corr_id: {
                    'ask_message_id': corr.ask_message_id,
                    'asker_id': corr.asker_id,
                    'responder_id': corr.responder_id,
                    'state': corr.state.value,
                    'created': corr.created,
                    'retry_count': corr.retry_count
                }
                for corr_id, corr in self.correlations.items()
            },
            'contracts': {
                contract_id: {
                    'contract_type': contract.contract_type,
                    'initiator_id': contract.initiator_id,
                    'participant_ids': list(contract.participant_ids),
                    'state': contract.state.value,
                    'created': contract.created,
                    'expires': contract.expires
                }
                for contract_id, contract in self.contracts.items()
            },
            'stats': self.get_stats()
        }
