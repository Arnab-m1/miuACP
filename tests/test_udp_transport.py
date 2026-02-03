"""
µACP UDP Transport Tests

Tests for UDP P2P transport implementation.
"""

import pytest
import asyncio
from src.miuacp.udp_transport import UDPTransport


class TestUDPTransport:
    """Test suite for UDP transport."""
    
    @pytest.mark.asyncio
    async def test_bind_fixed_port(self):
        """Test binding to a specific port."""
        transport = UDPTransport()
        
        try:
            # Bind to fixed port
            success = await transport.bind("127.0.0.1", 9001)
            assert success, "Failed to bind to fixed port"
            
            # Check port
            assert transport.get_local_port() == 9001
            assert transport.is_bound()
            
        finally:
            transport.close()
    
    @pytest.mark.asyncio
    async def test_bind_ephemeral_port(self):
        """Test binding to ephemeral port (port=0)."""
        transport = UDPTransport()
        
        try:
            # Bind with port=0 (OS assigns)
            success = await transport.bind("127.0.0.1", 0)
            assert success, "Failed to bind to ephemeral port"
            
            # Port should be assigned
            port = transport.get_local_port()
            assert port > 0, "Ephemeral port not assigned"
            assert transport.is_bound()
            
        finally:
            transport.close()
    
    @pytest.mark.asyncio
    async def test_peer_to_peer_communication(self):
        """Test sending and receiving between two peers."""
        transport1 = UDPTransport()
        transport2 = UDPTransport()
        
        try:
            # Bind both transports
            await transport1.bind("127.0.0.1", 0)
            await transport2.bind("127.0.0.1", 0)
            
            port1 = transport1.get_local_port()
            port2 = transport2.get_local_port()
            
            # Send from transport1 to transport2
            test_data = b"Hello from peer 1"
            success = await transport1.send_to_peer(test_data, "127.0.0.1", port2)
            assert success, "Failed to send to peer"
            
            # Receive on transport2
            data, sender_host, sender_port = await transport2.receive_from_peer(1000)
            assert data == test_data, f"Data mismatch: {data} != {test_data}"
            assert sender_port == port1, "Sender port mismatch"
            
            # Send response back
            response_data = b"Hello from peer 2"
            await transport2.send_to_peer(response_data, "127.0.0.1", port1)
            
            # Receive response
            data, sender_host, sender_port = await transport1.receive_from_peer(1000)
            assert data == response_data, "Response data mismatch"
            
        finally:
            transport1.close()
            transport2.close()
    
    @pytest.mark.asyncio
    async def test_receive_timeout(self):
        """Test receive timeout behavior."""
        transport = UDPTransport()
        
        try:
            await transport.bind("127.0.0.1", 0)
            
            # Try to receive with short timeout (should timeout)
            data, host, port = await transport.receive_from_peer(100)
            
            # Should return empty on timeout
            assert data == b"", "Should return empty bytes on timeout"
            assert host == "", "Should return empty host on timeout"
            assert port == 0, "Should return 0 port on timeout"
            
        finally:
            transport.close()
    
    @pytest.mark.asyncio
    async def test_broadcast_enabled(self):
        """Test enabling broadcast."""
        transport = UDPTransport()
        
        try:
            await transport.bind("0.0.0.0", 0)
            
            # Enable broadcast
            success = await transport.enable_broadcast()
            assert success, "Failed to enable broadcast"
            
            # Try to send to broadcast address
            test_data = b"Broadcast message"
            success = await transport.send_to_peer(test_data, "255.255.255.255", 9999)
            # Note: This might not actually deliver, but shouldn't error
            assert success, "Failed to send broadcast"
            
        finally:
            transport.close()
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test proper resource cleanup."""
        transport = UDPTransport()
        
        # Bind and then close
        await transport.bind("127.0.0.1", 0)
        port = transport.get_local_port()
        assert port > 0
        
        transport.close()
        
        # After close, should not be bound
        assert not transport.is_bound()
        assert transport.get_local_port() == 0
    
    @pytest.mark.asyncio
    async def test_multiple_receives(self):
        """Test receiving multiple messages."""
        sender = UDPTransport()
        receiver = UDPTransport()
        
        try:
            await sender.bind("127.0.0.1", 0)
            await receiver.bind("127.0.0.1", 0)
            
            receiver_port = receiver.get_local_port()
            
            # Send multiple messages
            messages = [b"Message 1", b"Message 2", b"Message 3"]
            for msg in messages:
                await sender.send_to_peer(msg, "127.0.0.1", receiver_port)
            
            # Receive all messages
            received = []
            for _ in range(3):
                data, _, _ = await receiver.receive_from_peer(1000)
                if data:
                    received.append(data)
            
            assert len(received) == 3, f"Expected 3 messages, got {len(received)}"
            assert set(received) == set(messages), "Received messages don't match sent"
            
        finally:
            sender.close()
            receiver.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
