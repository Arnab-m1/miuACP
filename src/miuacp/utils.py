"""
µACP Utilities

Provides utility functions and tools for:
- Message validation and debugging
- Protocol analysis
- Performance measurement
- Common operations
"""

import time
import struct
import hashlib
import json
import cbor2
from typing import Dict, List, Optional, Union, Any, Tuple
from .protocol import (
    UACPProtocol, UACPMessage, UACPHeader, UACPOption, 
    UACPOptionType, UACPVerb, UACPContentType
)


class UACPUtils:
    """Utility functions for µACP protocol."""
    
    @staticmethod
    def validate_message_structure(message: UACPMessage) -> Tuple[bool, List[str]]:
        """Validate message structure and return (is_valid, errors)."""
        errors = []
        
        # Check header
        if message.header.version != 1:
            errors.append(f"Invalid version: {message.header.version}")
        
        if message.header.verb not in UACPVerb:
            errors.append(f"Invalid verb: {message.header.verb}")
        
        if message.header.qos not in [0, 1, 2]:
            errors.append(f"Invalid QoS: {message.header.qos}")
        
        if message.header.msg_id < 0 or message.header.msg_id > 0xFFFFFF:
            errors.append(f"Invalid message ID: {message.header.msg_id}")
        
        if message.header.opts_count != len(message.options):
            errors.append(f"Options count mismatch: header={message.header.opts_count}, actual={len(message.options)}")
        
        # Check options
        for i, option in enumerate(message.options):
            if option.type not in UACPOptionType:
                errors.append(f"Invalid option type at index {i}: {option.type}")
            
            # Validate option values based on type
            if option.type == UACPOptionType.CONTENT_TYPE:
                if not isinstance(option.value, int) or option.value not in UACPContentType:
                    errors.append(f"Invalid content type value: {option.value}")
            
            elif option.type == UACPOptionType.PRIORITY:
                if not isinstance(option.value, int) or option.value < 0 or option.value > 7:
                    errors.append(f"Invalid priority value: {option.value}")
        
        # Check message size
        try:
            message_size = len(message.pack())
            if message_size > UACPProtocol.MAX_MESSAGE_SIZE:
                errors.append(f"Message too large: {message_size} bytes (max: {UACPProtocol.MAX_MESSAGE_SIZE})")
        except Exception as e:
            errors.append(f"Failed to pack message: {e}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def analyze_message_efficiency(message: UACPMessage) -> Dict[str, Any]:
        """Analyze message efficiency metrics."""
        try:
            packed = message.pack()
            header_size = 8  # Fixed header size
            options_size = sum(2 + len(opt.value) if isinstance(opt.value, bytes) else 2 + len(str(opt.value).encode()) 
                             for opt in message.options)
            payload_size = len(message.payload) if message.payload else 0
            
            total_size = len(packed)
            
            return {
                "total_size": total_size,
                "header_size": header_size,
                "options_size": options_size,
                "payload_size": payload_size,
                "header_efficiency": header_size / total_size if total_size > 0 else 0,
                "overhead_ratio": (header_size + options_size) / total_size if total_size > 0 else 0,
                "compression_ratio": payload_size / total_size if total_size > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def create_message_hash(message: UACPMessage) -> str:
        """Create a hash of the message for integrity checking."""
        try:
            packed = message.pack()
            return hashlib.sha256(packed).hexdigest()[:16]
        except Exception:
            return "hash_error"
    
    @staticmethod
    def format_message_debug(message: UACPMessage) -> str:
        """Format message for debugging output."""
        try:
            debug_info = []
            debug_info.append(f"µACP Message Debug:")
            debug_info.append(f"  Header:")
            debug_info.append(f"    Version: {message.header.version}")
            debug_info.append(f"    Verb: {message.header.verb.name} ({message.header.verb.value})")
            debug_info.append(f"    QoS: {message.header.qos}")
            debug_info.append(f"    Code: {message.header.code}")
            debug_info.append(f"    Message ID: {message.header.msg_id}")
            debug_info.append(f"    Options Count: {message.header.opts_count}")
            
            if message.options:
                debug_info.append(f"  Options:")
                for i, option in enumerate(message.options):
                    debug_info.append(f"    {i}: {option.type.name} = {option.value}")
            
            if message.payload:
                debug_info.append(f"  Payload: {len(message.payload)} bytes")
                try:
                    # Try to decode as text
                    text = message.payload.decode('utf-8')
                    debug_info.append(f"    Text: {text[:100]}{'...' if len(text) > 100 else ''}")
                except UnicodeDecodeError:
                    debug_info.append(f"    Binary data")
            else:
                debug_info.append(f"  Payload: None")
            
            return "\n".join(debug_info)
        except Exception as e:
            return f"Debug formatting error: {e}"
    
    @staticmethod
    def estimate_message_size(verb: UACPVerb, 
                            options: Optional[List[UACPOption]] = None,
                            payload_size: int = 0) -> int:
        """Estimate the size of a message before creation."""
        base_size = 8  # Fixed header
        
        if options:
            for option in options:
                if isinstance(option.value, str):
                    base_size += 2 + len(option.value.encode('utf-8'))
                elif isinstance(option.value, int):
                    base_size += 2 + 4  # Assume 4-byte int
                else:
                    base_size += 2 + len(option.value)
        
        return base_size + payload_size
    
    @staticmethod
    def create_test_message(verb: UACPVerb = UACPVerb.PING,
                          msg_id: int = 1,
                          qos: int = 0,
                          options: Optional[List[UACPOption]] = None,
                          payload: Optional[Union[bytes, str, dict]] = None) -> UACPMessage:
        """Create a test message for testing purposes."""
        return UACPProtocol.create_message(
            verb=verb,
            msg_id=msg_id,
            qos=qos,
            options=options,
            payload=payload
        )
    
    @staticmethod
    def benchmark_message_operations(message: UACPMessage, iterations: int = 1000) -> Dict[str, float]:
        """Benchmark message packing/unpacking operations."""
        results = {}
        
        # Benchmark packing
        start_time = time.time()
        for _ in range(iterations):
            packed = message.pack()
        pack_time = time.time() - start_time
        results['pack_time_per_msg'] = pack_time / iterations * 1000  # ms
        
        # Benchmark unpacking
        packed = message.pack()
        start_time = time.time()
        for _ in range(iterations):
            unpacked = UACPMessage.unpack(packed)
        unpack_time = time.time() - start_time
        results['unpack_time_per_msg'] = unpack_time / iterations * 1000  # ms
        
        # Calculate throughput
        results['pack_throughput'] = iterations / pack_time
        results['unpack_throughput'] = iterations / unpack_time
        
        return results
    
    @staticmethod
    def compare_messages(msg1: UACPMessage, msg2: UACPMessage) -> Dict[str, Any]:
        """Compare two messages and return differences."""
        differences = {}
        
        # Compare headers
        if msg1.header.version != msg2.header.version:
            differences['version'] = (msg1.header.version, msg2.header.version)
        
        if msg1.header.verb != msg2.header.verb:
            differences['verb'] = (msg1.header.verb, msg2.header.verb)
        
        if msg1.header.qos != msg2.header.qos:
            differences['qos'] = (msg1.header.qos, msg2.header.qos)
        
        if msg1.header.code != msg2.header.code:
            differences['code'] = (msg1.header.code, msg2.header.code)
        
        if msg1.header.msg_id != msg2.header.msg_id:
            differences['msg_id'] = (msg1.header.msg_id, msg2.header.msg_id)
        
        # Compare options
        if len(msg1.options) != len(msg2.options):
            differences['options_count'] = (len(msg1.options), len(msg2.options))
        else:
            option_diffs = []
            for i, (opt1, opt2) in enumerate(zip(msg1.options, msg2.options)):
                if opt1.type != opt2.type or opt1.value != opt2.value:
                    option_diffs.append({
                        'index': i,
                        'type': (opt1.type, opt2.type),
                        'value': (opt1.value, opt2.value)
                    })
            if option_diffs:
                differences['options'] = option_diffs
        
        # Compare payloads
        if msg1.payload != msg2.payload:
            differences['payload'] = (len(msg1.payload) if msg1.payload else 0,
                                   len(msg2.payload) if msg2.payload else 0)
        
        return differences
    
    @staticmethod
    def create_message_template(verb: UACPVerb, 
                              template_name: str = "custom") -> Dict[str, Any]:
        """Create a message template for documentation or testing."""
        return {
            "template_name": template_name,
            "verb": verb.name,
            "verb_value": verb.value,
            "header": {
                "version": 1,
                "qos": 0,
                "code": 0,
                "msg_id": "auto_generated",
                "opts_count": "auto_calculated"
            },
            "options": [],
            "payload": None,
            "description": f"Template for {verb.name} messages",
            "usage_example": f"UACPProtocol.create_{verb.name.lower()}(msg_id, ...)"
        }
    
    @staticmethod
    def validate_topic_pattern(topic: str) -> Tuple[bool, List[str]]:
        """Validate topic pattern format."""
        errors = []
        
        if not topic:
            errors.append("Topic cannot be empty")
            return False, errors
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\']
        for char in invalid_chars:
            if char in topic:
                errors.append(f"Invalid character in topic: '{char}'")
        
        # Check for consecutive slashes
        if '//' in topic:
            errors.append("Topic cannot contain consecutive slashes")
        
        # Check for leading/trailing slashes
        if topic.startswith('/') or topic.endswith('/'):
            errors.append("Topic should not start or end with slash")
        
        # Check length
        if len(topic) > 255:
            errors.append("Topic too long (max 255 characters)")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def topic_matches_pattern(topic: str, pattern: str) -> bool:
        """Check if a topic matches a pattern (supports wildcards)."""
        # Simple wildcard matching: * matches any sequence, ? matches single character
        import re
        
        # Convert pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex_pattern = f"^{regex_pattern}$"
        
        try:
            return bool(re.match(regex_pattern, topic))
        except re.error:
            return False
    
    @staticmethod
    def generate_message_id() -> int:
        """Generate a unique message ID."""
        return int(time.time() * 1000) % 0xFFFFFF  # 24-bit timestamp-based ID
    
    @staticmethod
    def create_conversation_id() -> str:
        """Create a unique conversation ID."""
        import uuid
        return f"conv:{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def format_bytes(size_bytes: int) -> str:
        """Format bytes into human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration into human-readable format."""
        if seconds < 1:
            return f"{seconds * 1000:.1f} ms"
        elif seconds < 60:
            return f"{seconds:.2f} s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


# Convenience functions
def validate_message(message: UACPMessage) -> bool:
    """Quick validation of a message."""
    is_valid, _ = UACPUtils.validate_message_structure(message)
    return is_valid


def debug_message(message: UACPMessage) -> str:
    """Quick debug output for a message."""
    return UACPUtils.format_message_debug(message)


def estimate_size(verb: UACPVerb, options: Optional[List[UACPOption]] = None, payload_size: int = 0) -> int:
    """Quick size estimation for a message."""
    return UACPUtils.estimate_message_size(verb, options, payload_size)
