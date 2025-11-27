"""
µACP Discovery Implementation

Provides agent discovery functionality:
- Agent capability advertisement
- Service discovery
- Agent registry management
"""

import asyncio
import socket
import time
import json
import cbor2
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from .protocol import UACPProtocol, UACPMessage, UACPVerb, UACPOptionType
from .agent import UACPAgentInfo, UACPCapability


@dataclass
class UACPServiceInfo:
    """Service information for discovery."""
    service_id: str
    name: str
    description: str
    agent_host: str
    agent_port: int
    topics: List[str]
    capabilities: List[str]
    metadata: Dict[str, Any]


class UACPDiscovery:
    """µACP agent discovery service."""
    
    def __init__(self, 
                 multicast_group: str = "224.0.0.1",
                 discovery_port: int = 8889,
                 broadcast_interval: float = 30.0):
        
        self.multicast_group = multicast_group
        self.discovery_port = discovery_port
        self.broadcast_interval = broadcast_interval
        
        # Service registry
        self.services: Dict[str, UACPServiceInfo] = {}
        self.agents: Dict[str, UACPAgentInfo] = {}
        
        # Discovery socket
        self.socket: Optional[socket.socket] = None
        self.running = False
        
        # Background tasks
        self.broadcast_task: Optional[asyncio.Task] = None
        self.listen_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the discovery service."""
        if self.running:
            return
        
        try:
            # Create UDP socket for discovery
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to discovery port
            self.socket.bind(('', self.discovery_port))
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(self.multicast_group), socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            self.running = True
            
            # Start background tasks
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())
            self.listen_task = asyncio.create_task(self._listen_loop())
            
            print(f"µACP Discovery service started on {self.multicast_group}:{self.discovery_port}")
            
        except Exception as e:
            print(f"Failed to start discovery service: {e}")
            raise
    
    async def stop(self):
        """Stop the discovery service."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel background tasks
        if self.broadcast_task:
            self.broadcast_task.cancel()
        if self.listen_task:
            self.listen_task.cancel()
        
        # Close socket
        if self.socket:
            self.socket.close()
            self.socket = None
        
        print("µACP Discovery service stopped")
    
    def register_service(self, service_info: UACPServiceInfo):
        """Register a service for discovery."""
        self.services[service_info.service_id] = service_info
        
        # Also register the agent
        if hasattr(service_info, 'agent_info'):
            self.agents[service_info.agent_info.agent_id] = service_info.agent_info
    
    def unregister_service(self, service_id: str):
        """Unregister a service."""
        if service_id in self.services:
            del self.services[service_id]
    
    def get_service(self, service_id: str) -> Optional[UACPServiceInfo]:
        """Get service information by ID."""
        return self.services.get(service_id)
    
    def get_services_by_topic(self, topic: str) -> List[UACPServiceInfo]:
        """Get services that handle a specific topic."""
        matching_services = []
        for service in self.services.values():
            if topic in service.topics:
                matching_services.append(service)
        return matching_services
    
    def get_services_by_capability(self, capability: str) -> List[UACPServiceInfo]:
        """Get services that provide a specific capability."""
        matching_services = []
        for service in self.services.values():
            if capability in service.capabilities:
                matching_services.append(service)
        return matching_services
    
    def search_services(self, query: str) -> List[UACPServiceInfo]:
        """Search services by name, description, or capability."""
        matching_services = []
        query_lower = query.lower()
        
        for service in self.services.values():
            if (query_lower in service.name.lower() or
                query_lower in service.description.lower() or
                any(query_lower in cap.lower() for cap in service.capabilities)):
                matching_services.append(service)
        
        return matching_services
    
    async def _broadcast_loop(self):
        """Background task for broadcasting service advertisements."""
        while self.running:
            try:
                # Broadcast all registered services
                for service in self.services.values():
                    await self._broadcast_service(service)
                
                # Wait before next broadcast
                await asyncio.sleep(self.broadcast_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Broadcast error: {e}")
                await asyncio.sleep(5.0)
    
    async def _broadcast_service(self, service: UACPServiceInfo):
        """Broadcast a service advertisement."""
        try:
            # Create service advertisement message
            advertisement = {
                "type": "service_advertisement",
                "service_id": service.service_id,
                "name": service.name,
                "description": service.description,
                "host": service.agent_host,
                "port": service.agent_port,
                "topics": service.topics,
                "capabilities": service.capabilities,
                "metadata": service.metadata,
                "timestamp": time.time()
            }
            
            # Send to multicast group
            data = cbor2.dumps(advertisement)
            self.socket.sendto(data, (self.multicast_group, self.discovery_port))
            
        except Exception as e:
            print(f"Failed to broadcast service {service.service_id}: {e}")
    
    async def _listen_loop(self):
        """Background task for listening to discovery messages."""
        while self.running:
            try:
                # Receive discovery messages
                data, addr = self.socket.recvfrom(1024)
                sender_host, sender_port = addr
                
                # Parse message
                try:
                    message = cbor2.loads(data)
                    await self._handle_discovery_message(message, sender_host, sender_port)
                except Exception as e:
                    print(f"Failed to parse discovery message: {e}")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Discovery listen error: {e}")
                    await asyncio.sleep(1.0)
    
    async def _handle_discovery_message(self, message: Dict[str, Any], sender_host: str, sender_port: int):
        """Handle incoming discovery message."""
        msg_type = message.get("type")
        
        if msg_type == "service_advertisement":
            await self._handle_service_advertisement(message, sender_host, sender_port)
        elif msg_type == "service_query":
            await self._handle_service_query(message, sender_host, sender_port)
        elif msg_type == "service_response":
            await self._handle_service_response(message, sender_host, sender_port)
    
    async def _handle_service_advertisement(self, message: Dict[str, Any], sender_host: str, sender_port: int):
        """Handle service advertisement from another agent."""
        service_id = message.get("service_id")
        
        if service_id and service_id not in self.services:
            # Create service info
            service_info = UACPServiceInfo(
                service_id=service_id,
                name=message.get("name", "Unknown"),
                description=message.get("description", ""),
                agent_host=sender_host,
                agent_port=sender_port,
                topics=message.get("topics", []),
                capabilities=message.get("capabilities", []),
                metadata=message.get("metadata", {})
            )
            
            # Register service
            self.services[service_id] = service_info
            print(f"Discovered service: {service_info.name} ({service_id})")
    
    async def _handle_service_query(self, message: Dict[str, Any], sender_host: str, sender_port: int):
        """Handle service query from another agent."""
        query_type = message.get("query_type")
        query_value = message.get("query_value")
        
        matching_services = []
        
        if query_type == "topic":
            matching_services = self.get_services_by_topic(query_value)
        elif query_type == "capability":
            matching_services = self.get_services_by_capability(query_value)
        elif query_type == "search":
            matching_services = self.search_services(query_value)
        
        # Send response
        response = {
            "type": "service_response",
            "query_id": message.get("query_id"),
            "services": [
                {
                    "service_id": service.service_id,
                    "name": service.name,
                    "description": service.description,
                    "host": service.agent_host,
                    "port": service.agent_port,
                    "topics": service.topics,
                    "capabilities": service.capabilities
                }
                for service in matching_services
            ]
        }
        
        try:
            data = cbor2.dumps(response)
            self.socket.sendto(data, (sender_host, sender_port))
        except Exception as e:
            print(f"Failed to send service response: {e}")
    
    async def _handle_service_response(self, message: Dict[str, Any], sender_host: str, sender_port: int):
        """Handle service response from another agent."""
        # This could be used for caching or updating local service registry
        pass
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of registered services and agents."""
        return {
            "services_count": len(self.services),
            "agents_count": len(self.agents),
            "topics_covered": list(set(
                topic for service in self.services.values() for topic in service.topics
            )),
            "capabilities_available": list(set(
                cap for service in self.services.values() for cap in service.capabilities
            )),
            "services": [
                {
                    "id": service.service_id,
                    "name": service.name,
                    "host": f"{service.agent_host}:{service.agent_port}",
                    "topics": service.topics,
                    "capabilities": service.capabilities
                }
                for service in self.services.values()
            ]
        }


# Utility functions for discovery
def create_service_info(agent_info: UACPAgentInfo, 
                       host: str, 
                       port: int,
                       additional_metadata: Optional[Dict[str, Any]] = None) -> UACPServiceInfo:
    """Create service info from agent info."""
    metadata = additional_metadata or {}
    
    return UACPServiceInfo(
        service_id=f"service:{agent_info.agent_id}",
        name=agent_info.name,
        description=f"µACP Agent: {agent_info.name}",
        agent_host=host,
        agent_port=port,
        topics=agent_info.topics,
        capabilities=[cap.name for cap in agent_info.capabilities],
        metadata=metadata
    )


async def discover_agents(discovery: UACPDiscovery, 
                         query_type: str = "all",
                         query_value: str = "",
                         timeout: float = 10.0) -> List[UACPServiceInfo]:
    """Discover agents using the discovery service."""
    # Send discovery query
    query = {
        "type": "service_query",
        "query_id": str(uuid.uuid4()),
        "query_type": query_type,
        "query_value": query_value,
        "timestamp": time.time()
    }
    
    # Send query to discovery service
    data = cbor2.dumps(query)
    discovery.socket.sendto(data, (discovery.multicast_group, discovery.discovery_port))
    
    # Wait for responses
    await asyncio.sleep(timeout)
    
    # Return discovered services
    if query_type == "topic":
        return discovery.get_services_by_topic(query_value)
    elif query_type == "capability":
        return discovery.get_services_by_capability(query_value)
    elif query_type == "search":
        return discovery.search_services(query_value)
    else:
        return list(discovery.services.values())
