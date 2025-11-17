/**
 * @file test_comprehensive.cpp
 * @brief Comprehensive Test Suite for µACP C++ Library
 * 
 * This test suite provides extensive testing of all functionality in the µACP library,
 * including edge cases, error conditions, and performance characteristics.
 */

 #include <iostream>
 #include <cassert>
 #include <vector>
 #include <string>
 #include <chrono>
 #include <thread>
 #include <random>
 #include <algorithm>
 #include "miuacp/miuacp.h"
 
 using namespace miuacp;
 
 // Test utilities
 class TestSuite {
 private:
     std::string current_test_;
     int tests_passed_;
     int tests_failed_;
     std::vector<std::string> failed_tests_;
 
 public:
     TestSuite() : tests_passed_(0), tests_failed_(0) {}
     
     void startTest(const std::string& test_name) {
         current_test_ = test_name;
         std::cout << "Testing: " << test_name << "..." << std::flush;
     }
     
     void pass() {
         std::cout << " ✓ PASSED" << std::endl;
         tests_passed_++;
     }
     
     void fail(const std::string& reason = "") {
         std::cout << " ❌ FAILED";
         if (!reason.empty()) {
             std::cout << " (" << reason << ")";
         }
         std::cout << std::endl;
         tests_failed_++;
         failed_tests_.push_back(current_test_ + (reason.empty() ? "" : " - " + reason));
     }
     
    void assertTrue(bool condition, const std::string& message = "") {
        if (!condition) {
            fail(message);
            throw std::runtime_error("Assertion failed: " + message);
        }
    }
    
    void runTest(const std::function<void()>& test_func) {
        try {
            test_func();
        } catch (const std::exception& e) {
            fail("Exception: " + std::string(e.what()));
        } catch (...) {
            fail("Unknown exception");
        }
    }
     
     void assertFalse(bool condition, const std::string& message = "") {
         assertTrue(!condition, message);
     }
     
     void assertEqual(const std::string& expected, const std::string& actual, const std::string& message = "") {
         if (expected != actual) {
             fail(message + " (expected: '" + expected + "', actual: '" + actual + "')");
             throw std::runtime_error("Assertion failed: " + message);
         }
     }
     
     void assertEqual(int expected, int actual, const std::string& message = "") {
         if (expected != actual) {
             fail(message + " (expected: " + std::to_string(expected) + ", actual: " + std::to_string(actual) + ")");
             throw std::runtime_error("Assertion failed: " + message);
         }
     }
     
    void assertEqual(size_t expected, size_t actual, const std::string& message = "") {
        if (expected != actual) {
            fail(message + " (expected: " + std::to_string(expected) + ", actual: " + std::to_string(actual) + ")");
            throw std::runtime_error("Assertion failed: " + message);
        }
    }
    
    void assertEqual(uint32_t expected, uint32_t actual, const std::string& message = "") {
        if (expected != actual) {
            fail(message + " (expected: " + std::to_string(expected) + ", actual: " + std::to_string(actual) + ")");
            throw std::runtime_error("Assertion failed: " + message);
        }
    }
    
    void assertEqual(UACPVerb expected, UACPVerb actual, const std::string& message = "") {
        if (expected != actual) {
            fail(message + " (expected: " + std::to_string(static_cast<int>(expected)) + ", actual: " + std::to_string(static_cast<int>(actual)) + ")");
            throw std::runtime_error("Assertion failed: " + message);
        }
    }
    
    void assertEqual(UACPContentType expected, UACPContentType actual, const std::string& message = "") {
        if (expected != actual) {
            fail(message + " (expected: " + std::to_string(static_cast<int>(expected)) + ", actual: " + std::to_string(static_cast<int>(actual)) + ")");
            throw std::runtime_error("Assertion failed: " + message);
        }
    }
    
    void assertEqual(StatusCode expected, StatusCode actual, const std::string& message = "") {
        if (expected != actual) {
            fail(message + " (expected: " + std::to_string(static_cast<int>(expected)) + ", actual: " + std::to_string(static_cast<int>(actual)) + ")");
            throw std::runtime_error("Assertion failed: " + message);
        }
    }
    
    void assertEqual(const std::vector<uint8_t>& expected, const std::vector<uint8_t>& actual, const std::string& message = "") {
        if (expected != actual) {
            fail(message + " (vector sizes: expected " + std::to_string(expected.size()) + ", actual " + std::to_string(actual.size()) + ")");
            throw std::runtime_error("Assertion failed: " + message);
        }
    }
    
    void assertEqual(UACPOptionType expected, UACPOptionType actual, const std::string& message = "") {
        if (expected != actual) {
            fail(message + " (expected: " + std::to_string(static_cast<int>(expected)) + ", actual: " + std::to_string(static_cast<int>(actual)) + ")");
            throw std::runtime_error("Assertion failed: " + message);
        }
    }
     
    int getTestsPassed() const { return tests_passed_; }
    int getTestsFailed() const { return tests_failed_; }
    bool allTestsPassed() const { return tests_failed_ == 0; }
    
    void printSummary() {
        std::cout << "\n" << std::string(60, '=') << std::endl;
        std::cout << "TEST SUMMARY" << std::endl;
        std::cout << std::string(60, '=') << std::endl;
        std::cout << "Total Tests: " << (tests_passed_ + tests_failed_) << std::endl;
        std::cout << "Passed: " << tests_passed_ << std::endl;
        std::cout << "Failed: " << tests_failed_ << std::endl;
        
        if (tests_failed_ > 0) {
            std::cout << "\nFailed Tests:" << std::endl;
            for (const auto& test : failed_tests_) {
                std::cout << "  - " << test << std::endl;
            }
        }
        
        if (tests_failed_ == 0) {
            std::cout << "\n🎉 ALL TESTS PASSED! 🎉" << std::endl;
        } else {
            std::cout << "\n❌ " << tests_failed_ << " TESTS FAILED" << std::endl;
        }
    }
 };
 
 // Global test suite instance
 TestSuite g_test;
 
 // Test data generators
 class TestDataGenerator {
 private:
     std::mt19937 rng_;
     std::uniform_int_distribution<uint32_t> uint32_dist_;
     std::uniform_int_distribution<uint8_t> uint8_dist_;
 
 public:
     TestDataGenerator() : rng_(std::random_device{}()), uint32_dist_(1, 0xFFFFFF), uint8_dist_(0, 255) {}
     
     std::string generateRandomString(size_t length) {
         std::string result;
         result.reserve(length);
         for (size_t i = 0; i < length; ++i) {
             result += static_cast<char>('a' + (rng_() % 26));
         }
         return result;
     }
     
     std::vector<uint8_t> generateRandomBytes(size_t length) {
         std::vector<uint8_t> result(length);
         for (size_t i = 0; i < length; ++i) {
             result[i] = uint8_dist_(rng_);
         }
         return result;
     }
     
     uint32_t generateRandomUint32() {
         return uint32_dist_(rng_);
     }
     
     uint8_t generateRandomUint8() {
         return uint8_dist_(rng_);
     }
     
     UACPVerb generateRandomVerb() {
         return static_cast<UACPVerb>(rng_() % 4);
     }
     
     UACPOptionType generateRandomOptionType() {
         std::vector<UACPOptionType> types = {
             UACPOptionType::CONVERSATION_ID,
             UACPOptionType::CORRELATION_ID,
             UACPOptionType::TOPIC_PATH,
             UACPOptionType::CONTENT_TYPE,
             UACPOptionType::ETAG,
             UACPOptionType::MAX_AGE,
             UACPOptionType::BLOCK,
             UACPOptionType::AUTH,
             UACPOptionType::PRIORITY
         };
         return types[rng_() % types.size()];
     }
 };
 
 TestDataGenerator g_data_gen;
 
 // Test functions
 void testVersionInfo() {
     g_test.startTest("Version Information");
     
     g_test.assertEqual("1.0.0", std::string(getVersion()));
     g_test.assertEqual("Arnab", std::string(getAuthor()));
     g_test.assertEqual("hello@arnab.wiki", std::string(getEmail()));
     g_test.assertEqual("MIT", std::string(getLicense()));
     
     int major, minor, patch;
     getVersionComponents(major, minor, patch);
     g_test.assertEqual(1, major);
     g_test.assertEqual(0, minor);
     g_test.assertEqual(0, patch);
     
     g_test.pass();
 }
 
 void testEnums() {
     g_test.startTest("Protocol Enums");
     
     // Test UACPVerb
     g_test.assertEqual(0, static_cast<int>(UACPVerb::PING));
     g_test.assertEqual(1, static_cast<int>(UACPVerb::TELL));
     g_test.assertEqual(2, static_cast<int>(UACPVerb::ASK));
     g_test.assertEqual(3, static_cast<int>(UACPVerb::OBSERVE));
     
     // Test UACPOptionType
     g_test.assertEqual(0x01, static_cast<int>(UACPOptionType::CONVERSATION_ID));
     g_test.assertEqual(0x02, static_cast<int>(UACPOptionType::CORRELATION_ID));
     g_test.assertEqual(0x03, static_cast<int>(UACPOptionType::TOPIC_PATH));
     g_test.assertEqual(0x04, static_cast<int>(UACPOptionType::CONTENT_TYPE));
     g_test.assertEqual(0x05, static_cast<int>(UACPOptionType::ETAG));
     g_test.assertEqual(0x06, static_cast<int>(UACPOptionType::MAX_AGE));
     g_test.assertEqual(0x07, static_cast<int>(UACPOptionType::BLOCK));
     g_test.assertEqual(0x08, static_cast<int>(UACPOptionType::AUTH));
     g_test.assertEqual(0x09, static_cast<int>(UACPOptionType::PRIORITY));
     
     // Test UACPContentType
     g_test.assertEqual(0, static_cast<int>(UACPContentType::CBOR));
     g_test.assertEqual(1, static_cast<int>(UACPContentType::JSON));
     g_test.assertEqual(2, static_cast<int>(UACPContentType::PROTOBUF));
     g_test.assertEqual(3, static_cast<int>(UACPContentType::TEXT));
     
     // Test QoSLevel
     g_test.assertEqual(0, static_cast<int>(QoSLevel::AT_MOST_ONCE));
     g_test.assertEqual(1, static_cast<int>(QoSLevel::AT_LEAST_ONCE));
     g_test.assertEqual(2, static_cast<int>(QoSLevel::EXACTLY_ONCE));
     
     // Test StatusCode
    g_test.assertEqual(0, static_cast<int>(StatusCode::SUCCESS));
    g_test.assertEqual(0x40, static_cast<int>(StatusCode::BAD_REQUEST));
    g_test.assertEqual(0x80, static_cast<int>(StatusCode::INTERNAL_ERROR));
     
     g_test.pass();
 }
 
 void testConstants() {
     g_test.startTest("Protocol Constants");
     
     g_test.assertEqual(1, static_cast<int>(Constants::PROTOCOL_VERSION));
    g_test.assertEqual(static_cast<size_t>(8), Constants::HEADER_SIZE);
    g_test.assertEqual(static_cast<size_t>(65535), Constants::MAX_MESSAGE_SIZE);
    g_test.assertEqual(static_cast<size_t>(255), Constants::MAX_OPTIONS);
    g_test.assertEqual(static_cast<size_t>(1024), Constants::MAX_TOPIC_LENGTH);
    g_test.assertEqual(static_cast<size_t>(65527), Constants::MAX_PAYLOAD_SIZE);
    g_test.assertEqual(0xFFFFFFu, Constants::MAX_MESSAGE_ID);
     
     g_test.pass();
 }
 
 void testHeaderBasic() {
     g_test.startTest("Header Basic Operations");
     
     // Test default constructor
     UACPHeader header1;
     g_test.assertEqual(1, header1.getVersion());
     g_test.assertEqual(UACPVerb::PING, header1.getVerb());
     g_test.assertEqual(0, header1.getQoS());
     g_test.assertEqual(0, header1.getCode());
    g_test.assertEqual(0u, header1.getMessageId());
    g_test.assertEqual(0, header1.getOptionsCount());
     g_test.assertTrue(header1.isValid());
     
     // Test parameterized constructor
     UACPHeader header2(1, UACPVerb::TELL, 2, 5, 12345, 3);
     g_test.assertEqual(1, header2.getVersion());
     g_test.assertEqual(UACPVerb::TELL, header2.getVerb());
     g_test.assertEqual(2, header2.getQoS());
     g_test.assertEqual(5, header2.getCode());
    g_test.assertEqual(12345u, header2.getMessageId());
    g_test.assertEqual(3, header2.getOptionsCount());
     g_test.assertTrue(header2.isValid());
     
     // Test setters
     header2.setVersion(2);
     header2.setVerb(UACPVerb::ASK);
     header2.setQoS(1);
     header2.setCode(10);
     header2.setMessageId(54321);
     header2.setOptionsCount(5);
     
     g_test.assertEqual(2, header2.getVersion());
     g_test.assertEqual(UACPVerb::ASK, header2.getVerb());
     g_test.assertEqual(1, header2.getQoS());
     g_test.assertEqual(10, header2.getCode());
     g_test.assertEqual(54321u, header2.getMessageId());
     g_test.assertEqual(5, header2.getOptionsCount());
     
     g_test.pass();
 }
 
 void testHeaderPacking() {
     g_test.startTest("Header Packing/Unpacking");
     
     // Test packing
     UACPHeader original(1, UACPVerb::TELL, 2, 5, 12345, 3);
     auto packed = original.pack();
     g_test.assertEqual(static_cast<size_t>(8), packed.size());
     
     // Test unpacking
     auto unpacked = UACPHeader::unpack(packed);
     g_test.assertEqual(original.getVersion(), unpacked.getVersion());
     g_test.assertEqual(original.getVerb(), unpacked.getVerb());
     g_test.assertEqual(original.getQoS(), unpacked.getQoS());
     g_test.assertEqual(original.getCode(), unpacked.getCode());
     g_test.assertEqual(original.getMessageId(), unpacked.getMessageId());
     g_test.assertEqual(original.getOptionsCount(), unpacked.getOptionsCount());
     
     // Test unpacking with offset
     std::vector<uint8_t> data_with_offset = {0, 0, 0, 0, 0, 0, 0, 0};
     data_with_offset.insert(data_with_offset.end(), packed.begin(), packed.end());
     auto unpacked_with_offset = UACPHeader::unpack(data_with_offset, 8);
     g_test.assertEqual(original.getVersion(), unpacked_with_offset.getVersion());
     g_test.assertEqual(original.getVerb(), unpacked_with_offset.getVerb());
     
     // Test error conditions
     try {
         std::vector<uint8_t> short_data(4);
         UACPHeader::unpack(short_data);
         g_test.fail("Should have thrown exception for short data");
     } catch (const std::runtime_error&) {
         // Expected
     }
     
     g_test.pass();
 }
 
 void testHeaderValidation() {
     g_test.startTest("Header Validation");
     
     // Test valid headers
     UACPHeader valid1(1, UACPVerb::PING, 0, 0, 1, 0);
     g_test.assertTrue(valid1.isValid());
     
     UACPHeader valid2(1, UACPVerb::OBSERVE, 2, 0x84, 0xFFFFFF, 255);
     g_test.assertTrue(valid2.isValid());
     
     // Test invalid headers
     UACPHeader invalid1(4, UACPVerb::PING, 0, 0, 1, 0); // Invalid version
     g_test.assertFalse(invalid1.isValid());
     
     UACPHeader invalid2(1, UACPVerb::PING, 4, 0, 1, 0); // Invalid QoS
     g_test.assertFalse(invalid2.isValid());
     
     UACPHeader invalid3(1, UACPVerb::PING, 0, 0, 0x1000000, 0); // Invalid message ID
     g_test.assertFalse(invalid3.isValid());
     
     g_test.pass();
 }
 
 void testHeaderResponse() {
     g_test.startTest("Header Response Creation");
     
     UACPHeader request(1, UACPVerb::ASK, 1, 0, 12345, 2);
     auto response = UACPHeader::createResponse(request, StatusCode::SUCCESS);
     
     g_test.assertEqual(request.getVersion(), response.getVersion());
     g_test.assertEqual(request.getVerb(), response.getVerb());
     g_test.assertEqual(request.getQoS(), response.getQoS());
     g_test.assertEqual(static_cast<uint8_t>(StatusCode::SUCCESS), response.getCode());
     g_test.assertEqual(request.getMessageId(), response.getMessageId());
     g_test.assertEqual(0, response.getOptionsCount()); // Should be 0 for response
     
     g_test.pass();
 }
 
 void testOptionBasic() {
     g_test.startTest("Option Basic Operations");
     
     // Test default constructor
     UACPOption option1;
     g_test.assertEqual(UACPOptionType::TOPIC_PATH, option1.getType());
     g_test.assertFalse(option1.isStringValue());
     g_test.assertFalse(option1.isIntValue());
     
    // Test string option
    UACPOption string_opt(UACPOptionType::TOPIC_PATH, "test/topic");
    g_test.assertEqual(UACPOptionType::TOPIC_PATH, string_opt.getType());
    g_test.assertTrue(string_opt.isStringValue());
    g_test.assertFalse(string_opt.isIntValue());
    g_test.assertEqual("test/topic", string_opt.getStringValue());
    
    // Test integer option
    UACPOption int_opt(UACPOptionType::PRIORITY, 5u);
    g_test.assertEqual(UACPOptionType::PRIORITY, int_opt.getType());
    g_test.assertFalse(int_opt.isStringValue());
    g_test.assertTrue(int_opt.isIntValue());
    g_test.assertEqual(5u, int_opt.getIntValue());
    
    // Test byte array option
    std::vector<uint8_t> bytes = {0x48, 0x65, 0x6C, 0x6C, 0x6F};
    UACPOption bytes_opt(UACPOptionType::ETAG, bytes);
    g_test.assertEqual(UACPOptionType::ETAG, bytes_opt.getType());
    g_test.assertFalse(bytes_opt.isStringValue());
    g_test.assertFalse(bytes_opt.isIntValue());
    g_test.assertEqual(bytes.size(), bytes_opt.getBytesValue().size());
    
    g_test.pass();
}

void testOptionPacking() {
    g_test.startTest("Option Packing/Unpacking");
    
    // Test string option packing/unpacking
    UACPOption string_opt(UACPOptionType::TOPIC_PATH, "test/topic");
    auto packed = string_opt.pack();
    g_test.assertTrue(packed.size() > 0);
    
    UACPOption unpacked_string;
    size_t consumed = UACPOption::unpack(packed, 0, unpacked_string);
    g_test.assertEqual(packed.size(), consumed);
    g_test.assertEqual(string_opt.getType(), unpacked_string.getType());
    g_test.assertEqual(string_opt.getStringValue(), unpacked_string.getStringValue());
    
    // Test integer option packing/unpacking
    UACPOption int_opt(UACPOptionType::PRIORITY, 7u);
    auto packed_int = int_opt.pack();
    
    UACPOption unpacked_int;
    consumed = UACPOption::unpack(packed_int, 0, unpacked_int);
    g_test.assertEqual(packed_int.size(), consumed);
    g_test.assertEqual(int_opt.getType(), unpacked_int.getType());
    g_test.assertEqual(int_opt.getIntValue(), unpacked_int.getIntValue());
    
    // Test error conditions
    try {
        std::vector<uint8_t> short_data(1);
        UACPOption dummy;
        UACPOption::unpack(short_data, 0, dummy);
        g_test.fail("Should have thrown exception for short data");
    } catch (const std::runtime_error&) {
        // Expected
    }
    
    g_test.pass();
}

void testOptionSizes() {
    g_test.startTest("Option Size Calculations");
    
    // Test different option sizes
    UACPOption short_opt(UACPOptionType::PRIORITY, 1u);
    g_test.assertEqual(static_cast<size_t>(6), short_opt.getPackedSize()); // Type(1) + Length(1) + Value(4)
    
    UACPOption string_opt(UACPOptionType::TOPIC_PATH, "test");
    g_test.assertEqual(static_cast<size_t>(6), string_opt.getPackedSize()); // Type(1) + Length(1) + Value(4)
    
    UACPOption long_opt(UACPOptionType::TOPIC_PATH, "very/long/topic/path/that/exceeds/normal/length");
    g_test.assertEqual(2 + long_opt.getStringValue().size(), long_opt.getPackedSize());
    
    g_test.pass();
}

void testMessageBasic() {
    g_test.startTest("Message Basic Operations");
    
    // Test default constructor
    UACPMessage msg1;
    g_test.assertEqual(UACPVerb::PING, msg1.getHeader().getVerb());
    g_test.assertEqual(static_cast<size_t>(0), msg1.getPayload().size());
    g_test.assertEqual(static_cast<size_t>(0), msg1.getOptions().size());
    g_test.assertTrue(msg1.isValid());
    
    // Test constructor with parameters
    std::vector<uint8_t> payload = {'H', 'e', 'l', 'l', 'o'};
    UACPMessage msg2(UACPVerb::TELL, payload, 12345, 1, 0);
    g_test.assertEqual(UACPVerb::TELL, msg2.getHeader().getVerb());
    g_test.assertEqual(12345u, msg2.getHeader().getMessageId());
    g_test.assertEqual(1, msg2.getHeader().getQoS());
    g_test.assertEqual(0, msg2.getHeader().getCode());
    g_test.assertEqual(payload.size(), msg2.getPayload().size());
    g_test.assertEqual("Hello", msg2.getPayloadAsString());
    g_test.assertTrue(msg2.isValid());
    
    // Test copy constructor
    UACPMessage msg3(msg2);
    g_test.assertEqual(msg2.getHeader().getVerb(), msg3.getHeader().getVerb());
    g_test.assertEqual(msg2.getHeader().getMessageId(), msg3.getHeader().getMessageId());
    g_test.assertEqual(msg2.getPayloadAsString(), msg3.getPayloadAsString());
    
    // Test move constructor
    std::vector<uint8_t> test_payload = {'t', 'e', 's', 't'};
    UACPMessage msg4(std::move(UACPMessage(UACPVerb::ASK, test_payload, 54321, 0, 0)));
    g_test.assertEqual(UACPVerb::ASK, msg4.getHeader().getVerb());
    g_test.assertEqual(54321u, msg4.getHeader().getMessageId());
    g_test.assertEqual("test", msg4.getPayloadAsString());
    
    g_test.pass();
}

void testMessageOptions() {
    g_test.startTest("Message Options Management");
    
    UACPMessage msg;
    
    // Test adding options
    msg.addOption(UACPOptionType::TOPIC_PATH, "test/topic");
    msg.addOption(UACPOptionType::PRIORITY, 5u);
    msg.addOption(UACPOptionType::MAX_AGE, 3600u);
    
    g_test.assertEqual(static_cast<size_t>(3), msg.getOptions().size());
    g_test.assertEqual(3, msg.getHeader().getOptionsCount());
    
    // Test getting options
    const UACPOption* topic_opt = msg.getOption(UACPOptionType::TOPIC_PATH);
    g_test.assertTrue(topic_opt != nullptr);
    g_test.assertEqual("test/topic", topic_opt->getStringValue());
    
    const UACPOption* priority_opt = msg.getOption(UACPOptionType::PRIORITY);
    g_test.assertTrue(priority_opt != nullptr);
    g_test.assertEqual(5u, priority_opt->getIntValue());
    
    // Test option replacement
    msg.addOption(UACPOptionType::TOPIC_PATH, "new/topic");
    g_test.assertEqual(static_cast<size_t>(3), msg.getOptions().size()); // Should still be 3
    g_test.assertEqual("new/topic", msg.getOption(UACPOptionType::TOPIC_PATH)->getStringValue());
    
    // Test removing options
    bool removed = msg.removeOption(UACPOptionType::PRIORITY);
    g_test.assertTrue(removed);
    g_test.assertEqual(static_cast<size_t>(2), msg.getOptions().size());
    g_test.assertTrue(msg.getOption(UACPOptionType::PRIORITY) == nullptr);
    
    // Test removing non-existent option
    removed = msg.removeOption(UACPOptionType::AUTH);
    g_test.assertFalse(removed);
    g_test.assertEqual(static_cast<size_t>(2), msg.getOptions().size());
    
    g_test.pass();
}

void testMessagePayload() {
    g_test.startTest("Message Payload Operations");
    
    UACPMessage msg;
    
    // Test string payload
    msg.setPayload("Hello World");
    g_test.assertEqual("Hello World", msg.getPayloadAsString());
    g_test.assertEqual(static_cast<size_t>(11), msg.getPayload().size());

    // Test byte array payload
    std::vector<uint8_t> bytes = {0x48, 0x65, 0x6C, 0x6C, 0x6F};
    msg.setPayload(bytes);
    g_test.assertEqual(bytes.size(), msg.getPayload().size());
    g_test.assertEqual("Hello", msg.getPayloadAsString());
    
    // Test empty payload
    msg.setPayload("");
    g_test.assertEqual(static_cast<size_t>(0), msg.getPayload().size());
    g_test.assertEqual("", msg.getPayloadAsString());
    
    g_test.pass();
}

void testMessagePacking() {
    g_test.startTest("Message Packing/Unpacking");
    
    // Create a complex message
    std::vector<uint8_t> hello_world = {'H', 'e', 'l', 'l', 'o', ' ', 'W', 'o', 'r', 'l', 'd'};
    UACPMessage original(UACPVerb::TELL, hello_world, 12345, 1, 0);
    original.addOption(UACPOptionType::TOPIC_PATH, "test/topic");
    original.addOption(UACPOptionType::PRIORITY, 5u);
    original.addOption(UACPOptionType::CONTENT_TYPE, static_cast<uint32_t>(UACPContentType::JSON));
    
    // Test packing
    auto packed = original.pack();
    g_test.assertTrue(packed.size() > 0);
    g_test.assertEqual(original.getPackedSize(), packed.size());
    
    // Test unpacking
    auto unpacked = UACPMessage::unpack(packed);
    g_test.assertEqual(original.getHeader().getVerb(), unpacked.getHeader().getVerb());
    g_test.assertEqual(original.getHeader().getMessageId(), unpacked.getHeader().getMessageId());
    g_test.assertEqual(original.getHeader().getQoS(), unpacked.getHeader().getQoS());
    g_test.assertEqual(original.getHeader().getCode(), unpacked.getHeader().getCode());
    g_test.assertEqual(original.getHeader().getOptionsCount(), unpacked.getHeader().getOptionsCount());
    g_test.assertEqual(original.getPayloadAsString(), unpacked.getPayloadAsString());
    g_test.assertEqual(original.getOptions().size(), unpacked.getOptions().size());
    
    // Test unpacking with offset
    std::vector<uint8_t> data_with_offset = {0, 0, 0, 0};
    data_with_offset.insert(data_with_offset.end(), packed.begin(), packed.end());
    auto unpacked_with_offset = UACPMessage::unpack(data_with_offset, 4);
    g_test.assertEqual(original.getPayloadAsString(), unpacked_with_offset.getPayloadAsString());
    
    // Test error conditions
    try {
        std::vector<uint8_t> short_data(4);
        UACPMessage::unpack(short_data);
        g_test.fail("Should have thrown exception for short data");
    } catch (const std::runtime_error&) {
        // Expected
    }
    
    g_test.pass();
}

void testMessageValidation() {
    g_test.startTest("Message Validation");
    
    // Test valid messages
    UACPMessage valid1(UACPVerb::PING, std::vector<uint8_t>(), 1, 0, 0);
    g_test.assertTrue(valid1.isValid());
    
    std::vector<uint8_t> hello_payload = {'H', 'e', 'l', 'l', 'o'};
    UACPMessage valid2(UACPVerb::TELL, hello_payload, 12345, 2, 0);
    valid2.addOption(UACPOptionType::TOPIC_PATH, "test");
    g_test.assertTrue(valid2.isValid());
    
    // Test invalid message (too large)
    std::string large_payload(Constants::MAX_PAYLOAD_SIZE + 1, 'A');
    std::vector<uint8_t> large_payload_vec(large_payload.begin(), large_payload.end());
    UACPMessage invalid1(UACPVerb::TELL, large_payload_vec, 1, 0, 0);
    g_test.assertFalse(invalid1.isValid());
    
    g_test.pass();
}

void testMessageResponse() {
    g_test.startTest("Message Response Creation");
    
    std::vector<uint8_t> request_payload = {'R', 'e', 'q', 'u', 'e', 's', 't', ' ', 'd', 'a', 't', 'a'};
    UACPMessage request(UACPVerb::ASK, request_payload, 12345, 1, 0);
    request.addOption(UACPOptionType::TOPIC_PATH, "test/request");
    
    // Test response with byte payload
    std::vector<uint8_t> response_payload = {'R', 'e', 's', 'p', 'o', 'n', 's', 'e'};
    auto response1 = request.createResponse(StatusCode::SUCCESS, response_payload);
    
    g_test.assertEqual(request.getHeader().getVerb(), response1.getHeader().getVerb());
    g_test.assertEqual(request.getHeader().getMessageId(), response1.getHeader().getMessageId());
    g_test.assertEqual(static_cast<uint8_t>(StatusCode::SUCCESS), response1.getHeader().getCode());
    g_test.assertEqual("Response", response1.getPayloadAsString());
    g_test.assertTrue(response1.isResponse());
    g_test.assertFalse(response1.isRequest());
    
    // Test response with string payload
    auto response2 = request.createResponse(StatusCode::NOT_FOUND, "Not found");
    g_test.assertEqual(static_cast<uint8_t>(StatusCode::NOT_FOUND), response2.getHeader().getCode());
    g_test.assertEqual("Not found", response2.getPayloadAsString());
    
    g_test.pass();
}

void testMessageHelpers() {
    g_test.startTest("Message Helper Functions");
    
    UACPMessage msg;
    
    // Test topic path helpers
    msg.setTopicPath("sensors/temperature");
    g_test.assertEqual("sensors/temperature", msg.getTopicPath());
    
    // Test content type helpers
    msg.setContentType(UACPContentType::JSON);
    g_test.assertEqual(UACPContentType::JSON, msg.getContentType());
    
    // Test default content type
    UACPMessage msg2;
    g_test.assertEqual(UACPContentType::CBOR, msg2.getContentType());
    
    // Test request/response detection
    std::vector<uint8_t> test_payload = {'t', 'e', 's', 't'};
    UACPMessage request(UACPVerb::ASK, test_payload, 1, 0, 0);
    g_test.assertTrue(request.isRequest());
    g_test.assertFalse(request.isResponse());
    
    auto response = request.createResponse(StatusCode::SUCCESS, "ok");
    g_test.assertFalse(response.isRequest());
    g_test.assertTrue(response.isResponse());
    
    g_test.pass();
}

void testProtocolBasic() {
    g_test.startTest("Protocol Basic Operations");
    
    UACPProtocol protocol;
    
    // Test protocol constants
    g_test.assertEqual(1, UACPProtocol::getProtocolVersion());
    g_test.assertEqual(static_cast<size_t>(65535), UACPProtocol::getMaxMessageSize());
    g_test.assertEqual(static_cast<size_t>(65527), UACPProtocol::getMaxPayloadSize());
    
    // Test message size validation
    g_test.assertTrue(UACPProtocol::isValidMessageSize(1000));
    g_test.assertTrue(UACPProtocol::isValidMessageSize(65535));
    g_test.assertFalse(UACPProtocol::isValidMessageSize(65536));
    
    g_test.assertTrue(UACPProtocol::isValidPayloadSize(1000));
    g_test.assertTrue(UACPProtocol::isValidPayloadSize(65527));
    g_test.assertFalse(UACPProtocol::isValidPayloadSize(65528));
    
    g_test.pass();
}

void testProtocolMessageCreation() {
    g_test.startTest("Protocol Message Creation");
    
    UACPProtocol protocol;
    
    // Test PING message creation
    auto ping1 = protocol.createPing();
    g_test.assertEqual(UACPVerb::PING, ping1.getHeader().getVerb());
    g_test.assertEqual(static_cast<size_t>(0), ping1.getPayload().size());
    g_test.assertTrue(ping1.getHeader().getMessageId() > 0);
    
    auto ping2 = protocol.createPing(12345);
    g_test.assertEqual(12345u, ping2.getHeader().getMessageId());
    
    // Test TELL message creation
    auto tell1 = protocol.createTell("Hello World");
    g_test.assertEqual(UACPVerb::TELL, tell1.getHeader().getVerb());
    g_test.assertEqual("Hello World", tell1.getPayloadAsString());
    
    auto tell2 = protocol.createTell("Hello", "test/topic", 54321, 1);
    g_test.assertEqual("Hello", tell2.getPayloadAsString());
    g_test.assertEqual("test/topic", tell2.getTopicPath());
    g_test.assertEqual(54321u, tell2.getHeader().getMessageId());
    g_test.assertEqual(1, tell2.getHeader().getQoS());
    
    // Test ASK message creation
    auto ask1 = protocol.createAsk("Request data");
    g_test.assertEqual(UACPVerb::ASK, ask1.getHeader().getVerb());
    g_test.assertEqual("Request data", ask1.getPayloadAsString());
    g_test.assertEqual(1, ask1.getHeader().getQoS()); // Default QoS for ASK
    
    auto ask2 = protocol.createAsk("Request", "test/ask", 99999, 2);
    g_test.assertEqual("Request", ask2.getPayloadAsString());
    g_test.assertEqual("test/ask", ask2.getTopicPath());
    g_test.assertEqual(99999u, ask2.getHeader().getMessageId());
    g_test.assertEqual(2, ask2.getHeader().getQoS());
    
    // Test OBSERVE message creation
    auto observe1 = protocol.createObserve("Subscribe", "sensors/temp");
    g_test.assertEqual(UACPVerb::OBSERVE, observe1.getHeader().getVerb());
    g_test.assertEqual("Subscribe", observe1.getPayloadAsString());
    g_test.assertEqual("sensors/temp", observe1.getTopicPath());
    g_test.assertEqual(1, observe1.getHeader().getQoS()); // Default QoS for OBSERVE
    
    // Test OBSERVE without topic (should throw)
    try {
        protocol.createObserve("Subscribe", "");
        g_test.fail("Should have thrown exception for empty topic");
    } catch (const std::runtime_error&) {
        // Expected
    }
    
    g_test.pass();
}

void testProtocolMessageValidation() {
    g_test.startTest("Protocol Message Validation");
    
    UACPProtocol protocol;
    
    // Test valid messages
    auto valid1 = protocol.createPing();
    g_test.assertTrue(protocol.validateMessage(valid1));
    
    auto valid2 = protocol.createTell("Hello", "test/topic");
    g_test.assertTrue(protocol.validateMessage(valid2));
    
    auto valid3 = protocol.createAsk("Request", "test/ask");
    g_test.assertTrue(protocol.validateMessage(valid3));
    
    auto valid4 = protocol.createObserve("Subscribe", "test/observe");
    g_test.assertTrue(protocol.validateMessage(valid4));
    
    // Test invalid message
    UACPMessage invalid(UACPVerb::PING, std::vector<uint8_t>(), 0x1000000, 0, 0); // Invalid message ID
    g_test.assertFalse(protocol.validateMessage(invalid));
    
    g_test.pass();
}

void testProtocolMessageIdGeneration() {
    g_test.startTest("Protocol Message ID Generation");
    
    UACPProtocol protocol;
    
    // Test multiple message ID generation
    std::set<uint32_t> message_ids;
    for (int i = 0; i < 1000; ++i) {
        uint32_t id = protocol.generateMessageId();
        g_test.assertTrue(id > 0);
        g_test.assertTrue(id <= Constants::MAX_MESSAGE_ID);
        message_ids.insert(id);
    }
    
    // Check for uniqueness (should be very high probability of uniqueness)
    g_test.assertTrue(message_ids.size() > 900, "Message IDs should be mostly unique");
    
    g_test.pass();
}

void testProtocolBinaryPayload() {
    g_test.startTest("Protocol Binary Payload Creation");
    
    UACPProtocol protocol;
    
    // Test with binary payload
    std::vector<uint8_t> binary_data = {0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x57, 0x6F, 0x72, 0x6C, 0x64};
    auto tell_binary = protocol.createTell(binary_data, "binary/test");
    g_test.assertEqual(UACPVerb::TELL, tell_binary.getHeader().getVerb());
    g_test.assertEqual(binary_data.size(), tell_binary.getPayload().size());
    g_test.assertEqual("Hello World", tell_binary.getPayloadAsString());
    g_test.assertEqual("binary/test", tell_binary.getTopicPath());
    
    auto ask_binary = protocol.createAsk(binary_data, "binary/request");
    g_test.assertEqual(UACPVerb::ASK, ask_binary.getHeader().getVerb());
    g_test.assertEqual(binary_data.size(), ask_binary.getPayload().size());
    
    auto observe_binary = protocol.createObserve(binary_data, "binary/subscribe");
    g_test.assertEqual(UACPVerb::OBSERVE, observe_binary.getHeader().getVerb());
    g_test.assertEqual(binary_data.size(), observe_binary.getPayload().size());
    
    g_test.pass();
}

void testRandomData() {
    g_test.startTest("Random Data Handling");
    
    UACPProtocol protocol;
    
    // Test with random data
    for (int i = 0; i < 100; ++i) {
        // Generate random message
        auto verb = g_data_gen.generateRandomVerb();
        auto payload = g_data_gen.generateRandomString(50);
        auto topic = g_data_gen.generateRandomString(20);
        auto msg_id = g_data_gen.generateRandomUint32();
        auto qos = g_data_gen.generateRandomUint8() % 3;
        
        UACPMessage msg;
        switch (verb) {
            case UACPVerb::PING:
                msg = protocol.createPing(msg_id);
                break;
            case UACPVerb::TELL:
                msg = protocol.createTell(payload, topic, msg_id, qos);
                break;
            case UACPVerb::ASK:
                msg = protocol.createAsk(payload, topic, msg_id, qos);
                break;
            case UACPVerb::OBSERVE:
                if (!topic.empty()) {
                    msg = protocol.createObserve(payload, topic, msg_id, qos);
                } else {
                    continue; // Skip invalid observe
                }
                break;
        }
        
        // Test message validity
        g_test.assertTrue(msg.isValid());
        
        // Test packing/unpacking
        auto packed = msg.pack();
        auto unpacked = UACPMessage::unpack(packed);
        g_test.assertEqual(msg.getHeader().getVerb(), unpacked.getHeader().getVerb());
        g_test.assertEqual(msg.getHeader().getMessageId(), unpacked.getHeader().getMessageId());
        g_test.assertEqual(msg.getPayloadAsString(), unpacked.getPayloadAsString());
    }
    
    g_test.pass();
}

void testEdgeCases() {
    g_test.startTest("Edge Cases and Boundary Conditions");
    
    UACPProtocol protocol;
    
    // Test maximum message ID
    auto max_id_msg = protocol.createPing(Constants::MAX_MESSAGE_ID);
    g_test.assertEqual(Constants::MAX_MESSAGE_ID, max_id_msg.getHeader().getMessageId());
    g_test.assertTrue(max_id_msg.isValid());
    
    // Test maximum QoS
    auto max_qos_msg = protocol.createTell("test", "topic", 1, 2);
    g_test.assertEqual(2, max_qos_msg.getHeader().getQoS());
    g_test.assertTrue(max_qos_msg.isValid());
    
    // Test maximum status code
    std::vector<uint8_t> test_payload = {'t', 'e', 's', 't'};
    UACPMessage request(UACPVerb::ASK, test_payload, 1, 0, 0);
    auto max_code_response = request.createResponse(StatusCode::GATEWAY_TIMEOUT, "timeout");
    g_test.assertEqual(static_cast<uint8_t>(StatusCode::GATEWAY_TIMEOUT), max_code_response.getHeader().getCode());
    
    // Test empty string payload
    auto empty_msg = protocol.createTell("", "empty");
    g_test.assertEqual(static_cast<size_t>(0), empty_msg.getPayload().size());
    g_test.assertEqual("", empty_msg.getPayloadAsString());
    g_test.assertTrue(empty_msg.isValid());
    
    // Test single character payload
    auto single_char_msg = protocol.createTell("A", "single");
    g_test.assertEqual(static_cast<size_t>(1), single_char_msg.getPayload().size());
    g_test.assertEqual("A", single_char_msg.getPayloadAsString());
    
    // Test maximum topic length
    std::string long_topic(Constants::MAX_TOPIC_LENGTH, 'a');
    auto long_topic_msg = protocol.createTell("test", long_topic);
    g_test.assertEqual(long_topic, long_topic_msg.getTopicPath());
    g_test.assertTrue(long_topic_msg.isValid());
    
    // Test large payload size (but within message size limits)
    size_t safe_payload_size = Constants::MAX_MESSAGE_SIZE - 100; // Leave room for header and options
    std::string large_payload(safe_payload_size, 'X');
    auto large_msg = protocol.createTell(large_payload, "large");
    g_test.assertEqual(safe_payload_size, large_msg.getPayload().size());
    g_test.assertTrue(large_msg.isValid());
    
    g_test.pass();
}

void testPerformance() {
    g_test.startTest("Performance Characteristics");
    
    UACPProtocol protocol;
    
    // Test message creation performance
    auto start = std::chrono::high_resolution_clock::now();
    const int num_messages = 10000;
    
    for (int i = 0; i < num_messages; ++i) {
        auto msg = protocol.createTell("Performance test message", "test/performance");
        auto packed = msg.pack();
        auto unpacked = UACPMessage::unpack(packed);
        (void)unpacked; // Suppress unused variable warning
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << " (" << num_messages << " messages in " << duration.count() << "ms)";
    
    // Performance should be reasonable (less than 1 second for 10k messages)
    g_test.assertTrue(duration.count() < 1000, "Performance should be under 1 second for 10k messages");
    
    g_test.pass();
}

void testMemoryUsage() {
    g_test.startTest("Memory Usage and Leaks");
    
    UACPProtocol protocol;
    
    // Test that objects can be created and destroyed without issues
    for (int i = 0; i < 1000; ++i) {
        UACPMessage msg = protocol.createTell("Memory test", "test/memory");
        msg.addOption(UACPOptionType::PRIORITY, static_cast<uint32_t>(i % 8));
        msg.addOption(UACPOptionType::MAX_AGE, static_cast<uint32_t>(i * 10));
        
        auto packed = msg.pack();
        auto unpacked = UACPMessage::unpack(packed);
        
        // Test copy and move semantics
        UACPMessage copied = unpacked;
        UACPMessage moved = std::move(copied);
        
        // Test assignment
        UACPMessage assigned;
        assigned = moved;
        
        (void)assigned; // Suppress unused variable warning
    }
    
    g_test.pass();
}

void testConcurrency() {
    g_test.startTest("Concurrency and Thread Safety");
    
    UACPProtocol protocol;
    std::vector<std::thread> threads;
    std::atomic<int> success_count{0};
    const int num_threads = 10;
    const int messages_per_thread = 100;
    
    // Test concurrent message creation
    for (int t = 0; t < num_threads; ++t) {
        threads.emplace_back([&protocol, &success_count, t, messages_per_thread]() {
            for (int i = 0; i < messages_per_thread; ++i) {
                try {
                    auto msg = protocol.createTell("Thread " + std::to_string(t) + " message " + std::to_string(i), 
                                                  "test/concurrent");
                    auto packed = msg.pack();
                    auto unpacked = UACPMessage::unpack(packed);
                    
                    if (unpacked.getPayloadAsString().find("Thread " + std::to_string(t)) != std::string::npos) {
                        success_count++;
                    }
                } catch (...) {
                    // Count failures
                }
            }
        });
    }
    
    // Wait for all threads to complete
    for (auto& thread : threads) {
        thread.join();
    }
    
    // All messages should have been processed successfully
    g_test.assertEqual(num_threads * messages_per_thread, success_count.load());
    
    g_test.pass();
}

void testErrorHandling() {
    g_test.startTest("Error Handling and Recovery");
    
    // Test invalid header unpacking
    try {
        std::vector<uint8_t> invalid_data(4); // Too short
        UACPHeader::unpack(invalid_data);
        g_test.fail("Should have thrown exception for invalid header data");
    } catch (const std::runtime_error&) {
        // Expected
    }
    
    // Test invalid option unpacking
    try {
        std::vector<uint8_t> invalid_option(1); // Too short
        UACPOption dummy;
        UACPOption::unpack(invalid_option, 0, dummy);
        g_test.fail("Should have thrown exception for invalid option data");
    } catch (const std::runtime_error&) {
        // Expected
    }
    
    // Test invalid message unpacking
    try {
        std::vector<uint8_t> invalid_message(4); // Too short
        UACPMessage::unpack(invalid_message);
        g_test.fail("Should have thrown exception for invalid message data");
    } catch (const std::runtime_error&) {
        // Expected
    }
    
    // Test option value type errors
    try {
        UACPOption int_opt(UACPOptionType::PRIORITY, 5u);
        int_opt.getStringValue(); // Should throw
        g_test.fail("Should have thrown exception for wrong value type");
    } catch (const std::runtime_error&) {
        // Expected
    }
    
    try {
        UACPOption string_opt(UACPOptionType::TOPIC_PATH, "test");
        string_opt.getIntValue(); // Should throw
        g_test.fail("Should have thrown exception for wrong value type");
    } catch (const std::runtime_error&) {
        // Expected
    }
    
    g_test.pass();
}

void testOptionEdgeCases() {
    g_test.startTest("Option Edge Cases");
    
    // Test option with maximum length value
    std::string max_value(255, 'X'); // Maximum option value length
    UACPOption max_opt(UACPOptionType::TOPIC_PATH, max_value);
    g_test.assertEqual(max_value, max_opt.getStringValue());
    g_test.assertTrue(max_opt.getPackedSize() > 0);
    
    // Test option with empty value
    UACPOption empty_opt(UACPOptionType::TOPIC_PATH, "");
    g_test.assertEqual("", empty_opt.getStringValue());
    g_test.assertEqual(static_cast<size_t>(2), empty_opt.getPackedSize()); // Type(1) + Length(1) + Value(0)
    
    // Test option with single character value
    UACPOption single_opt(UACPOptionType::TOPIC_PATH, "A");
    g_test.assertEqual("A", single_opt.getStringValue());
    g_test.assertEqual(static_cast<size_t>(3), single_opt.getPackedSize()); // Type(1) + Length(1) + Value(1)
    
    // Test integer option with maximum value
    UACPOption max_int_opt(UACPOptionType::PRIORITY, 0xFFFFFFFF);
    g_test.assertEqual(0xFFFFFFFF, max_int_opt.getIntValue());
    
    // Test integer option with minimum value
    UACPOption min_int_opt(UACPOptionType::PRIORITY, 0);
    g_test.assertEqual(0u, min_int_opt.getIntValue());
    
    g_test.pass();
}

void testMessageEdgeCases() {
    g_test.startTest("Message Edge Cases");
    
    UACPProtocol protocol;
    
    // Test message with multiple options of different types
    UACPMessage max_options_msg = protocol.createTell("test", "topic");
    // Add all available option types
    max_options_msg.addOption(UACPOptionType::CONVERSATION_ID, "conv1");
    max_options_msg.addOption(UACPOptionType::CORRELATION_ID, 12345u);
    max_options_msg.addOption(UACPOptionType::TOPIC_PATH, "test/topic");
    max_options_msg.addOption(UACPOptionType::CONTENT_TYPE, static_cast<uint32_t>(UACPContentType::JSON));
    max_options_msg.addOption(UACPOptionType::ETAG, "etag1");
    max_options_msg.addOption(UACPOptionType::MAX_AGE, 3600u);
    max_options_msg.addOption(UACPOptionType::BLOCK, std::vector<uint8_t>{1, 2, 3, 4});
    max_options_msg.addOption(UACPOptionType::AUTH, "auth1");
    max_options_msg.addOption(UACPOptionType::PRIORITY, 5u);
    g_test.assertEqual(static_cast<size_t>(9), max_options_msg.getOptions().size());
    g_test.assertTrue(max_options_msg.isValid());
    
    // Test message with all option types
    UACPMessage all_options_msg = protocol.createTell("test", "topic");
    all_options_msg.addOption(UACPOptionType::CONVERSATION_ID, "conv123");
    all_options_msg.addOption(UACPOptionType::CORRELATION_ID, 12345u);
    all_options_msg.addOption(UACPOptionType::TOPIC_PATH, "test/topic");
    all_options_msg.addOption(UACPOptionType::CONTENT_TYPE, static_cast<uint32_t>(UACPContentType::JSON));
    all_options_msg.addOption(UACPOptionType::ETAG, "etag123");
    all_options_msg.addOption(UACPOptionType::MAX_AGE, 3600u);
    all_options_msg.addOption(UACPOptionType::BLOCK, std::vector<uint8_t>{1, 2, 3, 4});
    all_options_msg.addOption(UACPOptionType::AUTH, "auth123");
    all_options_msg.addOption(UACPOptionType::PRIORITY, 5u);
    
    g_test.assertEqual(static_cast<size_t>(9), all_options_msg.getOptions().size());
    g_test.assertTrue(all_options_msg.isValid());
    
    // Test message with binary payload containing null bytes
    std::vector<uint8_t> binary_with_nulls = {0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x00, 0x57, 0x6F, 0x72, 0x6C, 0x64};
    UACPMessage binary_msg = protocol.createTell(binary_with_nulls, "binary/test");
    g_test.assertEqual(binary_with_nulls.size(), binary_msg.getPayload().size());
    g_test.assertEqual(binary_with_nulls, binary_msg.getPayload());
    
    g_test.pass();
}

void testProtocolCompatibility() {
    g_test.startTest("Protocol Compatibility and Interoperability");
    
    UACPProtocol protocol;
    
    // Test that messages created by one protocol instance can be read by another
    UACPProtocol protocol1;
    UACPProtocol protocol2;
    
    auto msg1 = protocol1.createTell("Compatibility test", "test/compat");
    auto packed = msg1.pack();
    auto unpacked = UACPMessage::unpack(packed);
    
    g_test.assertEqual(msg1.getPayloadAsString(), unpacked.getPayloadAsString());
    g_test.assertEqual(msg1.getTopicPath(), unpacked.getTopicPath());
    g_test.assertEqual(msg1.getHeader().getVerb(), unpacked.getHeader().getVerb());
    
    // Test cross-version compatibility (same version for now)
    auto msg2 = protocol2.createAsk("Cross protocol test", "test/cross");
    auto packed2 = msg2.pack();
    auto unpacked2 = UACPMessage::unpack(packed2);
    
    g_test.assertEqual(msg2.getPayloadAsString(), unpacked2.getPayloadAsString());
    
    g_test.pass();
}

void testStressTest() {
    g_test.startTest("Stress Test with Large Data");
    
    UACPProtocol protocol;
    
    // Test with large payloads (but within message size limits)
    size_t safe_payload_size = Constants::MAX_MESSAGE_SIZE - 100; // Leave room for header and options
    std::string large_payload(safe_payload_size, 'A');
    auto large_msg = protocol.createTell(large_payload, "stress/large");
    
    g_test.assertEqual(safe_payload_size, large_msg.getPayload().size());
    g_test.assertTrue(large_msg.isValid());
    
    // Test packing/unpacking large message
    auto packed = large_msg.pack();
    auto unpacked = UACPMessage::unpack(packed);
    
    g_test.assertEqual(large_msg.getPayload().size(), unpacked.getPayload().size());
    g_test.assertEqual(large_msg.getPayloadAsString(), unpacked.getPayloadAsString());
    
    // Test with many options (using different option types)
    UACPMessage many_options_msg = protocol.createTell("Many options test", "stress/options");
    
    // Add all available option types
    many_options_msg.addOption(UACPOptionType::CONVERSATION_ID, "conv_123");
    many_options_msg.addOption(UACPOptionType::CORRELATION_ID, 12345u);
    many_options_msg.addOption(UACPOptionType::TOPIC_PATH, "stress/options");
    many_options_msg.addOption(UACPOptionType::CONTENT_TYPE, static_cast<uint32_t>(UACPContentType::JSON));
    many_options_msg.addOption(UACPOptionType::ETAG, "etag_123");
    many_options_msg.addOption(UACPOptionType::MAX_AGE, 3600u);
    many_options_msg.addOption(UACPOptionType::BLOCK, std::vector<uint8_t>{1, 2, 3, 4});
    many_options_msg.addOption(UACPOptionType::AUTH, "auth_token");
    many_options_msg.addOption(UACPOptionType::PRIORITY, 5u);
    
    g_test.assertEqual(static_cast<size_t>(9), many_options_msg.getOptions().size());
    g_test.assertTrue(many_options_msg.isValid());
    
    auto packed_options = many_options_msg.pack();
    auto unpacked_options = UACPMessage::unpack(packed_options);
    
    g_test.assertEqual(many_options_msg.getOptions().size(), unpacked_options.getOptions().size());
    
    g_test.pass();
}

void testRealWorldScenarios() {
    g_test.startTest("Real-World Usage Scenarios");
    
    UACPProtocol protocol;
    
    // Scenario 1: IoT Sensor Data
    auto sensor_data = protocol.createTell("{\"temperature\": 25.5, \"humidity\": 60.2}", "sensors/room1");
    sensor_data.setContentType(UACPContentType::JSON);
    sensor_data.addOption(UACPOptionType::MAX_AGE, 300u); // 5 minutes
    sensor_data.addOption(UACPOptionType::PRIORITY, 3u);
    
    g_test.assertEqual("sensors/room1", sensor_data.getTopicPath());
    g_test.assertEqual(UACPContentType::JSON, sensor_data.getContentType());
    g_test.assertTrue(sensor_data.isValid());
    
    // Scenario 2: Service Discovery
    auto discovery_request = protocol.createAsk("{\"service\": \"database\", \"version\": \"1.0\"}", "discovery/find");
    discovery_request.setContentType(UACPContentType::JSON);
    discovery_request.addOption(UACPOptionType::CONVERSATION_ID, "discovery_session_123");
    
    auto discovery_response = discovery_request.createResponse(StatusCode::SUCCESS, 
        "{\"host\": \"192.168.1.100\", \"port\": 5432, \"status\": \"available\"}");
    discovery_response.setContentType(UACPContentType::JSON);
    
    g_test.assertTrue(discovery_request.isRequest());
    g_test.assertTrue(discovery_response.isResponse());
    g_test.assertEqual(StatusCode::SUCCESS, static_cast<StatusCode>(discovery_response.getHeader().getCode()));
    
    // Scenario 3: Event Subscription
    auto subscription = protocol.createObserve("{\"events\": [\"user_login\", \"file_upload\"]}", "events/user");
    subscription.setContentType(UACPContentType::JSON);
    subscription.addOption(UACPOptionType::CONVERSATION_ID, "subscription_456");
    subscription.addOption(UACPOptionType::MAX_AGE, 3600u); // 1 hour
    
    g_test.assertEqual("events/user", subscription.getTopicPath());
    g_test.assertEqual(UACPVerb::OBSERVE, subscription.getHeader().getVerb());
    
    // Scenario 4: Health Check
    auto health_check = protocol.createPing();
    health_check.addOption(UACPOptionType::CONVERSATION_ID, "health_check_789");
    
    auto health_response = health_check.createResponse(StatusCode::SUCCESS, "{\"status\": \"healthy\", \"uptime\": 3600}");
    health_response.setContentType(UACPContentType::JSON);
    
    g_test.assertEqual(UACPVerb::PING, health_check.getHeader().getVerb());
    g_test.assertEqual(StatusCode::SUCCESS, static_cast<StatusCode>(health_response.getHeader().getCode()));
    
    g_test.pass();
}

void testMessageSerialization() {
    g_test.startTest("Message Serialization Round-trip");
    
    UACPProtocol protocol;
    
    // Test all message types with various configurations
    std::vector<UACPMessage> test_messages;
    
    // PING messages
    test_messages.push_back(protocol.createPing());
    test_messages.push_back(protocol.createPing(12345));
    
    // TELL messages
    test_messages.push_back(protocol.createTell("Simple message"));
    test_messages.push_back(protocol.createTell("Message with topic", "test/topic"));
    test_messages.push_back(protocol.createTell("Message with QoS", "test/qos", 0, 2));
    
    // ASK messages
    test_messages.push_back(protocol.createAsk("Simple request"));
    test_messages.push_back(protocol.createAsk("Request with topic", "test/request"));
    test_messages.push_back(protocol.createAsk("Request with QoS", "test/request", 0, 1));
    
    // OBSERVE messages
    test_messages.push_back(protocol.createObserve("Simple subscription", "test/subscribe"));
    test_messages.push_back(protocol.createObserve("Subscription with QoS", "test/subscribe", 0, 2));
    
    // Test serialization round-trip for all messages
    for (const auto& original : test_messages) {
        // Add some options to make it more complex
        UACPMessage msg_with_options = original;
        msg_with_options.addOption(UACPOptionType::PRIORITY, 5u);
        msg_with_options.addOption(UACPOptionType::MAX_AGE, 3600u);
        msg_with_options.setContentType(UACPContentType::JSON);
        
        // Pack and unpack
        auto packed = msg_with_options.pack();
        auto unpacked = UACPMessage::unpack(packed);
        
        // Verify all properties are preserved
        g_test.assertEqual(msg_with_options.getHeader().getVerb(), unpacked.getHeader().getVerb());
        g_test.assertEqual(msg_with_options.getHeader().getMessageId(), unpacked.getHeader().getMessageId());
        g_test.assertEqual(msg_with_options.getHeader().getQoS(), unpacked.getHeader().getQoS());
        g_test.assertEqual(msg_with_options.getHeader().getCode(), unpacked.getHeader().getCode());
        g_test.assertEqual(msg_with_options.getHeader().getOptionsCount(), unpacked.getHeader().getOptionsCount());
        g_test.assertEqual(msg_with_options.getPayloadAsString(), unpacked.getPayloadAsString());
        g_test.assertEqual(msg_with_options.getTopicPath(), unpacked.getTopicPath());
        g_test.assertEqual(msg_with_options.getContentType(), unpacked.getContentType());
        g_test.assertEqual(msg_with_options.getOptions().size(), unpacked.getOptions().size());
        
        // Verify options are preserved
        const auto* priority_opt = unpacked.getOption(UACPOptionType::PRIORITY);
        g_test.assertTrue(priority_opt != nullptr);
        g_test.assertEqual(5u, priority_opt->getIntValue());
        
        const auto* max_age_opt = unpacked.getOption(UACPOptionType::MAX_AGE);
        g_test.assertTrue(max_age_opt != nullptr);
        g_test.assertEqual(3600u, max_age_opt->getIntValue());
    }
    
    g_test.pass();
}

void testProtocolRobustness() {
    g_test.startTest("Protocol Robustness and Error Recovery");
    
    UACPProtocol protocol;
    
    // Test with malformed data
    std::vector<std::vector<uint8_t>> malformed_data = {
        {}, // Empty
        {0x00}, // Too short
        {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}, // Almost header size
        {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}, // All 1s
        {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}, // All 0s
    };
    
    for (const auto& data : malformed_data) {
        try {
            if (data.size() >= 8) {
                UACPHeader::unpack(data);
            } else {
                UACPHeader::unpack(data);
                g_test.fail("Should have thrown exception for malformed data");
            }
        } catch (const std::runtime_error&) {
            // Expected for malformed data
        }
    }
    
    // Test with valid but edge-case data
    UACPHeader edge_header(1, UACPVerb::PING, 0, 0, 1, 0);
    auto edge_packed = edge_header.pack();
    auto edge_unpacked = UACPHeader::unpack(edge_packed);
    g_test.assertEqual(edge_header.getVersion(), edge_unpacked.getVersion());
    
    // Test message with maximum values
    UACPHeader max_header(1, UACPVerb::OBSERVE, 2, 0x84, Constants::MAX_MESSAGE_ID, 255);
    auto max_packed = max_header.pack();
    auto max_unpacked = UACPHeader::unpack(max_packed);
    g_test.assertEqual(max_header.getVersion(), max_unpacked.getVersion());
    g_test.assertEqual(max_header.getVerb(), max_unpacked.getVerb());
    g_test.assertEqual(max_header.getQoS(), max_unpacked.getQoS());
    g_test.assertEqual(max_header.getCode(), max_unpacked.getCode());
    g_test.assertEqual(max_header.getMessageId(), max_unpacked.getMessageId());
    g_test.assertEqual(max_header.getOptionsCount(), max_unpacked.getOptionsCount());
    
    g_test.pass();
}

void testOptionRobustness() {
    g_test.startTest("Option Robustness and Edge Cases");
    
    // Test option with maximum value length
    std::string max_value(255, 'X');
    UACPOption max_opt(UACPOptionType::TOPIC_PATH, max_value);
    auto max_packed = max_opt.pack();
    UACPOption max_unpacked;
    size_t consumed = UACPOption::unpack(max_packed, 0, max_unpacked);
    g_test.assertEqual(max_packed.size(), consumed);
    g_test.assertEqual(max_value, max_unpacked.getStringValue());
    
    // Test option with empty value
    UACPOption empty_opt(UACPOptionType::TOPIC_PATH, "");
    auto empty_packed = empty_opt.pack();
    UACPOption empty_unpacked;
    consumed = UACPOption::unpack(empty_packed, 0, empty_unpacked);
    g_test.assertEqual(empty_packed.size(), consumed);
    g_test.assertEqual("", empty_unpacked.getStringValue());
    
    // Test option with special characters
    std::string special_value = "test/topic/with/special/chars/!@#$%^&*()";
    UACPOption special_opt(UACPOptionType::TOPIC_PATH, special_value);
    auto special_packed = special_opt.pack();
    UACPOption special_unpacked;
    consumed = UACPOption::unpack(special_packed, 0, special_unpacked);
    g_test.assertEqual(special_packed.size(), consumed);
    g_test.assertEqual(special_value, special_unpacked.getStringValue());
    
    // Test integer option with edge values
    UACPOption min_int_opt(UACPOptionType::PRIORITY, 0);
    UACPOption max_int_opt(UACPOptionType::PRIORITY, 0xFFFFFFFF);
    
    auto min_int_packed = min_int_opt.pack();
    auto max_int_packed = max_int_opt.pack();
    
    UACPOption min_int_unpacked, max_int_unpacked;
    UACPOption::unpack(min_int_packed, 0, min_int_unpacked);
    UACPOption::unpack(max_int_packed, 0, max_int_unpacked);
    
    g_test.assertEqual(0u, min_int_unpacked.getIntValue());
    g_test.assertEqual(0xFFFFFFFF, max_int_unpacked.getIntValue());
    
    g_test.pass();
}

void testMessageRobustness() {
    g_test.startTest("Message Robustness and Complex Scenarios");
    
    UACPProtocol protocol;
    
    // Test message with all possible option types
    UACPMessage complex_msg = protocol.createTell("Complex message", "test/complex");
    
    // Add all option types
    complex_msg.addOption(UACPOptionType::CONVERSATION_ID, "conv_12345");
    complex_msg.addOption(UACPOptionType::CORRELATION_ID, 67890u);
    complex_msg.addOption(UACPOptionType::TOPIC_PATH, "test/complex/path");
    complex_msg.addOption(UACPOptionType::CONTENT_TYPE, static_cast<uint32_t>(UACPContentType::JSON));
    complex_msg.addOption(UACPOptionType::ETAG, "etag_abcdef");
    complex_msg.addOption(UACPOptionType::MAX_AGE, 7200u);
    complex_msg.addOption(UACPOptionType::BLOCK, std::vector<uint8_t>{1, 2, 3, 4, 5});
    complex_msg.addOption(UACPOptionType::AUTH, "auth_token_xyz");
    complex_msg.addOption(UACPOptionType::PRIORITY, 7u);
    
    g_test.assertEqual(static_cast<size_t>(9), complex_msg.getOptions().size());
    g_test.assertTrue(complex_msg.isValid());
    
    // Test serialization of complex message
    auto packed = complex_msg.pack();
    auto unpacked = UACPMessage::unpack(packed);
    
    g_test.assertEqual(complex_msg.getOptions().size(), unpacked.getOptions().size());
    g_test.assertEqual(complex_msg.getPayloadAsString(), unpacked.getPayloadAsString());
    g_test.assertEqual(complex_msg.getTopicPath(), unpacked.getTopicPath());
    
    // Verify all options are preserved
    for (const auto& option : complex_msg.getOptions()) {
        const auto* unpacked_option = unpacked.getOption(option.getType());
        g_test.assertTrue(unpacked_option != nullptr);
        
        if (option.isStringValue()) {
            g_test.assertEqual(option.getStringValue(), unpacked_option->getStringValue());
        } else if (option.isIntValue()) {
            g_test.assertEqual(option.getIntValue(), unpacked_option->getIntValue());
        } else {
            g_test.assertEqual(option.getBytesValue().size(), unpacked_option->getBytesValue().size());
        }
    }
    
    // Test message with binary payload containing various byte values
    std::vector<uint8_t> binary_payload;
    for (int i = 0; i < 256; ++i) {
        binary_payload.push_back(static_cast<uint8_t>(i));
    }
    
    UACPMessage binary_msg = protocol.createTell(binary_payload, "test/binary");
    auto binary_packed = binary_msg.pack();
    auto binary_unpacked = UACPMessage::unpack(binary_packed);
    
    g_test.assertEqual(binary_payload.size(), binary_unpacked.getPayload().size());
    g_test.assertEqual(binary_payload, binary_unpacked.getPayload());
    
    g_test.pass();
}

void testPerformanceBenchmarks() {
    g_test.startTest("Performance Benchmarks");
    
    UACPProtocol protocol;
    
    // Benchmark message creation
    auto start = std::chrono::high_resolution_clock::now();
    const int num_creations = 100000;
    
    for (int i = 0; i < num_creations; ++i) {
        auto msg = protocol.createTell("Benchmark message " + std::to_string(i), "benchmark/test");
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto creation_time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << " (" << num_creations << " creations in " << creation_time.count() << "ms)";
    
    // Benchmark packing
    start = std::chrono::high_resolution_clock::now();
    std::vector<std::vector<uint8_t>> packed_messages;
    
    for (int i = 0; i < num_creations; ++i) {
        auto msg = protocol.createTell("Packing benchmark " + std::to_string(i), "benchmark/pack");
        packed_messages.push_back(msg.pack());
    }
    
    end = std::chrono::high_resolution_clock::now();
    auto packing_time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << " (" << num_creations << " packings in " << packing_time.count() << "ms)";
    
    std::cout << " (" << num_creations << " packings in " << packing_time.count() << "ms)";
    
    // Benchmark unpacking
    start = std::chrono::high_resolution_clock::now();
    
    for (const auto& packed : packed_messages) {
        auto unpacked = UACPMessage::unpack(packed);
        (void)unpacked; // Suppress unused variable warning
    }
    
    end = std::chrono::high_resolution_clock::now();
    auto unpacking_time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << " (" << num_creations << " unpackings in " << unpacking_time.count() << "ms)";
    
    // Performance should be reasonable
    g_test.assertTrue(creation_time.count() < 5000, "Message creation should be fast");
    g_test.assertTrue(packing_time.count() < 5000, "Message packing should be fast");
    g_test.assertTrue(unpacking_time.count() < 5000, "Message unpacking should be fast");
    
    g_test.pass();
}

void testMemoryEfficiency() {
    g_test.startTest("Memory Efficiency and Resource Management");
    
    UACPProtocol protocol;
    
    // Test memory usage with many objects
    std::vector<UACPMessage> messages;
    messages.reserve(1000);
    
    for (int i = 0; i < 1000; ++i) {
        auto msg = protocol.createTell("Memory efficiency test " + std::to_string(i), "test/memory");
        msg.addOption(UACPOptionType::PRIORITY, static_cast<uint32_t>(i % 8));
        msg.addOption(UACPOptionType::MAX_AGE, static_cast<uint32_t>(i * 10));
        messages.push_back(std::move(msg));
    }
    
    // Test that all messages are valid
    for (const auto& msg : messages) {
        g_test.assertTrue(msg.isValid());
    }
    
    // Test serialization of all messages
    std::vector<std::vector<uint8_t>> packed_messages;
    packed_messages.reserve(messages.size());
    
    for (const auto& msg : messages) {
        packed_messages.push_back(msg.pack());
    }
    
    // Test deserialization
    for (size_t i = 0; i < packed_messages.size(); ++i) {
        auto unpacked = UACPMessage::unpack(packed_messages[i]);
        g_test.assertEqual(messages[i].getPayloadAsString(), unpacked.getPayloadAsString());
    }
    
    g_test.pass();
}

void testThreadSafety() {
    g_test.startTest("Thread Safety and Concurrent Access");
    
    UACPProtocol protocol;
    std::vector<std::thread> threads;
    std::atomic<int> success_count{0};
    std::atomic<int> error_count{0};
    const int num_threads = 20;
    const int operations_per_thread = 100;
    
    // Test concurrent message creation and processing
    for (int t = 0; t < num_threads; ++t) {
        threads.emplace_back([&protocol, &success_count, &error_count, t, operations_per_thread]() {
            for (int i = 0; i < operations_per_thread; ++i) {
                try {
                    // Create message
                    auto msg = protocol.createTell("Thread " + std::to_string(t) + " operation " + std::to_string(i), 
                                                  "test/concurrent");
                    
                    // Add options
                    msg.addOption(UACPOptionType::PRIORITY, static_cast<uint32_t>(i % 8));
                    msg.addOption(UACPOptionType::MAX_AGE, static_cast<uint32_t>(i * 10));
                    
                    // Pack and unpack
                    auto packed = msg.pack();
                    auto unpacked = UACPMessage::unpack(packed);
                    
                    // Verify
                    if (unpacked.getPayloadAsString().find("Thread " + std::to_string(t)) != std::string::npos) {
                        success_count++;
                    }
                } catch (...) {
                    error_count++;
                }
            }
        });
    }
    
    // Wait for all threads to complete
    for (auto& thread : threads) {
        thread.join();
    }
    
    // All operations should succeed
    g_test.assertEqual(num_threads * operations_per_thread, success_count.load());
    g_test.assertEqual(0, error_count.load());
    
    g_test.pass();
}

void testErrorRecovery() {
    g_test.startTest("Error Recovery and Exception Handling");
    
    UACPProtocol protocol;
    
    // Test recovery from various error conditions
    try {
        // Test invalid message creation
        std::string oversized_payload(Constants::MAX_PAYLOAD_SIZE + 1, 'X');
        std::vector<uint8_t> oversized_payload_vec(oversized_payload.begin(), oversized_payload.end());
        UACPMessage oversized_msg(UACPVerb::TELL, oversized_payload_vec, 1, 0, 0);
        g_test.assertFalse(oversized_msg.isValid());
    } catch (...) {
        // Expected for oversized payload
    }
    
    // Test recovery from malformed data
    std::vector<std::vector<uint8_t>> test_cases = {
        {}, // Empty data
        {0x00}, // Single byte
        {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}, // Almost header
        {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}, // All 1s
    };
    
    for (const auto& test_data : test_cases) {
        try {
            if (test_data.size() >= 8) {
                UACPHeader::unpack(test_data);
            } else {
                UACPHeader::unpack(test_data);
                g_test.fail("Should have thrown exception for invalid data");
            }
        } catch (const std::runtime_error&) {
            // Expected - test that we can continue after error
            auto recovery_msg = protocol.createPing();
            g_test.assertTrue(recovery_msg.isValid());
        }
    }
    
    g_test.pass();
}

void testProtocolCompleteness() {
    g_test.startTest("Protocol Completeness and Feature Coverage");
    
    UACPProtocol protocol;
    
    // Test all verb types
    auto ping_msg = protocol.createPing();
    g_test.assertEqual(UACPVerb::PING, ping_msg.getHeader().getVerb());
    
    auto tell_msg = protocol.createTell("Test message", "test/topic");
    g_test.assertEqual(UACPVerb::TELL, tell_msg.getHeader().getVerb());
    
    auto ask_msg = protocol.createAsk("Test request", "test/request");
    g_test.assertEqual(UACPVerb::ASK, ask_msg.getHeader().getVerb());
    
    auto observe_msg = protocol.createObserve("Test subscription", "test/subscribe");
    g_test.assertEqual(UACPVerb::OBSERVE, observe_msg.getHeader().getVerb());
    
    // Test all QoS levels
    for (int qos = 0; qos <= 2; ++qos) {
        auto qos_msg = protocol.createTell("QoS test", "test/qos", 0, qos);
        g_test.assertEqual(qos, qos_msg.getHeader().getQoS());
        g_test.assertTrue(qos_msg.isValid());
    }
    
    // Test all content types
    std::vector<UACPContentType> content_types = {
        UACPContentType::CBOR,
        UACPContentType::JSON,
        UACPContentType::PROTOBUF,
        UACPContentType::TEXT
    };
    
    for (auto content_type : content_types) {
        auto msg = protocol.createTell("Content type test", "test/content");
        msg.setContentType(content_type);
        g_test.assertEqual(content_type, msg.getContentType());
    }
    
    // Test all status codes
    std::vector<StatusCode> status_codes = {
        StatusCode::SUCCESS,
        StatusCode::BAD_REQUEST,
        StatusCode::UNAUTHORIZED,
        StatusCode::FORBIDDEN,
        StatusCode::NOT_FOUND,
        StatusCode::INTERNAL_ERROR
    };
    
    for (auto status_code : status_codes) {
        auto request = protocol.createAsk("Test request", "test/status");
        auto response = request.createResponse(status_code, "Response");
        g_test.assertEqual(static_cast<uint8_t>(status_code), response.getHeader().getCode());
    }
    
    g_test.pass();
}

void testIntegrationScenarios() {
    g_test.startTest("Integration Scenarios and Workflows");
    
    UACPProtocol protocol;
    
    // Scenario 1: Complete request-response cycle
    auto request = protocol.createAsk("Get user data for ID 123", "users/get");
    request.setContentType(UACPContentType::JSON);
    request.addOption(UACPOptionType::CONVERSATION_ID, "user_lookup_123");
    request.addOption(UACPOptionType::PRIORITY, 5u);
    
    auto response = request.createResponse(StatusCode::SUCCESS, 
        "{\"id\": 123, \"name\": \"John Doe\", \"email\": \"john@example.com\"}");
    response.setContentType(UACPContentType::JSON);
    
    g_test.assertTrue(request.isRequest());
    g_test.assertTrue(response.isResponse());
    g_test.assertEqual(request.getHeader().getMessageId(), response.getHeader().getMessageId());
    
    // Scenario 2: Event publishing and subscription
    auto event_publisher = protocol.createTell("{\"event\": \"user_login\", \"user_id\": 123, \"timestamp\": 1234567890}", 
                                              "events/user_activity");
    event_publisher.setContentType(UACPContentType::JSON);
    event_publisher.addOption(UACPOptionType::MAX_AGE, 3600u);
    
    auto event_subscriber = protocol.createObserve("{\"subscribe_to\": [\"user_login\", \"user_logout\"]}", 
                                                  "events/user_activity");
    event_subscriber.setContentType(UACPContentType::JSON);
    event_subscriber.addOption(UACPOptionType::CONVERSATION_ID, "event_subscription_456");
    
    g_test.assertEqual("events/user_activity", event_publisher.getTopicPath());
    g_test.assertEqual("events/user_activity", event_subscriber.getTopicPath());
    
    // Scenario 3: Health monitoring
    auto health_check = protocol.createPing();
    health_check.addOption(UACPOptionType::CONVERSATION_ID, "health_check_789");
    
    auto health_response = health_check.createResponse(StatusCode::SUCCESS, 
        "{\"status\": \"healthy\", \"services\": [\"database\", \"cache\", \"api\"], \"uptime\": 86400}");
    health_response.setContentType(UACPContentType::JSON);
    
    g_test.assertEqual(UACPVerb::PING, health_check.getHeader().getVerb());
    g_test.assertEqual(StatusCode::SUCCESS, static_cast<StatusCode>(health_response.getHeader().getCode()));
    
    // Scenario 4: File transfer simulation
    std::string file_data(1000, 'F'); // Simulate file content
    auto file_transfer = protocol.createTell(file_data, "files/upload/document.pdf");
    file_transfer.setContentType(UACPContentType::TEXT);
    file_transfer.addOption(UACPOptionType::CONVERSATION_ID, "file_transfer_101");
    file_transfer.addOption(UACPOptionType::PRIORITY, 7u);
    
    g_test.assertEqual(static_cast<size_t>(1000), file_transfer.getPayload().size());
    g_test.assertEqual("files/upload/document.pdf", file_transfer.getTopicPath());
    
    g_test.pass();
}

void testAdvancedFeatures() {
    g_test.startTest("Advanced Features and Complex Operations");
    
    UACPProtocol protocol;
    
    // Test message with maximum complexity
    UACPMessage complex_msg = protocol.createTell("Complex advanced message", "advanced/complex");
    
    // Add all possible options
    complex_msg.addOption(UACPOptionType::CONVERSATION_ID, "advanced_conv_12345");
    complex_msg.addOption(UACPOptionType::CORRELATION_ID, 98765u);
    complex_msg.addOption(UACPOptionType::TOPIC_PATH, "advanced/complex/nested/path");
    complex_msg.addOption(UACPOptionType::CONTENT_TYPE, static_cast<uint32_t>(UACPContentType::JSON));
    complex_msg.addOption(UACPOptionType::ETAG, "advanced_etag_abcdef123456");
    complex_msg.addOption(UACPOptionType::MAX_AGE, 7200u);
    complex_msg.addOption(UACPOptionType::BLOCK, std::vector<uint8_t>{0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08});
    complex_msg.addOption(UACPOptionType::AUTH, "advanced_auth_token_xyz789");
    complex_msg.addOption(UACPOptionType::PRIORITY, 7u);
    
    // Set content type
    complex_msg.setContentType(UACPContentType::JSON);
    
    g_test.assertEqual(static_cast<size_t>(9), complex_msg.getOptions().size());
    g_test.assertTrue(complex_msg.isValid());
    
    // Test serialization round-trip
    auto packed = complex_msg.pack();
    auto unpacked = UACPMessage::unpack(packed);
    
    g_test.assertEqual(complex_msg.getOptions().size(), unpacked.getOptions().size());
    g_test.assertEqual(complex_msg.getPayloadAsString(), unpacked.getPayloadAsString());
    g_test.assertEqual(complex_msg.getTopicPath(), unpacked.getTopicPath());
    g_test.assertEqual(complex_msg.getContentType(), unpacked.getContentType());
    
    // Test message chaining (request -> response -> follow-up)
    auto initial_request = protocol.createAsk("Initial request", "chain/start");
    initial_request.addOption(UACPOptionType::CONVERSATION_ID, "chain_123");
    
    auto response = initial_request.createResponse(StatusCode::SUCCESS, "Initial response");
    response.addOption(UACPOptionType::CONVERSATION_ID, "chain_123");
    
    auto follow_up = protocol.createAsk("Follow-up request", "chain/continue");
    follow_up.addOption(UACPOptionType::CONVERSATION_ID, "chain_123");
    follow_up.addOption(UACPOptionType::CORRELATION_ID, response.getHeader().getMessageId());
    
    g_test.assertEqual("chain_123", initial_request.getOption(UACPOptionType::CONVERSATION_ID)->getStringValue());
    g_test.assertEqual("chain_123", response.getOption(UACPOptionType::CONVERSATION_ID)->getStringValue());
    g_test.assertEqual("chain_123", follow_up.getOption(UACPOptionType::CONVERSATION_ID)->getStringValue());
    
    g_test.pass();
}

void testBoundaryConditions() {
    g_test.startTest("Boundary Conditions and Limits");
    
    UACPProtocol protocol;
    
    // Test message ID boundaries
    auto min_id_msg = protocol.createPing(1);
    g_test.assertEqual(1u, min_id_msg.getHeader().getMessageId());
    
    auto max_id_msg = protocol.createPing(Constants::MAX_MESSAGE_ID);
    g_test.assertEqual(Constants::MAX_MESSAGE_ID, max_id_msg.getHeader().getMessageId());
    
    // Test QoS boundaries
    for (int qos = 0; qos <= 2; ++qos) {
        auto qos_msg = protocol.createTell("QoS boundary test", "test/qos", 1, qos);
        g_test.assertEqual(qos, qos_msg.getHeader().getQoS());
        g_test.assertTrue(qos_msg.isValid());
    }
    
    // Test payload size boundaries
    std::string min_payload = "";
    auto min_payload_msg = protocol.createTell(min_payload, "test/min");
    g_test.assertEqual(static_cast<size_t>(0), min_payload_msg.getPayload().size());
    g_test.assertTrue(min_payload_msg.isValid());
    
    size_t safe_payload_size = Constants::MAX_MESSAGE_SIZE - 100; // Leave room for header and options
    std::string max_payload(safe_payload_size, 'X');
    auto max_payload_msg = protocol.createTell(max_payload, "test/max");
    g_test.assertEqual(safe_payload_size, max_payload_msg.getPayload().size());
    g_test.assertTrue(max_payload_msg.isValid());
    
    // Test option count boundaries
    UACPMessage max_options_msg = protocol.createTell("Max options test", "test/options");
    max_options_msg.addOption(UACPOptionType::CONVERSATION_ID, "conv1");
    max_options_msg.addOption(UACPOptionType::CORRELATION_ID, 12345u);
    max_options_msg.addOption(UACPOptionType::TOPIC_PATH, "test/topic");
    max_options_msg.addOption(UACPOptionType::CONTENT_TYPE, static_cast<uint32_t>(UACPContentType::JSON));
    max_options_msg.addOption(UACPOptionType::ETAG, "etag1");
    max_options_msg.addOption(UACPOptionType::MAX_AGE, 3600u);
    max_options_msg.addOption(UACPOptionType::BLOCK, std::vector<uint8_t>{1, 2, 3, 4});
    max_options_msg.addOption(UACPOptionType::AUTH, "auth1");
    max_options_msg.addOption(UACPOptionType::PRIORITY, 5u);
    g_test.assertEqual(static_cast<size_t>(9), max_options_msg.getOptions().size());
    g_test.assertTrue(max_options_msg.isValid());
    
    // Test topic length boundaries
    std::cout << "Debug: Testing topic length boundaries" << std::endl;
    std::string max_topic(Constants::MAX_TOPIC_LENGTH, 'a');
    auto max_topic_msg = protocol.createTell("Max topic test", max_topic);
    g_test.assertEqual(Constants::MAX_TOPIC_LENGTH, max_topic_msg.getTopicPath().size());
    g_test.assertTrue(max_topic_msg.isValid());
    
    std::cout << "Debug: All boundary conditions tests passed" << std::endl;
    g_test.pass();
}

void testRegressionTests() {
    g_test.startTest("Regression Tests and Bug Prevention");
    
    UACPProtocol protocol;
    
    // Test for potential memory leaks
    for (int i = 0; i < 1000; ++i) {
        auto msg = protocol.createTell("Regression test " + std::to_string(i), "regression/test");
        msg.addOption(UACPOptionType::PRIORITY, static_cast<uint32_t>(i % 8));
        
        auto packed = msg.pack();
        auto unpacked = UACPMessage::unpack(packed);
        
        // Test copy and move operations
        UACPMessage copied = unpacked;
        UACPMessage moved = std::move(copied);
        UACPMessage assigned;
        assigned = moved;
        
        (void)assigned; // Suppress unused variable warning
    }
    
    // Test for potential integer overflow
    UACPMessage overflow_test = protocol.createTell("Overflow test", "test/overflow");
    overflow_test.addOption(UACPOptionType::PRIORITY, 0xFFFFFFFF);
    overflow_test.addOption(UACPOptionType::MAX_AGE, 0xFFFFFFFF);
    
    auto packed = overflow_test.pack();
    auto unpacked = UACPMessage::unpack(packed);
    
    g_test.assertEqual(0xFFFFFFFF, unpacked.getOption(UACPOptionType::PRIORITY)->getIntValue());
    g_test.assertEqual(0xFFFFFFFF, unpacked.getOption(UACPOptionType::MAX_AGE)->getIntValue());
    
    g_test.pass();
}

void testCompatibilityTests() {
    g_test.startTest("Compatibility and Interoperability Tests");
    
    UACPProtocol protocol;
    
    // Test that different protocol instances produce compatible messages
    UACPProtocol protocol1;
    UACPProtocol protocol2;
    
    auto msg1 = protocol1.createTell("Compatibility test", "test/compat");
    auto msg2 = protocol2.createTell("Compatibility test", "test/compat");
    
    // Both should be valid
    g_test.assertTrue(msg1.isValid());
    g_test.assertTrue(msg2.isValid());
    
    // Both should have same structure
    g_test.assertEqual(msg1.getHeader().getVerb(), msg2.getHeader().getVerb());
    g_test.assertEqual(msg1.getPayloadAsString(), msg2.getPayloadAsString());
    g_test.assertEqual(msg1.getTopicPath(), msg2.getTopicPath());
    
    // Test cross-instance serialization
    auto packed1 = msg1.pack();
    auto unpacked1 = UACPMessage::unpack(packed1);
    
    auto packed2 = msg2.pack();
    auto unpacked2 = UACPMessage::unpack(packed2);
    
    g_test.assertEqual(unpacked1.getPayloadAsString(), unpacked2.getPayloadAsString());
    
    g_test.pass();
}

void testSecurityTests() {
    g_test.startTest("Security and Input Validation Tests");
    
    UACPProtocol protocol;
    
    // Test with potentially malicious input
    std::vector<std::string> malicious_inputs = {
        "", // Empty string
        std::string(10000, '\0'), // Null bytes
        std::string(10000, '\xFF'), // High bytes
        "test\x00\x01\x02\x03", // Mixed null bytes
        "test\xFF\xFE\xFD\xFC", // High byte values
        std::string(1000, 'A') + std::string(1000, '\0') + std::string(1000, 'B'), // Mixed content
    };
    
    for (const auto& input : malicious_inputs) {
        try {
            auto msg = protocol.createTell(input, "security/test");
            g_test.assertTrue(msg.isValid());
            
            auto packed = msg.pack();
            auto unpacked = UACPMessage::unpack(packed);
            
            // Should handle gracefully
            g_test.assertTrue(unpacked.isValid());
        } catch (...) {
            // Some inputs might cause exceptions, which is acceptable
        }
    }
    
    // Test with very large inputs
    try {
        std::string huge_input(Constants::MAX_PAYLOAD_SIZE + 1000, 'X');
        std::vector<uint8_t> huge_payload(huge_input.begin(), huge_input.end());
        UACPMessage huge_msg(UACPVerb::TELL, huge_payload, 1, 0, 0);
        g_test.assertFalse(huge_msg.isValid()); // Should be invalid
    } catch (...) {
        // Expected for oversized input
    }
    
    g_test.pass();
}

void testDocumentationTests() {
    g_test.startTest("Documentation and Example Validation");
    
    UACPProtocol protocol;
    
    // Test examples from documentation
    auto ping_msg = protocol.createPing();
    g_test.assertEqual(UACPVerb::PING, ping_msg.getHeader().getVerb());
    g_test.assertEqual(static_cast<size_t>(0), ping_msg.getPayload().size());
    
    auto tell_msg = protocol.createTell("Hello, world!", "greetings/hello");
    g_test.assertEqual(UACPVerb::TELL, tell_msg.getHeader().getVerb());
    g_test.assertEqual("Hello, world!", tell_msg.getPayloadAsString());
    g_test.assertEqual("greetings/hello", tell_msg.getTopicPath());
    
    auto ask_msg = protocol.createAsk("What is the temperature?", "sensors/temperature");
    g_test.assertEqual(UACPVerb::ASK, ask_msg.getHeader().getVerb());
    g_test.assertEqual("What is the temperature?", ask_msg.getPayloadAsString());
    g_test.assertEqual("sensors/temperature", ask_msg.getTopicPath());
    
    auto observe_msg = protocol.createObserve("Subscribe to updates", "sensors/temperature");
    g_test.assertEqual(UACPVerb::OBSERVE, observe_msg.getHeader().getVerb());
    g_test.assertEqual("Subscribe to updates", observe_msg.getPayloadAsString());
    g_test.assertEqual("sensors/temperature", observe_msg.getTopicPath());
    
    // Test with options
    auto complex_msg = protocol.createTell("Complex message", "test/complex");
    complex_msg.addOption(UACPOptionType::PRIORITY, 5u);
    complex_msg.addOption(UACPOptionType::MAX_AGE, 3600u);
    complex_msg.setContentType(UACPContentType::JSON);
    
    g_test.assertEqual(5u, complex_msg.getOption(UACPOptionType::PRIORITY)->getIntValue());
    g_test.assertEqual(3600u, complex_msg.getOption(UACPOptionType::MAX_AGE)->getIntValue());
    g_test.assertEqual(UACPContentType::JSON, complex_msg.getContentType());
    
    g_test.pass();
}

void testFinalIntegration() {
    g_test.startTest("Final Integration and System Test");
    
    UACPProtocol protocol;
    
    // Create a comprehensive test scenario
    std::vector<UACPMessage> messages;
    
    // Create various message types
    messages.push_back(protocol.createPing());
    messages.push_back(protocol.createTell("System status: OK", "system/status"));
    messages.push_back(protocol.createAsk("Get configuration", "system/config"));
    messages.push_back(protocol.createObserve("Monitor system events", "system/events"));
    
    // Add complexity to each message
    for (auto& msg : messages) {
        msg.addOption(UACPOptionType::PRIORITY, 5u);
        msg.addOption(UACPOptionType::MAX_AGE, 3600u);
        msg.setContentType(UACPContentType::JSON);
    }
    
    // Test serialization and deserialization of all messages
    std::vector<std::vector<uint8_t>> packed_messages;
    for (const auto& msg : messages) {
        packed_messages.push_back(msg.pack());
    }
    
    // Test deserialization
    for (size_t i = 0; i < packed_messages.size(); ++i) {
        auto unpacked = UACPMessage::unpack(packed_messages[i]);
        g_test.assertEqual(messages[i].getHeader().getVerb(), unpacked.getHeader().getVerb());
        g_test.assertEqual(messages[i].getPayloadAsString(), unpacked.getPayloadAsString());
        g_test.assertEqual(messages[i].getContentType(), unpacked.getContentType());
    }
    
    // Test response creation
    auto request = protocol.createAsk("Test request", "test/request");
    auto response = request.createResponse(StatusCode::SUCCESS, "Test response");
    
    g_test.assertTrue(request.isRequest());
    g_test.assertTrue(response.isResponse());
    g_test.assertEqual(request.getHeader().getMessageId(), response.getHeader().getMessageId());
    
    g_test.pass();
}

// Main test runner
int main() {
    std::cout << "µACP C++ Library - Comprehensive Test Suite" << std::endl;
    std::cout << "===========================================" << std::endl;
    std::cout << "Library Version: " << getVersion() << std::endl;
    std::cout << "Author: " << getAuthor() << std::endl;
    std::cout << "License: " << getLicense() << std::endl;
    std::cout << std::endl;
    
    try {
        // Core functionality tests
        g_test.runTest(testVersionInfo);
        g_test.runTest(testEnums);
        g_test.runTest(testConstants);
        
        // Header tests
        g_test.runTest(testHeaderBasic);
        g_test.runTest(testHeaderPacking);
        g_test.runTest(testHeaderValidation);
        g_test.runTest(testHeaderResponse);
        
        // Option tests
        g_test.runTest(testOptionBasic);
        g_test.runTest(testOptionPacking);
        g_test.runTest(testOptionSizes);
        g_test.runTest(testOptionEdgeCases);
        g_test.runTest(testOptionRobustness);
        
        // Message tests
        g_test.runTest(testMessageBasic);
        g_test.runTest(testMessageOptions);
        g_test.runTest(testMessagePayload);
        g_test.runTest(testMessagePacking);
        g_test.runTest(testMessageValidation);
        g_test.runTest(testMessageResponse);
        g_test.runTest(testMessageHelpers);
        g_test.runTest(testMessageEdgeCases);
        g_test.runTest(testMessageRobustness);
        
        // Protocol tests
        g_test.runTest(testProtocolBasic);
        g_test.runTest(testProtocolMessageCreation);
        g_test.runTest(testProtocolMessageValidation);
        g_test.runTest(testProtocolMessageIdGeneration);
        g_test.runTest(testProtocolBinaryPayload);
        g_test.runTest(testProtocolCompatibility);
        g_test.runTest(testProtocolRobustness);
        g_test.runTest(testProtocolCompleteness);
        
        // Advanced tests
        g_test.runTest(testRandomData);
        g_test.runTest(testEdgeCases);
        g_test.runTest(testPerformance);
        g_test.runTest(testMemoryUsage);
        g_test.runTest(testConcurrency);
        g_test.runTest(testErrorHandling);
        g_test.runTest(testStressTest);
        g_test.runTest(testRealWorldScenarios);
        g_test.runTest(testMessageSerialization);
        g_test.runTest(testPerformanceBenchmarks);
        g_test.runTest(testMemoryEfficiency);
        g_test.runTest(testThreadSafety);
        g_test.runTest(testErrorRecovery);
        g_test.runTest(testIntegrationScenarios);
        g_test.runTest(testAdvancedFeatures);
        g_test.runTest(testBoundaryConditions);
        g_test.runTest(testRegressionTests);
        g_test.runTest(testCompatibilityTests);
        g_test.runTest(testSecurityTests);
        g_test.runTest(testDocumentationTests);
        g_test.runTest(testFinalIntegration);
        
    } catch (const std::exception& e) {
        std::cerr << "❌ Test suite failed with exception: " << e.what() << std::endl;
        g_test.printSummary();
        return 1;
    } catch (...) {
        std::cerr << "❌ Test suite failed with unknown exception" << std::endl;
        g_test.printSummary();
        return 1;
    }
    
    g_test.printSummary();
    
    if (g_test.allTestsPassed()) {
        std::cout << "\n🚀 µACP C++ Library is ready for production use!" << std::endl;
        return 0;
    } else {
        return 1;
    }
}