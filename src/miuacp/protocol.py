"""
µACP Protocol Core Implementation

Implements the µACP protocol specification including:
- Fixed 8-byte header structure
- TLV options system
- Message creation and parsing
- Protocol constants and enums
"""

import struct
import cbor2
from enum import IntEnum
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass


class UACPVerb(IntEnum):
    """µACP protocol verbs (speech acts)."""
    PING = 0      # Liveness check / clock hint
    TELL = 1      # Inform (pub/sub)
    ASK = 2       # Request/response (RPC)
    OBSERVE = 3   # Subscription to future informs


class UACPOptionType(IntEnum):
    """µACP TLV option types."""
    CONVERSATION_ID = 0x01    # 8-16B: multi-turn task correlation
    CORRELATION_ID = 0x02     # 3B: pair ASK with reply
    TOPIC_PATH = 0x03         # UTF-8 string (e.g., "lab/arm/plan")
    CONTENT_TYPE = 0x04       # small int: CBOR=0, JSON=1, Protobuf=2, Text=3
    ETAG = 0x05               # cache validator
    MAX_AGE = 0x06            # seconds (uint)
    BLOCK = 0x07              # blockwise transfer descriptor
    AUTH = 0x08               # short token id (pairs with COSE/DTLS)
    PRIORITY = 0x09           # 0-7 scheduling hint


class UACPContentType(IntEnum):
    """µACP content types."""
    CBOR = 0      # CBOR (default)
    JSON = 1      # JSON
    PROTOBUF = 2  # Protocol Buffers
    TEXT = 3      # Plain text


@dataclass
class UACPHeader:
    """µACP fixed 8-byte header."""
    version: int = 1          # 2 bits: protocol version
    verb: UACPVerb = UACPVerb.PING  # 2 bits: verb type
    qos: int = 0              # 2 bits: QoS level
    code: int = 0             # 8 bits: response code
    msg_id: int = 0           # 24 bits: message ID
    opts_count: int = 0       # 8 bits: number of TLV options
    
    def pack(self) -> bytes:
        """Pack header into 8 bytes."""
        # Pack into 64 bits: VVTTQQCC MMMMMMMM MMMMMMMM MMMMMMMM OOOOOOOO
        header = (
            (self.version & 0x3) << 62 |
            (self.verb & 0x3) << 60 |
            (self.qos & 0x3) << 58 |
            (self.code & 0xFF) << 50 |
            (self.msg_id & 0xFFFFFF) << 26 |
            (self.opts_count & 0xFF) << 18
        )
        return struct.pack('>Q', header)
    
    @classmethod
    def unpack(cls, data: bytes) -> 'UACPHeader':
        """Unpack header from 8 bytes."""
        if len(data) < 8:
            raise ValueError("Header must be exactly 8 bytes")
        
        header_int = struct.unpack('>Q', data[:8])[0]
        
        return cls(
            version=(header_int >> 62) & 0x3,
            verb=UACPVerb((header_int >> 60) & 0x3),
            qos=(header_int >> 58) & 0x3,
            code=(header_int >> 50) & 0xFF,
            msg_id=(header_int >> 26) & 0xFFFFFF,
            opts_count=(header_int >> 18) & 0xFF
        )


@dataclass
class UACPOption:
    """µACP TLV option."""
    type: UACPOptionType
    value: Union[bytes, str, int]
    
    def pack(self) -> bytes:
        """Pack option into TLV format."""
        if isinstance(self.value, str):
            value_bytes = self.value.encode('utf-8')
        elif isinstance(self.value, int):
            value_bytes = struct.pack('>I', self.value)
        else:
            value_bytes = self.value
        
        length = len(value_bytes)
        
        # TLV: Type(1) + Length(1) + Value(length)
        return struct.pack('BB', self.type, length) + value_bytes
    
    @classmethod
    def unpack(cls, data: bytes) -> Tuple['UACPOption', int]:
        """Unpack option from TLV format. Returns (option, bytes_consumed)."""
        if len(data) < 2:
            raise ValueError("Option data too short")
        
        opt_type = UACPOptionType(data[0])
        length = data[1]
        
        if len(data) < 2 + length:
            raise ValueError("Option value truncated")
        
        value_bytes = data[2:2+length]
        
        # Convert value based on type
        if opt_type == UACPOptionType.CONTENT_TYPE:
            value = struct.unpack('>I', value_bytes.ljust(4, b'\x00'))[0]
        elif opt_type in [UACPOptionType.CONVERSATION_ID, UACPOptionType.TOPIC_PATH]:
            value = value_bytes.decode('utf-8')
        else:
            value = value_bytes
        
        return cls(opt_type, value), 2 + length


@dataclass
class UACPMessage:
    """Complete µACP message."""
    header: UACPHeader
    options: List[UACPOption]
    payload: Optional[bytes] = None
    
    def pack(self) -> bytes:
        """Pack complete message."""
        # Update options count in header
        self.header.opts_count = len(self.options)
        
        # Pack header
        message = self.header.pack()
        
        # Pack options
        for option in self.options:
            message += option.pack()
        
        # Pack payload if present
        if self.payload:
            message += self.payload
        
        return message
    
    @classmethod
    def unpack(cls, data: bytes) -> 'UACPMessage':
        """Unpack complete message."""
        if len(data) < 8:
            raise ValueError("Message too short")
        
        # Unpack header
        header = UACPHeader.unpack(data[:8])
        offset = 8
        
        # Unpack options
        options = []
        for _ in range(header.opts_count):
            if offset >= len(data):
                break
            option, consumed = UACPOption.unpack(data[offset:])
            options.append(option)
            offset += consumed
        
        # Remaining data is payload
        payload = data[offset:] if offset < len(data) else None
        
        return cls(header, options, payload)


class UACPProtocol:
    """µACP protocol implementation."""
    
    # Protocol constants
    MAX_MESSAGE_SIZE = 65535
    MAX_OPTIONS = 255
    DEFAULT_TIMEOUT = 30.0  # seconds
    
    @staticmethod
    def create_message(verb: UACPVerb, 
                      msg_id: int,
                      qos: int = 0,
                      code: int = 0,
                      options: Optional[List[UACPOption]] = None,
                      payload: Optional[Union[bytes, str, dict]] = None) -> UACPMessage:
        """Create a new µACP message."""
        if options is None:
            options = []
        
        # Convert payload to bytes
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        elif isinstance(payload, dict):
            payload_bytes = cbor2.dumps(payload)
        elif payload is None:
            payload_bytes = None
        else:
            payload_bytes = payload
        
        header = UACPHeader(
            version=1,
            verb=verb,
            qos=qos,
            code=code,
            msg_id=msg_id,
            opts_count=len(options)
        )
        
        return UACPMessage(header, options, payload_bytes)
    
    @staticmethod
    def create_ping(msg_id: int, qos: int = 0) -> UACPMessage:
        """Create a PING message."""
        return UACPProtocol.create_message(UACPVerb.PING, msg_id, qos)
    
    @staticmethod
    def create_tell(msg_id: int, topic: str, data: Union[bytes, str, dict], 
                   qos: int = 0, conv_id: Optional[str] = None) -> UACPMessage:
        """Create a TELL message."""
        options = [UACPOption(UACPOptionType.TOPIC_PATH, topic)]
        if conv_id:
            options.append(UACPOption(UACPOptionType.CONVERSATION_ID, conv_id))
        
        return UACPProtocol.create_message(UACPVerb.TELL, msg_id, qos, payload=data, options=options)
    
    @staticmethod
    def create_ask(msg_id: int, topic: str, data: Union[bytes, str, dict],
                  qos: int = 1, conv_id: Optional[str] = None) -> UACPMessage:
        """Create an ASK message."""
        options = [UACPOption(UACPOptionType.TOPIC_PATH, topic)]
        if conv_id:
            options.append(UACPOption(UACPOptionType.CONVERSATION_ID, conv_id))
        
        return UACPProtocol.create_message(UACPVerb.ASK, msg_id, qos, payload=data, options=options)
    
    @staticmethod
    def create_observe(msg_id: int, topic: str, qos: int = 1) -> UACPMessage:
        """Create an OBSERVE message."""
        options = [UACPOption(UACPOptionType.TOPIC_PATH, topic)]
        return UACPProtocol.create_message(UACPVerb.OBSERVE, msg_id, qos, options=options)
    
    @staticmethod
    def create_response(original_msg: UACPMessage, code: int, 
                       payload: Optional[Union[bytes, str, dict]] = None) -> UACPMessage:
        """Create a response message."""
        # Copy options but add correlation ID
        options = original_msg.options.copy()
        options.append(UACPOption(UACPOptionType.CORRELATION_ID, original_msg.header.msg_id))
        
        return UACPProtocol.create_message(
            verb=original_msg.header.verb,
            msg_id=original_msg.header.msg_id + 1000000,  # Avoid collision
            qos=original_msg.header.qos,
            code=code,
            options=options,
            payload=payload
        )
    
    @staticmethod
    def validate_message(message: UACPMessage) -> bool:
        """Validate message structure and constraints."""
        # Check header constraints
        if message.header.version != 1:
            return False
        
        if message.header.verb not in UACPVerb:
            return False
        
        if message.header.qos not in [0, 1, 2]:
            return False
        
        if message.header.opts_count > UACPProtocol.MAX_OPTIONS:
            return False
        
        # Check message size
        message_size = len(message.pack())
        if message_size > UACPProtocol.MAX_MESSAGE_SIZE:
            return False
        
        return True
    
    @staticmethod
    def get_option(message: UACPMessage, opt_type: UACPOptionType) -> Optional[UACPOption]:
        """Get option by type from message."""
        for option in message.options:
            if option.type == opt_type:
                return option
        return None
    
    @staticmethod
    def get_topic(message: UACPMessage) -> Optional[str]:
        """Get topic from message options."""
        option = UACPProtocol.get_option(message, UACPOptionType.TOPIC_PATH)
        return option.value if option else None
    
    @staticmethod
    def get_conversation_id(message: UACPMessage) -> Optional[str]:
        """Get conversation ID from message options."""
        option = UACPProtocol.get_option(message, UACPOptionType.CONVERSATION_ID)
        return option.value if option else None
