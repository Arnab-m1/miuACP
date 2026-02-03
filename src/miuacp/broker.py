"""
µACP Broker & Middleware State Management

This module handles all broker and middleware state including:
- Topic trees (trie for pub/sub matching)
- Retained messages (MQTT-style retained TELL)
- Brokered flow control credits
- Load-balancer / connection mapping state
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import re


class BrokerNodeType(Enum):
    """Broker node types."""
    ROOT = "root"
    TOPIC = "topic"
    WILDCARD = "wildcard"
    LEAF = "leaf"


class MessageRetention(Enum):
    """Message retention policies."""
    NONE = "none"
    RETAINED = "retained"
    PERSISTENT = "persistent"
    EXPIRING = "expiring"


class LoadBalancerStrategy(Enum):
    """Load balancer strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    STICKY = "sticky"


@dataclass
class TopicNode:
    """Node in the topic tree."""
    name: str
    node_type: BrokerNodeType
    parent: Optional['TopicNode'] = None
    children: Dict[str, 'TopicNode'] = field(default_factory=dict)
    subscribers: Set[str] = field(default_factory=set)
    retained_messages: List[Dict[str, Any]] = field(default_factory=list)
    max_retained: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetainedMessage:
    """Retained message information."""
    message_id: str
    topic: str
    payload: bytes
    qos: int
    created: float
    retention_policy: MessageRetention
    expires: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowControlCredit:
    """Flow control credit for a connection."""
    connection_id: str
    agent_id: str
    credits: int
    max_credits: int
    last_updated: float
    refill_rate: float  # credits per second
    refill_interval: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadBalancerTarget:
    """Load balancer target information."""
    target_id: str
    address: str
    port: int
    weight: int = 1
    max_connections: int = 1000
    current_connections: int = 0
    health_status: str = "healthy"
    last_health_check: float = 0.0
    response_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionMapping:
    """Connection mapping for load balancing."""
    connection_id: str
    agent_id: str
    target_id: str
    created: float
    last_activity: float
    sticky_session: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class UACPBroker:
    """µACP broker and middleware state management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Topic tree
        self.topic_root = TopicNode("", BrokerNodeType.ROOT)
        self.topic_cache: Dict[str, TopicNode] = {}  # topic -> node
        
        # Retained messages
        self.retained_messages: Dict[str, RetainedMessage] = {}
        self.topic_retained: Dict[str, List[str]] = defaultdict(list)  # topic -> message_ids
        
        # Flow control
        self.flow_credits: Dict[str, FlowControlCredit] = {}
        self.agent_credits: Dict[str, str] = {}  # agent_id -> connection_id
        
        # Load balancer
        self.load_balancer_targets: Dict[str, LoadBalancerTarget] = {}
        self.connection_mappings: Dict[str, ConnectionMapping] = {}
        self.agent_connections: Dict[str, str] = {}  # agent_id -> connection_id
        self.load_balancer_strategy = LoadBalancerStrategy.ROUND_ROBIN
        self.round_robin_index = 0
        
        # Configuration
        self.max_retained_messages = self.config.get('max_retained_messages', 10000)
        self.max_flow_credits = self.config.get('max_flow_credits', 1000)
        self.max_load_balancer_targets = self.config.get('max_load_balancer_targets', 100)
        self.max_connections = self.config.get('max_connections', 10000)
        
        self.retention_timeout = self.config.get('retention_timeout', 3600.0)  # 1 hour
        self.credit_refill_interval = self.config.get('credit_refill_interval', 1.0)
        self.health_check_interval = self.config.get('health_check_interval', 30.0)
        
        # State tracking
        self.last_cleanup = time.time()
        self.cleanup_interval = 60.0
        self.stats = {
            'topics_created': 0,
            'subscribers_added': 0,
            'retained_messages_stored': 0,
            'retained_messages_expired': 0,
            'flow_credits_created': 0,
            'connections_mapped': 0,
            'load_balanced_requests': 0,
            'health_checks': 0
        }
        
        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._credit_refill_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the broker manager."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._credit_refill_task = asyncio.create_task(self._credit_refill_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def stop(self):
        """Stop the broker manager."""
        self._running = False
        
        for task in [self._cleanup_task, self._credit_refill_task, self._health_check_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    # === Topic Tree Management ===
    
    def add_topic(self, topic: str) -> TopicNode:
        """Add a topic to the tree."""
        if topic in self.topic_cache:
            return self.topic_cache[topic]
        
        parts = topic.split('/') if topic else []
        current = self.topic_root
        
        for i, part in enumerate(parts):
            if part not in current.children:
                # Determine node type
                if part == '+':
                    node_type = BrokerNodeType.WILDCARD
                elif part == '#':
                    node_type = BrokerNodeType.WILDCARD
                elif i == len(parts) - 1:
                    node_type = BrokerNodeType.LEAF
                else:
                    node_type = BrokerNodeType.TOPIC
                
                # Create new node
                new_node = TopicNode(
                    name=part,
                    node_type=node_type,
                    parent=current
                )
                current.children[part] = new_node
                self.stats['topics_created'] += 1
            
            current = current.children[part]
        
        self.topic_cache[topic] = current
        return current
    
    def add_subscriber(self, topic: str, subscriber_id: str) -> bool:
        """Add a subscriber to a topic."""
        node = self.add_topic(topic)
        node.subscribers.add(subscriber_id)
        self.stats['subscribers_added'] += 1
        return True
    
    def remove_subscriber(self, topic: str, subscriber_id: str) -> bool:
        """Remove a subscriber from a topic."""
        if topic in self.topic_cache:
            node = self.topic_cache[topic]
            if subscriber_id in node.subscribers:
                node.subscribers.remove(subscriber_id)
                return True
        return False
    
    def get_subscribers(self, topic: str) -> Set[str]:
        """Get all subscribers for a topic (including wildcard matching)."""
        subscribers = set()
        
        # Direct match
        if topic in self.topic_cache:
            node = self.topic_cache[topic]
            subscribers.update(node.subscribers)
        
        # Wildcard matching
        self._find_wildcard_subscribers(self.topic_root, topic.split('/'), 0, subscribers)
        
        return subscribers
    
    def _find_wildcard_subscribers(self, node: TopicNode, parts: List[str], 
                                 depth: int, subscribers: Set[str]):
        """Recursively find subscribers using wildcard matching."""
        if depth >= len(parts):
            # Reached end of topic path
            subscribers.update(node.subscribers)
            return
        
        part = parts[depth]
        
        # Check exact match
        if part in node.children:
            self._find_wildcard_subscribers(node.children[part], parts, depth + 1, subscribers)
        
        # Check wildcard matches
        if '+' in node.children:
            self._find_wildcard_subscribers(node.children['+'], parts, depth + 1, subscribers)
        
        # Check multi-level wildcard
        if '#' in node.children:
            subscribers.update(node.children['#'].subscribers)
    
    def get_topic_tree(self) -> Dict[str, Any]:
        """Get the complete topic tree structure."""
        def serialize_node(node: TopicNode) -> Dict[str, Any]:
            return {
                'name': node.name,
                'type': node.node_type.value,
                'subscriber_count': len(node.subscribers),
                'retained_count': len(node.retained_messages),
                'children': {name: serialize_node(child) for name, child in node.children.items()}
            }
        
        return serialize_node(self.topic_root)
    
    # === Retained Message Management ===
    
    def store_retained_message(self, topic: str, message_id: str, payload: bytes,
                              qos: int, retention_policy: MessageRetention = MessageRetention.RETAINED,
                              expires: Optional[float] = None) -> bool:
        """Store a retained message."""
        if len(self.retained_messages) >= self.max_retained_messages:
            # Remove oldest retained message
            oldest = min(self.retained_messages.values(), key=lambda m: m.created)
            self._remove_retained_message(oldest.message_id)
        
        now = time.time()
        
        retained_message = RetainedMessage(
            message_id=message_id,
            topic=topic,
            payload=payload,
            qos=qos,
            created=now,
            expires=expires,
            retention_policy=retention_policy
        )
        
        self.retained_messages[message_id] = retained_message
        self.topic_retained[topic].append(message_id)
        
        # Limit retained messages per topic
        if len(self.topic_retained[topic]) > 10:
            oldest_msg_id = self.topic_retained[topic].pop(0)
            if oldest_msg_id in self.retained_messages:
                del self.retained_messages[oldest_msg_id]
        
        self.stats['retained_messages_stored'] += 1
        return True
    
    def get_retained_messages(self, topic: str) -> List[RetainedMessage]:
        """Get retained messages for a topic."""
        message_ids = self.topic_retained.get(topic, [])
        return [self.retained_messages[msg_id] for msg_id in message_ids 
                if msg_id in self.retained_messages]
    
    def remove_retained_message(self, message_id: str) -> bool:
        """Remove a retained message."""
        return self._remove_retained_message(message_id)
    
    def _remove_retained_message(self, message_id: str) -> bool:
        """Remove a retained message."""
        if message_id in self.retained_messages:
            message = self.retained_messages[message_id]
            
            # Remove from topic index
            if message.topic in self.topic_retained:
                if message_id in self.topic_retained[message.topic]:
                    self.topic_retained[message.topic].remove(message_id)
            
            del self.retained_messages[message_id]
            return True
        
        return False
    
    # === Flow Control Management ===
    
    def create_flow_credit(self, connection_id: str, agent_id: str,
                           max_credits: int, refill_rate: float) -> bool:
        """Create flow control credit for a connection."""
        if len(self.flow_credits) >= self.max_flow_credits:
            # Remove oldest credit entry
            oldest = min(self.flow_credits.values(), key=lambda c: c.last_updated)
            del self.flow_credits[oldest.connection_id]
            if oldest.agent_id in self.agent_credits:
                del self.agent_credits[oldest.agent_id]
        
        now = time.time()
        
        credit = FlowControlCredit(
            connection_id=connection_id,
            agent_id=agent_id,
            credits=max_credits,
            max_credits=max_credits,
            last_updated=now,
            refill_rate=refill_rate
        )
        
        self.flow_credits[connection_id] = credit
        self.agent_credits[agent_id] = connection_id
        
        self.stats['flow_credits_created'] += 1
        return True
    
    def consume_credit(self, connection_id: str, amount: int = 1) -> bool:
        """Consume flow control credit."""
        if connection_id in self.flow_credits:
            credit = self.flow_credits[connection_id]
            if credit.credits >= amount:
                credit.credits -= amount
                credit.last_updated = time.time()
                return True
        return False
    
    def get_credit_status(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get flow control credit status."""
        if connection_id in self.flow_credits:
            credit = self.flow_credits[connection_id]
            return {
                'credits': credit.credits,
                'max_credits': credit.max_credits,
                'refill_rate': credit.refill_rate,
                'last_updated': credit.last_updated
            }
        return None
    
    def refill_credits(self):
        """Refill flow control credits."""
        now = time.time()
        
        for credit in self.flow_credits.values():
            time_since_update = now - credit.last_updated
            if time_since_update >= credit.refill_interval:
                refill_amount = int(credit.refill_rate * time_since_update)
                credit.credits = min(credit.max_credits, credit.credits + refill_amount)
                credit.last_updated = now
    
    # === Load Balancer Management ===
    
    def add_load_balancer_target(self, target_id: str, address: str, port: int,
                                weight: int = 1, max_connections: int = 1000) -> bool:
        """Add a load balancer target."""
        if len(self.load_balancer_targets) >= self.max_load_balancer_targets:
            # Remove target with least connections
            least_loaded = min(self.load_balancer_targets.values(), 
                              key=lambda t: t.current_connections)
            del self.load_balancer_targets[least_loaded.target_id]
        
        target = LoadBalancerTarget(
            target_id=target_id,
            address=address,
            port=port,
            weight=weight,
            max_connections=max_connections
        )
        
        self.load_balancer_targets[target_id] = target
        return True
    
    def get_load_balancer_target(self, target_id: str) -> Optional[LoadBalancerTarget]:
        """Get load balancer target by ID."""
        return self.load_balancer_targets.get(target_id)
    
    def select_target(self, agent_id: str, sticky: bool = False) -> Optional[str]:
        """Select a load balancer target."""
        if not self.load_balancer_targets:
            return None
        
        if sticky and agent_id in self.agent_connections:
            # Return existing connection target
            connection_id = self.agent_connections[agent_id]
            if connection_id in self.connection_mappings:
                return self.connection_mappings[connection_id].target_id
        
        if self.load_balancer_strategy == LoadBalancerStrategy.ROUND_ROBIN:
            return self._round_robin_select()
        elif self.load_balancer_strategy == LoadBalancerStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select()
        elif self.load_balancer_strategy == LoadBalancerStrategy.WEIGHTED:
            return self._weighted_select()
        else:
            return self._round_robin_select()
    
    def _round_robin_select(self) -> Optional[str]:
        """Round-robin target selection."""
        if not self.load_balancer_targets:
            return None
        
        targets = list(self.load_balancer_targets.keys())
        if not targets:
            return None
        
        target_id = targets[self.round_robin_index % len(targets)]
        self.round_robin_index = (self.round_robin_index + 1) % len(targets)
        return target_id
    
    def _least_connections_select(self) -> Optional[str]:
        """Least connections target selection."""
        if not self.load_balancer_targets:
            return None
        
        return min(self.load_balancer_targets.values(), 
                  key=lambda t: t.current_connections).target_id
    
    def _weighted_select(self) -> Optional[str]:
        """Weighted target selection."""
        if not self.load_balancer_targets:
            return None
        
        # Simple weighted random selection
        total_weight = sum(t.weight for t in self.load_balancer_targets.values())
        if total_weight == 0:
            return self._round_robin_select()
        
        import random
        rand = random.uniform(0, total_weight)
        current_weight = 0
        
        for target in self.load_balancer_targets.values():
            current_weight += target.weight
            if rand <= current_weight:
                return target.target_id
        
        return list(self.load_balancer_targets.keys())[-1]
    
    def map_connection(self, connection_id: str, agent_id: str, target_id: str,
                       sticky: bool = False) -> bool:
        """Map a connection to a load balancer target."""
        if len(self.connection_mappings) >= self.max_connections:
            # Remove oldest connection
            oldest = min(self.connection_mappings.values(), key=lambda c: c.created)
            self._remove_connection_mapping(oldest.connection_id)
        
        now = time.time()
        
        mapping = ConnectionMapping(
            connection_id=connection_id,
            agent_id=agent_id,
            target_id=target_id,
            created=now,
            last_activity=now,
            sticky_session=sticky
        )
        
        self.connection_mappings[connection_id] = mapping
        self.agent_connections[agent_id] = connection_id
        
        # Update target connection count
        if target_id in self.load_balancer_targets:
            self.load_balancer_targets[target_id].current_connections += 1
        
        self.stats['connections_mapped'] += 1
        return True
    
    def remove_connection_mapping(self, connection_id: str) -> bool:
        """Remove a connection mapping."""
        return self._remove_connection_mapping(connection_id)
    
    def _remove_connection_mapping(self, connection_id: str) -> bool:
        """Remove a connection mapping."""
        if connection_id in self.connection_mappings:
            mapping = self.connection_mappings[connection_id]
            
            # Remove from agent connections
            if mapping.agent_id in self.agent_connections:
                del self.agent_connections[mapping.agent_id]
            
            # Update target connection count
            if mapping.target_id in self.load_balancer_targets:
                target = self.load_balancer_targets[mapping.target_id]
                target.current_connections = max(0, target.current_connections - 1)
            
            del self.connection_mappings[connection_id]
            return True
        
        return False
    
    def update_connection_activity(self, connection_id: str) -> bool:
        """Update connection activity timestamp."""
        if connection_id in self.connection_mappings:
            self.connection_mappings[connection_id].last_activity = time.time()
            return True
        return False
    
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
    
    async def _credit_refill_loop(self):
        """Background credit refill loop."""
        while self._running:
            try:
                await asyncio.sleep(self.credit_refill_interval)
                self.refill_credits()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in credit refill loop: {e}")
    
    async def _health_check_loop(self):
        """Background health check loop."""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in health check loop: {e}")
    
    def _cleanup_expired(self):
        """Clean up expired entries."""
        now = time.time()
        
        # Clean up expired retained messages
        expired_messages = [
            msg_id for msg_id, message in self.retained_messages.items()
            if message.expires and now > message.expires
        ]
        
        for msg_id in expired_messages:
            self._remove_retained_message(msg_id)
            self.stats['retained_messages_expired'] += 1
        
        # Clean up expired connection mappings
        expired_connections = [
            conn_id for conn_id, mapping in self.connection_mappings.items()
            if now - mapping.last_activity > 3600  # 1 hour
        ]
        
        for conn_id in expired_connections:
            self._remove_connection_mapping(conn_id)
        
        self.last_cleanup = now
    
    def _perform_health_checks(self):
        """Perform health checks on load balancer targets."""
        now = time.time()
        
        for target in self.load_balancer_targets.values():
            if now - target.last_health_check >= self.health_check_interval:
                # Simple health check - could be extended with actual network checks
                if target.current_connections < target.max_connections:
                    target.health_status = "healthy"
                else:
                    target.health_status = "overloaded"
                
                target.last_health_check = now
                self.stats['health_checks'] += 1
    
    # === Statistics and Export ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get broker statistics."""
        return {
            **self.stats,
            'current_topics': len(self.topic_cache),
            'current_retained_messages': len(self.retained_messages),
            'current_flow_credits': len(self.flow_credits),
            'current_load_balancer_targets': len(self.load_balancer_targets),
            'current_connections': len(self.connection_mappings),
            'last_cleanup': self.last_cleanup
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export current broker state."""
        return {
            'topic_tree': self.get_topic_tree(),
            'retained_messages': {
                msg_id: {
                    'topic': msg.topic,
                    'qos': msg.qos,
                    'created': msg.created,
                    'expires': msg.expires,
                    'retention_policy': msg.retention_policy.value
                }
                for msg_id, msg in self.retained_messages.items()
            },
            'flow_credits': {
                conn_id: {
                    'agent_id': credit.agent_id,
                    'credits': credit.credits,
                    'max_credits': credit.max_credits,
                    'refill_rate': credit.refill_rate
                }
                for conn_id, credit in self.flow_credits.items()
            },
            'load_balancer_targets': {
                target_id: {
                    'address': target.address,
                    'port': target.port,
                    'weight': target.weight,
                    'current_connections': target.current_connections,
                    'max_connections': target.max_connections,
                    'health_status': target.health_status
                }
                for target_id, target in self.load_balancer_targets.items()
            },
            'connection_mappings': {
                conn_id: {
                    'agent_id': mapping.agent_id,
                    'target_id': mapping.target_id,
                    'created': mapping.created,
                    'sticky_session': mapping.sticky_session
                }
                for conn_id, mapping in self.connection_mappings.items()
            },
            'stats': self.get_stats()
        }
