"""
µACP Reliability & QoS State Management

This module handles all reliability and QoS state including:
- Duplicate suppression cache (Msg-ID window)
- Pending ACK timers and retransmission counters
- Out-of-order reassembly buffers (if blockwise)
- Sliding windows (for congestion and block transfers)
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import heapq


class QoSLevel(Enum):
    """QoS levels for reliability."""
    AT_MOST_ONCE = 0      # No guarantees
    AT_LEAST_ONCE = 1     # Retry with ACK
    EXACTLY_ONCE = 2      # Two-phase commit


class MessageState(Enum):
    """Message states for reliability tracking."""
    SENT = "sent"
    ACKED = "acked"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"


class ReassemblyState(Enum):
    """Reassembly states for blockwise transfers."""
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class MessageTracker:
    """Track message for reliability guarantees."""
    message_id: str
    qos: QoSLevel
    state: MessageState
    created: float
    sent_time: float
    ack_time: Optional[float] = None
    delivery_time: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    last_retry: float = 0.0
    timeout: float = 30.0
    payload_size: int = 0
    destination: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ACKTimer:
    """ACK timer for QoS1/QoS2 messages."""
    message_id: str
    created: float
    expires: float
    callback: Optional[Callable] = None
    retry_callback: Optional[Callable] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReassemblyBuffer:
    """Buffer for reassembling blockwise transfers."""
    transfer_id: str
    total_blocks: int
    received_blocks: Set[int]
    block_data: Dict[int, bytes]
    created: float
    expires: float
    state: ReassemblyState
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SlidingWindow:
    """Sliding window for flow control."""
    window_id: str
    size: int
    base: int
    next_seq: int
    unacked: Set[int]
    received: Set[int]
    created: float
    last_activity: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class UACPReliability:
    """µACP reliability and QoS state management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Message tracking
        self.message_trackers: Dict[str, MessageTracker] = {}
        self.duplicate_cache: Dict[str, float] = {}  # message_id -> timestamp
        
        # ACK timers
        self.ack_timers: Dict[str, ACKTimer] = {}
        self.timer_queue: List[Tuple[float, str]] = []  # (expires, message_id)
        
        # Reassembly buffers
        self.reassembly_buffers: Dict[str, ReassemblyBuffer] = {}
        self.transfer_blocks: Dict[str, Dict[int, bytes]] = defaultdict(dict)
        
        # Sliding windows
        self.sliding_windows: Dict[str, SlidingWindow] = {}
        self.connection_windows: Dict[str, str] = {}  # connection_id -> window_id
        
        # Configuration
        self.max_message_trackers = self.config.get('max_message_trackers', 10000)
        self.max_reassembly_buffers = self.config.get('max_reassembly_buffers', 1000)
        self.max_sliding_windows = self.config.get('max_sliding_windows', 1000)
        
        self.duplicate_window = self.config.get('duplicate_window', 300.0)  # 5 minutes
        self.ack_timeout = self.config.get('ack_timeout', 30.0)
        self.reassembly_timeout = self.config.get('reassembly_timeout', 300.0)
        self.window_timeout = self.config.get('window_timeout', 600.0)
        
        # State tracking
        self.last_cleanup = time.time()
        self.cleanup_interval = 30.0
        self.stats = {
            'messages_tracked': 0,
            'messages_acked': 0,
            'messages_delivered': 0,
            'messages_failed': 0,
            'duplicates_dropped': 0,
            'retransmissions': 0,
            'reassemblies_completed': 0,
            'window_advances': 0
        }
        
        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._timer_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the reliability manager."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._timer_task = asyncio.create_task(self._timer_loop())
    
    async def stop(self):
        """Stop the reliability manager."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._timer_task:
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass
    
    # === Message Tracking ===
    
    def track_message(self, message_id: str, qos: QoSLevel, destination: str,
                     payload_size: int = 0, timeout: float = 30.0,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Start tracking a message for reliability."""
        if len(self.message_trackers) >= self.max_message_trackers:
            # Remove oldest tracker
            oldest = min(self.message_trackers.values(), key=lambda t: t.created)
            del self.message_trackers[oldest.message_id]
        
        now = time.time()
        
        tracker = MessageTracker(
            message_id=message_id,
            qos=qos,
            state=MessageState.SENT,
            created=now,
            sent_time=now,
            timeout=timeout,
            payload_size=payload_size,
            destination=destination,
            metadata=metadata or {}
        )
        
        self.message_trackers[message_id] = tracker
        self.stats['messages_tracked'] += 1
        
        # Add to ACK timer if QoS > 0
        if qos != QoSLevel.AT_MOST_ONCE:
            self._add_ack_timer(message_id, timeout)
        
        return True
    
    def update_message_state(self, message_id: str, new_state: MessageState,
                            **kwargs) -> bool:
        """Update message state."""
        if message_id in self.message_trackers:
            tracker = self.message_trackers[message_id]
            tracker.state = new_state
            
            if new_state == MessageState.ACKED:
                tracker.ack_time = time.time()
                self.stats['messages_acked'] += 1
                self._remove_ack_timer(message_id)
            
            elif new_state == MessageState.DELIVERED:
                tracker.delivery_time = time.time()
                self.stats['messages_delivered'] += 1
            
            elif new_state == MessageState.FAILED:
                self.stats['messages_failed'] += 1
            
            # Update other fields
            for key, value in kwargs.items():
                if hasattr(tracker, key):
                    setattr(tracker, key, value)
            
            return True
        
        return False
    
    def get_message_tracker(self, message_id: str) -> Optional[MessageTracker]:
        """Get message tracker by ID."""
        return self.message_trackers.get(message_id)
    
    def retry_message(self, message_id: str) -> bool:
        """Retry a message."""
        if message_id in self.message_trackers:
            tracker = self.message_trackers[message_id]
            if tracker.retry_count < tracker.max_retries:
                tracker.retry_count += 1
                tracker.last_retry = time.time()
                tracker.state = MessageState.SENT
                self.stats['retransmissions'] += 1
                return True
        
        return False
    
    # === Duplicate Suppression ===
    
    def is_duplicate(self, message_id: str) -> bool:
        """Check if message is a duplicate."""
        now = time.time()
        
        if message_id in self.duplicate_cache:
            if now - self.duplicate_cache[message_id] < self.duplicate_window:
                self.stats['duplicates_dropped'] += 1
                return True
            else:
                # Expired duplicate entry
                del self.duplicate_cache[message_id]
        
        # Add to duplicate cache
        self.duplicate_cache[message_id] = now
        return False
    
    def mark_message_received(self, message_id: str) -> None:
        """Mark message as received for duplicate suppression."""
        self.duplicate_cache[message_id] = time.time()
    
    # === ACK Timer Management ===
    
    def _add_ack_timer(self, message_id: str, timeout: float,
                       callback: Optional[Callable] = None,
                       retry_callback: Optional[Callable] = None,
                       context: Optional[Dict[str, Any]] = None) -> None:
        """Add ACK timer for a message."""
        now = time.time()
        expires = now + timeout
        
        timer = ACKTimer(
            message_id=message_id,
            created=now,
            expires=expires,
            callback=callback,
            retry_callback=retry_callback,
            context=context or {}
        )
        
        self.ack_timers[message_id] = timer
        heapq.heappush(self.timer_queue, (expires, message_id))
    
    def _remove_ack_timer(self, message_id: str) -> bool:
        """Remove ACK timer for a message."""
        if message_id in self.ack_timers:
            del self.ack_timers[message_id]
            # Note: timer_queue cleanup happens in timer loop
            return True
        return False
    
    def _check_expired_timers(self) -> List[str]:
        """Check for expired timers."""
        now = time.time()
        expired = []
        
        while self.timer_queue and self.timer_queue[0][0] <= now:
            expires, message_id = heapq.heappop(self.timer_queue)
            
            if message_id in self.ack_timers:
                timer = self.ack_timers[message_id]
                if timer.expires <= now:
                    expired.append(message_id)
                    del self.ack_timers[message_id]
        
        return expired
    
    # === Reassembly Buffer Management ===
    
    def create_reassembly_buffer(self, transfer_id: str, total_blocks: int,
                                timeout: float = 300.0) -> bool:
        """Create a reassembly buffer for blockwise transfer."""
        if len(self.reassembly_buffers) >= self.max_reassembly_buffers:
            # Remove oldest buffer
            oldest = min(self.reassembly_buffers.values(), key=lambda b: b.created)
            del self.reassembly_buffers[oldest.transfer_id]
        
        now = time.time()
        
        buffer = ReassemblyBuffer(
            transfer_id=transfer_id,
            total_blocks=total_blocks,
            received_blocks=set(),
            block_data={},
            created=now,
            expires=now + timeout,
            state=ReassemblyState.INCOMPLETE
        )
        
        self.reassembly_buffers[transfer_id] = buffer
        return True
    
    def add_block(self, transfer_id: str, block_number: int, block_data: bytes) -> bool:
        """Add a block to reassembly buffer."""
        if transfer_id in self.reassembly_buffers:
            buffer = self.reassembly_buffers[transfer_id]
            
            if block_number not in buffer.received_blocks:
                buffer.received_blocks.add(block_number)
                buffer.block_data[block_number] = block_data
                buffer.last_activity = time.time()
                
                # Check if complete
                if len(buffer.received_blocks) == buffer.total_blocks:
                    buffer.state = ReassemblyState.COMPLETE
                    self.stats['reassemblies_completed'] += 1
                
                return True
        
        return False
    
    def get_reassembly_buffer(self, transfer_id: str) -> Optional[ReassemblyBuffer]:
        """Get reassembly buffer by transfer ID."""
        return self.reassembly_buffers.get(transfer_id)
    
    def is_transfer_complete(self, transfer_id: str) -> bool:
        """Check if transfer is complete."""
        buffer = self.reassembly_buffers.get(transfer_id)
        return buffer is not None and buffer.state == ReassemblyState.COMPLETE
    
    def get_complete_data(self, transfer_id: str) -> Optional[bytes]:
        """Get complete reassembled data."""
        buffer = self.reassembly_buffers.get(transfer_id)
        if buffer and buffer.state == ReassemblyState.COMPLETE:
            # Sort blocks and concatenate
            sorted_blocks = [buffer.block_data[i] for i in sorted(buffer.received_blocks)]
            return b''.join(sorted_blocks)
        return None
    
    # === Sliding Window Management ===
    
    def create_sliding_window(self, window_id: str, size: int,
                             initial_seq: int = 0) -> bool:
        """Create a sliding window for flow control."""
        if len(self.sliding_windows) >= self.max_sliding_windows:
            # Remove oldest window
            oldest = min(self.sliding_windows.values(), key=lambda w: w.created)
            del self.sliding_windows[oldest.window_id]
        
        now = time.time()
        
        window = SlidingWindow(
            window_id=window_id,
            size=size,
            base=initial_seq,
            next_seq=initial_seq,
            unacked=set(),
            received=set(),
            created=now,
            last_activity=now
        )
        
        self.sliding_windows[window_id] = window
        return True
    
    def send_packet(self, window_id: str, seq_num: int) -> bool:
        """Send a packet through sliding window."""
        if window_id in self.sliding_windows:
            window = self.sliding_windows[window_id]
            
            if seq_num >= window.base and seq_num < window.base + window.size:
                window.unacked.add(seq_num)
                window.next_seq = max(window.next_seq, seq_num + 1)
                window.last_activity = time.time()
                return True
        
        return False
    
    def receive_ack(self, window_id: str, seq_num: int) -> bool:
        """Receive ACK for packet."""
        if window_id in self.sliding_windows:
            window = self.sliding_windows[window_id]
            
            if seq_num in window.unacked:
                window.unacked.remove(seq_num)
                
                # Advance window if possible
                while window.base in window.unacked:
                    window.base += 1
                
                window.last_activity = time.time()
                self.stats['window_advances'] += 1
                return True
        
        return False
    
    def receive_packet(self, window_id: str, seq_num: int) -> bool:
        """Receive a packet in sliding window."""
        if window_id in self.sliding_windows:
            window = self.sliding_windows[window_id]
            
            if seq_num >= window.base:
                window.received.add(seq_num)
                window.last_activity = time.time()
                return True
        
        return False
    
    def get_window_status(self, window_id: str) -> Optional[Dict[str, Any]]:
        """Get sliding window status."""
        if window_id in self.sliding_windows:
            window = self.sliding_windows[window_id]
            return {
                'size': window.size,
                'base': window.base,
                'next_seq': window.next_seq,
                'unacked_count': len(window.unacked),
                'received_count': len(window.received),
                'available': window.size - len(window.unacked)
            }
        return None
    
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
    
    async def _timer_loop(self):
        """Background timer loop."""
        while self._running:
            try:
                await asyncio.sleep(1.0)  # Check timers every second
                self._process_expired_timers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in timer loop: {e}")
    
    def _process_expired_timers(self):
        """Process expired timers."""
        expired = self._check_expired_timers()
        
        for message_id in expired:
            if message_id in self.message_trackers:
                tracker = self.message_trackers[message_id]
                
                if tracker.retry_count < tracker.max_retries:
                    # Retry message
                    self.retry_message(message_id)
                    if tracker.qos == QoSLevel.AT_LEAST_ONCE:
                        self._add_ack_timer(message_id, tracker.timeout)
                else:
                    # Mark as failed
                    self.update_message_state(message_id, MessageState.FAILED)
    
    def _cleanup_expired(self):
        """Clean up expired entries."""
        now = time.time()
        
        # Clean up expired message trackers
        expired_trackers = [
            msg_id for msg_id, tracker in self.message_trackers.items()
            if now - tracker.created > tracker.timeout * 2
        ]
        
        for msg_id in expired_trackers:
            del self.message_trackers[msg_id]
        
        # Clean up expired reassembly buffers
        expired_buffers = [
            transfer_id for transfer_id, buffer in self.reassembly_buffers.items()
            if now > buffer.expires
        ]
        
        for transfer_id in expired_buffers:
            del self.reassembly_buffers[transfer_id]
        
        # Clean up expired sliding windows
        expired_windows = [
            window_id for window_id, window in self.sliding_windows.items()
            if now - window.last_activity > self.window_timeout
        ]
        
        for window_id in expired_windows:
            del self.sliding_windows[window_id]
        
        # Clean up expired duplicate cache entries
        expired_duplicates = [
            msg_id for msg_id, timestamp in self.duplicate_cache.items()
            if now - timestamp > self.duplicate_window
        ]
        
        for msg_id in expired_duplicates:
            del self.duplicate_cache[msg_id]
        
        self.last_cleanup = now
    
    # === Statistics and Export ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reliability statistics."""
        return {
            **self.stats,
            'current_trackers': len(self.message_trackers),
            'current_ack_timers': len(self.ack_timers),
            'current_reassembly_buffers': len(self.reassembly_buffers),
            'current_sliding_windows': len(self.sliding_windows),
            'duplicate_cache_size': len(self.duplicate_cache),
            'last_cleanup': self.last_cleanup
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export current reliability state."""
        return {
            'message_trackers': {
                msg_id: {
                    'qos': tracker.qos.value,
                    'state': tracker.state.value,
                    'retry_count': tracker.retry_count,
                    'created': tracker.created,
                    'destination': tracker.destination
                }
                for msg_id, tracker in self.message_trackers.items()
            },
            'reassembly_buffers': {
                transfer_id: {
                    'total_blocks': buffer.total_blocks,
                    'received_blocks': len(buffer.received_blocks),
                    'state': buffer.state.value,
                    'created': buffer.created
                }
                for transfer_id, buffer in self.reassembly_buffers.items()
            },
            'sliding_windows': {
                window_id: {
                    'size': window.size,
                    'base': window.base,
                    'next_seq': window.next_seq,
                    'unacked_count': len(window.unacked)
                }
                for window_id, window in self.sliding_windows.items()
            },
            'stats': self.get_stats()
        }
