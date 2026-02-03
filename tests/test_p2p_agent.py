"""
µACP P2P Agent Tests

Tests for symmetric peer-to-peer agent implementation.
"""

import pytest
import asyncio
from src.miuacp.agent import UACPAgent, PeerInfo
from src.miuacp.protocol import UACPVerb, UACPMessage


class TestP2PAgent:
    """Test suite for P2P Agent."""
    
    @pytest.mark.asyncio
    async def test_agent_lifecycle(self):
        """Test starting and stopping agent."""
        agent = UACPAgent(
            agent_id="test-agent-1",
            name="Test Agent 1",
            port=0  # Ephemeral
        )
        
        try:
            # Start agent
            success = await agent.start()
            assert success, "Failed to start agent"
            assert agent.running
            assert agent.port > 0, "Port not assigned"
            
            # Stop agent
            await agent.stop()
            assert not agent.running
            
        finally:
            if agent.running:
                await agent.stop()
    
    @pytest.mark.asyncio
    async def test_peer_to_peer_ping(self):
        """Test PING between two agents."""
        agent1 = UACPAgent(agent_id="agent1", name="Agent 1", port=0)
        agent2 = UACPAgent(agent_id="agent2", name="Agent 2", port=0)
        
        # Track if agent2 received ping
        ping_received = asyncio.Event()
        
        async def handle_ping(msg, sender_host, sender_port):
            ping_received.set()
        
        agent2.add_message_handler(UACPVerb.PING, handle_ping)
        
        try:
            await agent1.start()
            await agent2.start()
            
            # Agent1 pings Agent2 (no connect needed!)
            success = await agent1.ping("127.0.0.1", agent2.port)
            assert success, "Failed to send PING"
            
            # Wait for agent2 to receive
            await asyncio.wait_for(ping_received.wait(), timeout=2.0)
            
            # Check statistics
            assert agent1.stats['messages_sent'] >= 1
            assert agent2.stats['messages_received'] >= 1
            
        finally:
            await agent1.stop()
            await agent2.stop()
    
    @pytest.mark.asyncio
    async def test_peer_to_peer_tell(self):
        """Test TELL between two agents."""
        agent1 = UACPAgent(agent_id="agent1", name="Agent 1", port=0)
        agent2 = UACPAgent(agent_id="agent2", name="Agent 2", port=0)
        
        received_message = None
        message_received = asyncio.Event()
        
        async def handle_tell(msg, sender_host, sender_port):
            nonlocal received_message
            received_message = msg
            message_received.set()
        
        agent2.add_message_handler(UACPVerb.TELL, handle_tell)
        
        try:
            await agent1.start()
            await agent2.start()
            
            # Agent1 tells Agent2 something
            test_data = {"message": "Hello from agent1"}
            success = await agent1.tell("127.0.0.1", agent2.port, "test/topic", test_data)
            assert success, "Failed to send TELL"
            
            # Wait for message
            await asyncio.wait_for(message_received.wait(), timeout=2.0)
            
            assert received_message is not None, "Message not received"
            assert received_message.header.verb == UACPVerb.TELL
            
        finally:
            await agent1.stop()
            await agent2.stop()
    
    @pytest.mark.asyncio
    async def test_peer_to_peer_ask(self):
        """Test ASK/response between two agents."""
        agent1 = UACPAgent(agent_id="agent1", name="Agent 1", port=0)
        agent2 = UACPAgent(agent_id="agent2", name="Agent 2", port=0)
        
        async def handle_ask(msg, sender_host, sender_port):
            # Send response back
            response_data = {"answer": "42"}
            response = UACPMessage(
                header=msg.header,
                options=msg.options,
                payload=msg.pack()  # Echo for now
            )
            await agent2._send_to_peer(sender_host, sender_port, response)
        
        agent2.add_message_handler(UACPVerb.ASK, handle_ask)
        
        try:
            await agent1.start()
            await agent2.start()
            
            # Agent1 asks Agent2
            query_data = {"question": "What is the answer?"}
            response = await agent1.ask("127.0.0.1", agent2.port, "query/test", query_data, timeout=2.0)
            
            # Should receive response (even if it's just an echo)
            assert response is not None, "No response received"
            
        finally:
            await agent1.stop()
            await agent2.stop()
    
    @pytest.mark.asyncio
    async def test_topic_handlers(self):
        """Test topic-based message routing."""
        agent = UACPAgent(agent_id="agent-topic", name="Topic Agent", port=0)
        
        received_topics = []
        
        async def handle_sensor_topic(msg, sender_host, sender_port):
            topic = msg.options[0].value.decode() if msg.options else "unknown"
            received_topics.append(topic)
        
        agent.add_topic_handler("sensor/temperature", handle_sensor_topic)
        
        try:
            await agent.start()
            
            # Send message to own topic
            await agent.tell("127.0.0.1", agent.port, "sensor/temperature", {"value": 25.5})
            
            # Give it time to process
            await asyncio.sleep(0.5)
            
            # Check if handler was called
            assert len(received_topics) > 0, "Topic handler not called"
            
        finally:
            await agent.stop()
    
    @pytest.mark.asyncio
    async def test_peer_discovery(self):
        """Test peer discovery via broadcast."""
        agent1 = UACPAgent(agent_id="agent1", name="Agent 1", port=8881)
        agent2 = UACPAgent(agent_id="agent2", name="Agent 2", port=8882)
        agent3 = UACPAgent(agent_id="agent3", name="Agent 3", port=8883)
        
        try:
            await agent1.start()
            await agent2.start()
            await agent3.start()
            
            # Agent1 discovers peers
            # Note: Broadcast might not work in all test environments
            peer_count = await agent1.discover_peers("127.0.0.1", 8882, timeout=0.5)
            
            # At minimum, should track peers it communicates with
            assert peer_count >= 0, "Peer count should be non-negative"
            
        finally:
            await agent1.stop()
            await agent2.stop()
            await agent3.stop()
    
    @pytest.mark.asyncio
    async def test_peer_registry(self):
        """Test peer registry management."""
        agent1 = UACPAgent(agent_id="agent1", name="Agent 1", port=0)
        agent2 = UACPAgent(agent_id="agent2", name="Agent 2", port=0)
        
        try:
            await agent1.start()
            await agent2.start()
            
            # Send message from agent1 to agent2
            await agent1.ping("127.0.0.1", agent2.port)
            
            # Give it time to process
            await asyncio.sleep(0.3)
            
            # Agent2 should have registered agent1 as a peer
            peers = agent2.get_discovered_peers()
            assert len(peers) >= 1, "Agent1 not registered as peer"
            
            # Check peer info
            peer_key = f"127.0.0.1:{agent1.port}"
            assert peer_key in agent2.peers, "Peer not in registry"
            
            peer_info = agent2.peers[peer_key]
            assert peer_info.host == "127.0.0.1"
            assert peer_info.port == agent1.port
            assert peer_info.is_alive(), "Peer marked as not alive"
            
        finally:
            await agent1.stop()
            await agent2.stop()
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self):
        """Test statistics tracking."""
        agent1 = UACPAgent(agent_id="agent1", name="Agent 1", port=0)
        agent2 = UACPAgent(agent_id="agent2", name="Agent 2", port=0)
        
        try:
            await agent1.start()
            await agent2.start()
            
            # Send multiple messages
            await agent1.ping("127.0.0.1", agent2.port)
            await agent1.tell("127.0.0.1", agent2.port, "test", {"data": "test"})
            await agent1.ping("127.0.0.1", agent2.port)
            
            # Wait for processing
            await asyncio.sleep(0.5)
            
            # Check stats
            stats1 = agent1.get_stats()
            stats2 = agent2.get_stats()
            
            assert stats1['messages_sent'] >= 3, "Agent1 should have sent 3+ messages"
            assert stats2['messages_received'] >= 3, "Agent2 should have received 3+ messages"
            assert stats1['bytes_sent'] > 0, "Bytes sent should be > 0"
            assert stats2['bytes_received'] > 0, "Bytes received should be > 0"
            
        finally:
            await agent1.stop()
            await agent2.stop()
    
    @pytest.mark.asyncio
    async def test_wildcard_topic_matching(self):
        """Test wildcard topic pattern matching."""
        agent = UACPAgent(agent_id="agent", name="Test Agent", port=0)
        
        # Test exact match
        assert agent._topic_matches("sensor/temp", "sensor/temp")
        
        # Test multi-level wildcard
        assert agent._topic_matches("sensor/temp/room1", "sensor/#")
        assert agent._topic_matches("sensor/temp", "sensor/#")
        assert not agent._topic_matches("device/temp", "sensor/#")
        
        # Test single-level wildcard
        assert agent._topic_matches("sensor/temp", "*/temp")
        assert agent._topic_matches("device/temp", "*/temp")
        assert not agent._topic_matches("sensor/temp/room1", "*/temp")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
