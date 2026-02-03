"""
µACP Routing & Addressing State Management

This module handles all routing and addressing state including:
- Neighbor tables (peer IPs, ports, agent IDs)
- NAT traversal state (mappings, keepalives)
- Multicast group membership tables
- Forwarding/routing caches (if multi-hop/swarm)
"""

import asyncio
import time
import ipaddress
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import socket
import struct


class RouteType(Enum):
    """Route types for different addressing schemes."""
    DIRECT = "direct"           # Direct connection
    NAT_MAPPED = "nat_mapped"  # NAT traversal
    MULTICAST = "multicast"     # Multicast group
    FORWARDED = "forwarded"     # Multi-hop forwarding
    PROXY = "proxy"             # Proxy/broker route


class NATState(Enum):
    """NAT traversal states."""
    UNKNOWN = "unknown"
    MAPPING = "mapping"
    MAPPED = "mapped"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class NeighborInfo:
    """Information about a neighbor agent."""
    agent_id: str
    ip_address: str
    port: int
    last_seen: float
    route_type: RouteType
    nat_state: NATState = NATState.UNKNOWN
    nat_mapping: Optional[Tuple[str, int]] = None
    keepalive_interval: float = 30.0
    last_keepalive: float = 0.0
    rtt_samples: List[float] = field(default_factory=list)
    max_rtt: float = 1000.0  # ms
    reliability_score: float = 1.0
    capabilities: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MulticastGroup:
    """Multicast group information."""
    group_address: str
    port: int
    ttl: int = 32
    members: Set[str] = field(default_factory=set)
    last_activity: float = 0.0
    max_members: int = 1000
    auto_cleanup: bool = True


@dataclass
class RouteEntry:
    """Routing table entry."""
    destination: str
    next_hop: str
    cost: float
    route_type: RouteType
    last_updated: float
    ttl: float = 300.0  # 5 minutes
    metrics: Dict[str, float] = field(default_factory=dict)


class UACPRouting:
    """µACP routing and addressing state management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.neighbors: Dict[str, NeighborInfo] = {}
        self.multicast_groups: Dict[str, MulticastGroup] = {}
        self.routing_table: Dict[str, RouteEntry] = {}
        self.nat_mappings: Dict[str, Dict[str, Any]] = {}
        self.forwarding_cache: Dict[str, List[str]] = {}
        
        # Configuration
        self.neighbor_timeout = self.config.get('neighbor_timeout', 300.0)
        self.keepalive_interval = self.config.get('keepalive_interval', 30.0)
        self.routing_update_interval = self.config.get('routing_update_interval', 60.0)
        self.max_neighbors = self.config.get('max_neighbors', 1000)
        self.max_routes = self.config.get('max_routes', 10000)
        
        # State tracking
        self.last_cleanup = time.time()
        self.cleanup_interval = 60.0
        self.stats = {
            'neighbors_added': 0,
            'neighbors_removed': 0,
            'routes_added': 0,
            'routes_removed': 0,
            'multicast_joins': 0,
            'multicast_leaves': 0,
            'nat_mappings': 0,
            'forwarding_events': 0
        }
        
        # Start background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the routing manager."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())
    
    async def stop(self):
        """Stop the routing manager."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
    
    def add_neighbor(self, agent_id: str, ip_address: str, port: int, 
                     route_type: RouteType = RouteType.DIRECT,
                     capabilities: Optional[Dict[str, Any]] = None) -> bool:
        """Add or update a neighbor."""
        if len(self.neighbors) >= self.max_neighbors:
            # Remove oldest neighbor
            oldest = min(self.neighbors.values(), key=lambda n: n.last_seen)
            del self.neighbors[oldest.agent_id]
            self.stats['neighbors_removed'] += 1
        
        neighbor = NeighborInfo(
            agent_id=agent_id,
            ip_address=ip_address,
            port=port,
            last_seen=time.time(),
            route_type=route_type,
            capabilities=capabilities or {}
        )
        
        self.neighbors[agent_id] = neighbor
        self.stats['neighbors_added'] += 1
        
        # Update routing table
        self._update_routing_table(agent_id, ip_address, route_type)
        
        return True
    
    def remove_neighbor(self, agent_id: str) -> bool:
        """Remove a neighbor."""
        if agent_id in self.neighbors:
            del self.neighbors[agent_id]
            self.stats['neighbors_removed'] += 1
            
            # Remove from routing table
            if agent_id in self.routing_table:
                del self.routing_table[agent_id]
                self.stats['routes_removed'] += 1
            
            return True
        return False
    
    def update_neighbor(self, agent_id: str, **kwargs) -> bool:
        """Update neighbor information."""
        if agent_id in self.neighbors:
            neighbor = self.neighbors[agent_id]
            for key, value in kwargs.items():
                if hasattr(neighbor, key):
                    setattr(neighbor, key, value)
            
            neighbor.last_seen = time.time()
            return True
        return False
    
    def get_neighbor(self, agent_id: str) -> Optional[NeighborInfo]:
        """Get neighbor information."""
        return self.neighbors.get(agent_id)
    
    def get_neighbors_by_type(self, route_type: RouteType) -> List[NeighborInfo]:
        """Get all neighbors of a specific route type."""
        return [n for n in self.neighbors.values() if n.route_type == route_type]
    
    def join_multicast_group(self, group_address: str, port: int, 
                            agent_id: str, ttl: int = 32) -> bool:
        """Join a multicast group."""
        group_key = f"{group_address}:{port}"
        
        if group_key not in self.multicast_groups:
            group = MulticastGroup(
                group_address=group_address,
                port=port,
                ttl=ttl
            )
            self.multicast_groups[group_key] = group
        else:
            group = self.multicast_groups[group_key]
        
        if len(group.members) < group.max_members:
            group.members.add(agent_id)
            group.last_activity = time.time()
            self.stats['multicast_joins'] += 1
            return True
        
        return False
    
    def leave_multicast_group(self, group_address: str, port: int, 
                             agent_id: str) -> bool:
        """Leave a multicast group."""
        group_key = f"{group_address}:{port}"
        
        if group_key in self.multicast_groups:
            group = self.multicast_groups[group_key]
            if agent_id in group.members:
                group.members.remove(agent_id)
                group.last_activity = time.time()
                self.stats['multicast_leaves'] += 1
                
                # Auto-cleanup empty groups
                if group.auto_cleanup and not group.members:
                    del self.multicast_groups[group_key]
                
                return True
        
        return False
    
    def get_multicast_members(self, group_address: str, port: int) -> Set[str]:
        """Get members of a multicast group."""
        group_key = f"{group_address}:{port}"
        group = self.multicast_groups.get(group_key)
        return group.members if group else set()
    
    def add_nat_mapping(self, internal_addr: str, internal_port: int,
                        external_addr: str, external_port: int,
                        agent_id: str) -> bool:
        """Add NAT mapping information."""
        mapping_key = f"{internal_addr}:{internal_port}"
        
        self.nat_mappings[mapping_key] = {
            'internal_addr': internal_addr,
            'internal_port': internal_port,
            'external_addr': external_addr,
            'external_port': external_port,
            'agent_id': agent_id,
            'created': time.time(),
            'last_used': time.time(),
            'expires': time.time() + 3600  # 1 hour
        }
        
        self.stats['nat_mappings'] += 1
        
        # Update neighbor NAT state
        if agent_id in self.neighbors:
            self.neighbors[agent_id].nat_state = NATState.MAPPED
            self.neighbors[agent_id].nat_mapping = (external_addr, external_port)
        
        return True
    
    def get_nat_mapping(self, internal_addr: str, internal_port: int) -> Optional[Dict[str, Any]]:
        """Get NAT mapping information."""
        mapping_key = f"{internal_addr}:{internal_port}"
        return self.nat_mappings.get(mapping_key)
    
    def add_route(self, destination: str, next_hop: str, cost: float,
                  route_type: RouteType, ttl: float = 300.0) -> bool:
        """Add or update a route."""
        if len(self.routing_table) >= self.max_routes:
            # Remove oldest route
            oldest = min(self.routing_table.values(), key=lambda r: r.last_updated)
            del self.routing_table[oldest.destination]
            self.stats['routes_removed'] += 1
        
        route = RouteEntry(
            destination=destination,
            next_hop=next_hop,
            cost=cost,
            route_type=route_type,
            last_updated=time.time(),
            ttl=ttl
        )
        
        self.routing_table[destination] = route
        self.stats['routes_added'] += 1
        return True
    
    def get_route(self, destination: str) -> Optional[RouteEntry]:
        """Get route to destination."""
        return self.routing_table.get(destination)
    
    def find_route(self, destination: str) -> Optional[RouteEntry]:
        """Find best route to destination."""
        if destination in self.routing_table:
            route = self.routing_table[destination]
            if time.time() - route.last_updated < route.ttl:
                return route
        
        # Try to find route through neighbors
        for neighbor in self.neighbors.values():
            if neighbor.agent_id == destination:
                return RouteEntry(
                    destination=destination,
                    next_hop=neighbor.ip_address,
                    cost=1.0,
                    route_type=neighbor.route_type,
                    last_updated=time.time()
                )
        
        return None
    
    def add_forwarding_cache(self, source: str, path: List[str]) -> None:
        """Add entry to forwarding cache."""
        self.forwarding_cache[source] = path
        self.stats['forwarding_events'] += 1
    
    def get_forwarding_path(self, source: str) -> List[str]:
        """Get forwarding path from cache."""
        return self.forwarding_cache.get(source, [])
    
    def _update_routing_table(self, agent_id: str, ip_address: str, route_type: RouteType):
        """Update routing table when neighbor changes."""
        cost = 1.0 if route_type == RouteType.DIRECT else 2.0
        
        self.add_route(
            destination=agent_id,
            next_hop=ip_address,
            cost=cost,
            route_type=route_type
        )
    
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
    
    async def _keepalive_loop(self):
        """Background keepalive loop."""
        while self._running:
            try:
                await asyncio.sleep(self.keepalive_interval)
                self._send_keepalives()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in keepalive loop: {e}")
    
    def _cleanup_expired(self):
        """Clean up expired entries."""
        now = time.time()
        
        # Clean up expired neighbors
        expired_neighbors = [
            agent_id for agent_id, neighbor in self.neighbors.items()
            if now - neighbor.last_seen > self.neighbor_timeout
        ]
        
        for agent_id in expired_neighbors:
            self.remove_neighbor(agent_id)
        
        # Clean up expired routes
        expired_routes = [
            dest for dest, route in self.routing_table.items()
            if now - route.last_updated > route.ttl
        ]
        
        for dest in expired_routes:
            del self.routing_table[dest]
            self.stats['routes_removed'] += 1
        
        # Clean up expired NAT mappings
        expired_mappings = [
            key for key, mapping in self.nat_mappings.items()
            if now > mapping['expires']
        ]
        
        for key in expired_mappings:
            del self.nat_mappings[key]
        
        # Clean up expired multicast groups
        expired_groups = [
            key for key, group in self.multicast_groups.items()
            if group.auto_cleanup and not group.members
        ]
        
        for key in expired_groups:
            del self.multicast_groups[key]
        
        self.last_cleanup = now
    
    def _send_keepalives(self):
        """Send keepalives to neighbors."""
        now = time.time()
        
        for neighbor in self.neighbors.values():
            if now - neighbor.last_keepalive >= neighbor.keepalive_interval:
                # Send keepalive (this would integrate with transport layer)
                neighbor.last_keepalive = now
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            **self.stats,
            'current_neighbors': len(self.neighbors),
            'current_routes': len(self.routing_table),
            'current_multicast_groups': len(self.multicast_groups),
            'current_nat_mappings': len(self.nat_mappings),
            'last_cleanup': self.last_cleanup
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export current routing state."""
        return {
            'neighbors': {
                agent_id: {
                    'ip_address': n.ip_address,
                    'port': n.port,
                    'route_type': n.route_type.value,
                    'nat_state': n.nat_state.value,
                    'last_seen': n.last_seen,
                    'capabilities': n.capabilities
                }
                for agent_id, n in self.neighbors.items()
            },
            'multicast_groups': {
                key: {
                    'group_address': g.group_address,
                    'port': g.port,
                    'member_count': len(g.members),
                    'last_activity': g.last_activity
                }
                for key, g in self.multicast_groups.items()
            },
            'routing_table': {
                dest: {
                    'next_hop': r.next_hop,
                    'cost': r.cost,
                    'route_type': r.route_type.value,
                    'last_updated': r.last_updated
                }
                for dest, r in self.routing_table.items()
            },
            'nat_mappings': self.nat_mappings,
            'stats': self.get_stats()
        }
