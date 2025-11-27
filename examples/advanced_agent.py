#!/usr/bin/env python3
"""
Advanced µACP Agent Example

Demonstrates all µACP features:
- Transport layer (UDP/TCP)
- Security framework (authentication, encryption)
- Protocol bridges (MQTT, CoAP, MCP)
- Monitoring and debugging tools
"""

import asyncio
import json
import time
import signal
import sys
from typing import Dict, Any

# Import µACP components
from uacp_lib import (
    UACPAgent, UACPTransport, TransportConfig, TransportType,
    UACPSecurity, SecurityConfig, SecurityLevel, AuthMethod,
    BridgeManager, BridgeConfig, BridgeType,
    UACPMonitoring, UACPMessage, UACPVerb, UACPOptionType
)


class AdvancedUACPAgent:
    """Advanced µACP agent with all features enabled."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.running = False
        
        # Initialize components
        self._init_transport()
        self._init_security()
        self._init_bridges()
        self._init_monitoring()
        self._init_agent()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _init_transport(self):
        """Initialize transport layer."""
        transport_config = TransportConfig(
            transport_type=TransportType.UDP,
            host=self.config.get('host', '0.0.0.0'),
            port=self.config.get('port', 8888),
            connection_timeout=30.0,
            max_connections=100
        )
        
        self.transport = UACPTransport(transport_config)
        
        # Add message handler
        self.transport.add_message_handler(self._handle_transport_message)
    
    def _init_security(self):
        """Initialize security framework."""
        security_config = SecurityConfig(
            security_level=SecurityLevel.BASIC,
            auth_method=AuthMethod.HMAC,
            secret_key=self.config.get('secret_key', 'default_secret')
        )
        
        self.security = UACPSecurity(security_config)
    
    def _init_bridges(self):
        """Initialize protocol bridges."""
        self.bridge_manager = BridgeManager(self.transport)
        
        # MQTT bridge
        if self.config.get('mqtt_enabled', False):
            mqtt_config = BridgeConfig(
                bridge_type=BridgeType.MQTT,
                host=self.config.get('mqtt_host', 'localhost'),
                port=self.config.get('mqtt_port', 1883),
                topics=['uacp/#', 'agent/#'],
                qos=1
            )
            mqtt_bridge = MQTTBridge(mqtt_config, self.transport)
            mqtt_bridge.add_message_handler(self._handle_bridge_message)
            self.bridge_manager.add_bridge(mqtt_bridge)
        
        # CoAP bridge
        if self.config.get('coap_enabled', False):
            coap_config = BridgeConfig(
                bridge_type=BridgeType.COAP,
                host=self.config.get('coap_host', 'localhost'),
                port=self.config.get('coap_port', 5683)
            )
            coap_bridge = CoAPBridge(coap_config, self.transport)
            coap_bridge.add_message_handler(self._handle_bridge_message)
            self.bridge_manager.add_bridge(coap_bridge)
    
    def _init_monitoring(self):
        """Initialize monitoring system."""
        self.monitoring = UACPMonitoring()
        
        # Add custom health checks
        self.monitoring.health.add_health_check('agent', self._check_agent_health)
        self.monitoring.health.add_health_check('transport', self._check_transport_health)
        
        # Add alert handler
        self.monitoring.alerts.add_alert_handler(self._handle_alert)
    
    def _init_agent(self):
        """Initialize µACP agent."""
        self.agent = UACPAgent(
            agent_id=self.agent_id,
            capabilities=['advanced_features', 'bridges', 'monitoring'],
            topics=['/agent/advanced', '/system/status', '/bridge/#']
        )
        
        # Add topic handlers
        self.agent.add_topic_handler('/agent/advanced', self._handle_advanced_topic)
        self.agent.add_topic_handler('/system/status', self._handle_status_topic)
        self.agent.add_topic_handler('/bridge/#', self._handle_bridge_topic)
    
    async def start(self):
        """Start the advanced agent."""
        if self.running:
            return
        
        print(f"🚀 Starting Advanced µACP Agent: {self.agent_id}")
        
        try:
            # Start transport
            await self.transport.start()
            print("✅ Transport layer started")
            
            # Start bridges
            await self.bridge_manager.start_all()
            print("✅ Protocol bridges started")
            
            # Start agent
            await self.agent.start()
            print("✅ µACP agent started")
            
            # Start monitoring
            print("✅ Monitoring system active")
            
            self.running = True
            
            # Start background tasks
            asyncio.create_task(self._status_reporter())
            asyncio.create_task(self._health_checker())
            asyncio.create_task(self._metrics_collector())
            
            print(f"🎯 Advanced µACP Agent {self.agent_id} is running!")
            print("   Press Ctrl+C to stop")
            
        except Exception as e:
            print(f"❌ Failed to start agent: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the advanced agent."""
        if not self.running:
            return
        
        print(f"\n🛑 Stopping Advanced µACP Agent: {self.agent_id}")
        
        self.running = False
        
        try:
            # Stop components
            await self.agent.stop()
            await self.bridge_manager.stop_all()
            await self.transport.stop()
            
            print("✅ Advanced µACP Agent stopped")
            
        except Exception as e:
            print(f"❌ Error stopping agent: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        print(f"\n📡 Received signal {signum}")
        asyncio.create_task(self.stop())
    
    async def _handle_transport_message(self, message: UACPMessage, host: str, port: int):
        """Handle messages from transport layer."""
        try:
            # Record metrics
            self.monitoring.record_message_metric(
                'transport',
                len(message.pack()),
                True
            )
            
            # Process message
            await self.agent.handle_message(message)
            
        except Exception as e:
            print(f"Transport message handling error: {e}")
            self.monitoring.record_message_metric('transport', 0, False)
    
    async def _handle_bridge_message(self, message: UACPMessage, source: str):
        """Handle messages from protocol bridges."""
        try:
            # Record metrics
            self.monitoring.record_message_metric(
                'bridge',
                len(message.pack()),
                True
            )
            
            # Process bridge message
            await self.agent.handle_message(message)
            
        except Exception as e:
            print(f"Bridge message handling error: {e}")
            self.monitoring.record_message_metric('bridge', 0, False)
    
    async def _handle_advanced_topic(self, message: UACPMessage) -> UACPMessage:
        """Handle advanced topic messages."""
        print(f"🔧 Advanced topic message: {message.header.verb.name}")
        
        # Create response
        response = UACPMessage(
            header=message.header,
            options=message.options,
            payload=json.dumps({
                'status': 'processed',
                'agent_id': self.agent_id,
                'timestamp': time.time(),
                'advanced_features': True
            }).encode()
        )
        
        return response
    
    async def _handle_status_topic(self, message: UACPMessage) -> UACPMessage:
        """Handle status topic messages."""
        print(f"📊 Status request received")
        
        # Get system status
        status_data = self.monitoring.get_dashboard_data()
        
        response = UACPMessage(
            header=message.header,
            options=message.options,
            payload=json.dumps(status_data).encode()
        )
        
        return response
    
    async def _handle_bridge_topic(self, message: UACPMessage) -> UACPMessage:
        """Handle bridge-related messages."""
        print(f"🌉 Bridge message: {message.header.verb.name}")
        
        # Get bridge status
        bridge_stats = self.bridge_manager.get_bridge_stats()
        
        response = UACPMessage(
            header=message.header,
            options=message.options,
            payload=json.dumps(bridge_stats).encode()
        )
        
        return response
    
    async def _status_reporter(self):
        """Report agent status periodically."""
        while self.running:
            try:
                # Get status
                status = {
                    'agent_id': self.agent_id,
                    'running': self.running,
                    'uptime': time.time() - self.monitoring.start_time,
                    'connections': len(self.transport.get_connection_info()),
                    'bridges': len(self.bridge_manager.bridges)
                }
                
                print(f"📈 Status: {json.dumps(status, indent=2)}")
                
                await asyncio.sleep(30)  # Report every 30 seconds
                
            except Exception as e:
                print(f"Status reporter error: {e}")
                await asyncio.sleep(10)
    
    async def _health_checker(self):
        """Check system health periodically."""
        while self.running:
            try:
                # Check health
                health_status = self.monitoring.health.get_health_status()
                
                for component, status in health_status.items():
                    if status.status != 'healthy':
                        print(f"⚠️  Health warning: {component} is {status.status}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Health checker error: {e}")
                await asyncio.sleep(30)
    
    async def _metrics_collector(self):
        """Collect and report metrics periodically."""
        while self.running:
            try:
                # Export metrics
                metrics_json = self.monitoring.export_metrics('json')
                
                # Save to file
                with open(f'uacp_agent_{self.agent_id}_metrics.json', 'w') as f:
                    f.write(metrics_json)
                
                await asyncio.sleep(300)  # Export every 5 minutes
                
            except Exception as e:
                print(f"Metrics collector error: {e}")
                await asyncio.sleep(60)
    
    def _check_agent_health(self) -> Dict[str, Any]:
        """Check agent health."""
        return {
            'status': 'healthy' if self.running else 'unhealthy',
            'details': {
                'running': self.running,
                'agent_id': self.agent_id,
                'connections': len(self.transport.get_connection_info())
            }
        }
    
    def _check_transport_health(self) -> Dict[str, Any]:
        """Check transport health."""
        transport_stats = self.transport.get_stats()
        
        # Check for errors
        error_rate = 0
        if transport_stats['messages_sent'] > 0:
            error_rate = transport_stats['network_errors'] / transport_stats['messages_sent']
        
        status = 'healthy'
        if error_rate > 0.1:  # 10% error rate
            status = 'degraded'
        if error_rate > 0.5:  # 50% error rate
            status = 'unhealthy'
        
        return {
            'status': status,
            'details': {
                'error_rate': error_rate,
                'messages_sent': transport_stats['messages_sent'],
                'messages_received': transport_stats['messages_received'],
                'connections_active': transport_stats['connections_active']
            }
        }
    
    def _handle_alert(self, alert):
        """Handle monitoring alerts."""
        print(f"🚨 ALERT [{alert.level.value.upper()}] {alert.source}: {alert.message}")
        if alert.details:
            print(f"   Details: {alert.details}")
    
    async def send_message(self, topic: str, verb: UACPVerb, payload: Dict[str, Any] = None):
        """Send a message."""
        try:
            message = UACPMessage(
                header=self.agent.create_header(verb),
                options=[
                    self.agent.create_option(UACPOptionType.TOPIC_PATH, topic.encode())
                ],
                payload=json.dumps(payload or {}).encode()
            )
            
            # Send via transport
            success = await self.transport.send_message(
                '127.0.0.1',  # Local for demo
                self.config.get('port', 8888),
                message
            )
            
            if success:
                print(f"✅ Message sent to {topic}")
            else:
                print(f"❌ Failed to send message to {topic}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False


async def main():
    """Main function."""
    # Configuration
    config = {
        'host': '0.0.0.0',
        'port': 8888,
        'mqtt_enabled': True,
        'mqtt_host': 'localhost',
        'mqtt_port': 1883,
        'coap_enabled': True,
        'coap_host': 'localhost',
        'coap_port': 5683,
        'secret_key': 'advanced_agent_secret'
    }
    
    # Create agent
    agent = AdvancedUACPAgent('advanced_demo', config)
    
    try:
        # Start agent
        await agent.start()
        
        # Demo: Send some messages
        await asyncio.sleep(2)
        
        print("\n🎭 Running demo operations...")
        
        # Send PING
        await agent.send_message('/agent/advanced', UACPVerb.PING, {'demo': True})
        await asyncio.sleep(1)
        
        # Send TELL
        await agent.send_message('/system/status', UACPVerb.TELL, {'status': 'running'})
        await asyncio.sleep(1)
        
        # Send ASK
        await agent.send_message('/agent/advanced', UACPVerb.ASK, {'query': 'capabilities'})
        await asyncio.sleep(1)
        
        # Keep running
        print("\n🔄 Agent is running. Press Ctrl+C to stop.")
        while agent.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await agent.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
