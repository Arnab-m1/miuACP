/**
 * @file udp_transport.cpp
 * @brief µACP UDP Transport Implementation
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 */

#include "miuacp/udp_transport.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <cstring>
#include <stdexcept>
#include <errno.h>

namespace miuacp {

UACPUdpTransport::UACPUdpTransport()
    : socket_fd_(-1)
    , local_port_(0)
    , is_bound_(false)
    , broadcast_enabled_(false)
{
    std::memset(&local_addr_, 0, sizeof(local_addr_));
}

UACPUdpTransport::~UACPUdpTransport() {
    close();
}

UACPUdpTransport::UACPUdpTransport(UACPUdpTransport&& other) noexcept
    : socket_fd_(other.socket_fd_)
    , local_addr_(other.local_addr_)
    , local_port_(other.local_port_)
    , is_bound_(other.is_bound_)
    , broadcast_enabled_(other.broadcast_enabled_)
    , multicast_group_(std::move(other.multicast_group_))
{
    other.socket_fd_ = -1;
    other.is_bound_ = false;
}

UACPUdpTransport& UACPUdpTransport::operator=(UACPUdpTransport&& other) noexcept {
    if (this != &other) {
        close();
        socket_fd_ = other.socket_fd_;
        local_addr_ = other.local_addr_;
        local_port_ = other.local_port_;
        is_bound_ = other.is_bound_;
        broadcast_enabled_ = other.broadcast_enabled_;
        multicast_group_ = std::move(other.multicast_group_);
        
        other.socket_fd_ = -1;
        other.is_bound_ = false;
    }
    return *this;
}

bool UACPUdpTransport::bind(const std::string& host, int port) {
    if (is_bound_) {
        return false;  // Already bound
    }
    
    // Create UDP socket
    socket_fd_ = socket(AF_INET, SOCK_DGRAM, 0);
    if (socket_fd_ < 0) {
        return false;
    }
    
    // Set SO_REUSEADDR to allow multiple agents on same machine
    setReuseAddress(true);
    
    // Prepare address structure
    std::memset(&local_addr_, 0, sizeof(local_addr_));
    local_addr_.sin_family = AF_INET;
    local_addr_.sin_port = htons(port);
    
    if (host == "0.0.0.0" || host.empty()) {
        local_addr_.sin_addr.s_addr = INADDR_ANY;
    } else {
        if (inet_pton(AF_INET, host.c_str(), &local_addr_.sin_addr) <= 0) {
            ::close(socket_fd_);
            socket_fd_ = -1;
            return false;
        }
    }
    
    // Bind socket
    if (::bind(socket_fd_, reinterpret_cast<sockaddr*>(&local_addr_), sizeof(local_addr_)) < 0) {
        ::close(socket_fd_);
        socket_fd_ = -1;
        return false;
    }
    
    // Get actual port if ephemeral (port == 0)
    if (port == 0) {
        sockaddr_in addr;
        socklen_t addr_len = sizeof(addr);
        if (getsockname(socket_fd_, reinterpret_cast<sockaddr*>(&addr), &addr_len) == 0) {
            local_port_ = ntohs(addr.sin_port);
        }
    } else {
        local_port_ = port;
    }
    
    is_bound_ = true;
    return true;
}

void UACPUdpTransport::close() {
    if (socket_fd_ >= 0) {
        // Leave multicast group if joined
        if (!multicast_group_.empty()) {
            ip_mreq mreq;
            std::memset(&mreq, 0, sizeof(mreq));
            inet_pton(AF_INET, multicast_group_.c_str(), &mreq.imr_multiaddr);
            mreq.imr_interface.s_addr = INADDR_ANY;
            setsockopt(socket_fd_, IPPROTO_IP, IP_DROP_MEMBERSHIP, &mreq, sizeof(mreq));
            multicast_group_.clear();
        }
        
        ::close(socket_fd_);
        socket_fd_ = -1;
    }
    is_bound_ = false;
    broadcast_enabled_ = false;
    local_port_ = 0;
}

bool UACPUdpTransport::isBound() const {
    return is_bound_ && socket_fd_ >= 0;
}

int UACPUdpTransport::getLocalPort() const {
    return local_port_;
}

bool UACPUdpTransport::sendToPeer(const std::vector<uint8_t>& data, 
                                 const std::string& peer_host, 
                                 int peer_port) {
    if (!is_bound_) {
        return false;
    }
    
    if (data.empty()) {
        return false;
    }
    
    if (data.size() > getMaxPacketSize()) {
        return false;  // Packet too large for UDP
    }
    
    // Prepare peer address
    sockaddr_in peer_addr;
    std::memset(&peer_addr, 0, sizeof(peer_addr));
    peer_addr.sin_family = AF_INET;
    peer_addr.sin_port = htons(peer_port);
    
    if (inet_pton(AF_INET, peer_host.c_str(), &peer_addr.sin_addr) <= 0) {
        return false;
    }
    
    // Send datagram
    ssize_t sent = sendto(socket_fd_, data.data(), data.size(), 0,
                         reinterpret_cast<sockaddr*>(&peer_addr), sizeof(peer_addr));
    
    return sent == static_cast<ssize_t>(data.size());
}

std::vector<uint8_t> UACPUdpTransport::receiveFromPeer(int timeout_ms, 
                                                      std::string& sender_host, 
                                                      int& sender_port) {
    if (!is_bound_) {
        return {};
    }
    
    // Wait for data with timeout
    if (timeout_ms >= 0) {
        if (!waitForReadable(timeout_ms)) {
            return {};  // Timeout
        }
    }
    
    // Receive datagram
    std::vector<uint8_t> buffer(getMaxPacketSize());
    sockaddr_in sender_addr;
    socklen_t sender_addr_len = sizeof(sender_addr);
    std::memset(&sender_addr, 0, sizeof(sender_addr));
    
    ssize_t received = recvfrom(socket_fd_, buffer.data(), buffer.size(), 0,
                               reinterpret_cast<sockaddr*>(&sender_addr), &sender_addr_len);
    
    if (received < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            return {};  // No data available (non-blocking)
        }
        return {};  // Error
    }
    
    if (received == 0) {
        return {};  // No data
    }
    
    // Extract sender info
    char sender_ip[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &sender_addr.sin_addr, sender_ip, INET_ADDRSTRLEN);
    sender_host = sender_ip;
    sender_port = ntohs(sender_addr.sin_port);
    
    // Resize buffer to actual received size
    buffer.resize(received);
    return buffer;
}

bool UACPUdpTransport::enableBroadcast() {
    if (!is_bound_) {
        return false;
    }
    
    int enable = 1;
    if (setsockopt(socket_fd_, SOL_SOCKET, SO_BROADCAST, &enable, sizeof(enable)) < 0) {
        return false;
    }
    
    broadcast_enabled_ = true;
    return true;
}

bool UACPUdpTransport::sendBroadcast(const std::vector<uint8_t>& data, int port) {
    if (!is_bound_ || !broadcast_enabled_) {
        return false;
    }
    
    if (data.empty() || data.size() > getMaxPacketSize()) {
        return false;
    }
    
    // Prepare broadcast address
    sockaddr_in broadcast_addr;
    std::memset(&broadcast_addr, 0, sizeof(broadcast_addr));
    broadcast_addr.sin_family = AF_INET;
    broadcast_addr.sin_port = htons(port);
    broadcast_addr.sin_addr.s_addr = INADDR_BROADCAST;  // 255.255.255.255
    
    // Send broadcast
    ssize_t sent = sendto(socket_fd_, data.data(), data.size(), 0,
                         reinterpret_cast<sockaddr*>(&broadcast_addr), sizeof(broadcast_addr));
    
    return sent == static_cast<ssize_t>(data.size());
}

bool UACPUdpTransport::enableMulticast(const std::string& group) {
    if (!is_bound_) {
        return false;
    }
    
    // Leave previous multicast group if any
    if (!multicast_group_.empty()) {
        ip_mreq mreq;
        std::memset(&mreq, 0, sizeof(mreq));
        inet_pton(AF_INET, multicast_group_.c_str(), &mreq.imr_multiaddr);
        mreq.imr_interface.s_addr = INADDR_ANY;
        setsockopt(socket_fd_, IPPROTO_IP, IP_DROP_MEMBERSHIP, &mreq, sizeof(mreq));
    }
    
    // Join new multicast group
    ip_mreq mreq;
    std::memset(&mreq, 0, sizeof(mreq));
    
    if (inet_pton(AF_INET, group.c_str(), &mreq.imr_multiaddr) <= 0) {
        return false;
    }
    
    mreq.imr_interface.s_addr = INADDR_ANY;
    
    if (setsockopt(socket_fd_, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) < 0) {
        return false;
    }
    
    multicast_group_ = group;
    return true;
}

bool UACPUdpTransport::setReceiveBufferSize(int size) {
    if (!is_bound_) {
        return false;
    }
    
    return setsockopt(socket_fd_, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size)) == 0;
}

bool UACPUdpTransport::setSendBufferSize(int size) {
    if (!is_bound_) {
        return false;
    }
    
    return setsockopt(socket_fd_, SOL_SOCKET, SO_SNDBUF, &size, sizeof(size)) == 0;
}

bool UACPUdpTransport::setReuseAddress(bool enable) {
    if (socket_fd_ < 0) {
        return false;
    }
    
    int opt = enable ? 1 : 0;
    return setsockopt(socket_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == 0;
}

bool UACPUdpTransport::setNonBlocking(bool enable) {
    if (socket_fd_ < 0) {
        return false;
    }
    
    int flags = fcntl(socket_fd_, F_GETFL, 0);
    if (flags < 0) {
        return false;
    }
    
    if (enable) {
        flags |= O_NONBLOCK;
    } else {
        flags &= ~O_NONBLOCK;
    }
    
    return fcntl(socket_fd_, F_SETFL, flags) == 0;
}

bool UACPUdpTransport::waitForReadable(int timeout_ms) {
    if (socket_fd_ < 0) {
        return false;
    }
    
    pollfd pfd;
    pfd.fd = socket_fd_;
    pfd.events = POLLIN;
    pfd.revents = 0;
    
    int result = poll(&pfd, 1, timeout_ms);
    
    if (result < 0) {
        return false;  // Error
    }
    
    if (result == 0) {
        return false;  // Timeout
    }
    
    return (pfd.revents & POLLIN) != 0;
}

} // namespace miuacp
