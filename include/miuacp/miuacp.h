/**
 * @file miuacp.h
 * @brief µACP (Micro Agent Communication Protocol) C++ Library
 * 
 * This is the main header file for the µACP C++ library. It provides a lightweight,
 * agent-centric communication protocol designed for edge-native multi-agent systems.
 * 
 * The library includes:
 * - Core protocol implementation with fixed 8-byte headers
 * - TLV options system for extensibility
 * - 4 semantic verbs: PING, TELL, ASK, OBSERVE
 * - QoS levels: At-most-once, at-least-once, exactly-once
 * - High-performance message handling
 * 
 * @author Arnab
 * @version 1.0.0
 * @license MIT
 * @see https://github.com/Arnab-m1/miuACP
 */

#pragma once

// Core protocol components
#include "enums.h"
#include "header.h"
#include "option.h"
#include "message.h"
#include "protocol.h"

// Client, server, and agent components
#include "client.h"
#include "server.h"
#include "agent.h"

// Version information
#define MIUACP_VERSION_MAJOR 1
#define MIUACP_VERSION_MINOR 0
#define MIUACP_VERSION_PATCH 0
#define MIUACP_VERSION_STRING "1.0.0"

// Library information
#define MIUACP_AUTHOR "Arnab"
#define MIUACP_EMAIL "hello@arnab.wiki"
#define MIUACP_LICENSE "MIT"
#define MIUACP_DESCRIPTION "µACP: A lightweight agent communication protocol for edge-native multi-agent systems"

namespace miuacp {

/**
 * @brief Get library version string
 * @return Version string
 */
inline const char* getVersion() {
    return MIUACP_VERSION_STRING;
}

/**
 * @brief Get library author
 * @return Author string
 */
inline const char* getAuthor() {
    return MIUACP_AUTHOR;
}

/**
 * @brief Get library email
 * @return Email string
 */
inline const char* getEmail() {
    return MIUACP_EMAIL;
}

/**
 * @brief Get library license
 * @return License string
 */
inline const char* getLicense() {
    return MIUACP_LICENSE;
}

/**
 * @brief Get library description
 * @return Description string
 */
inline const char* getDescription() {
    return MIUACP_DESCRIPTION;
}

/**
 * @brief Get library version components
 * @param major Major version number
 * @param minor Minor version number
 * @param patch Patch version number
 */
inline void getVersionComponents(int& major, int& minor, int& patch) {
    major = MIUACP_VERSION_MAJOR;
    minor = MIUACP_VERSION_MINOR;
    patch = MIUACP_VERSION_PATCH;
}

} // namespace miuacp
