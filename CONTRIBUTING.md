# Contributing to µACP

Thank you for your interest in contributing to the µACP (Micro Agent Communication Protocol) library! This document provides guidelines and information for contributors.

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.8 or higher
- Git
- Basic knowledge of Python, networking, and agent communication protocols

### **Development Setup**
```bash
# Clone the repository
git clone https://github.com/uacp/miuacp.git
cd miuacp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## 🔧 **Development Workflow**

### **1. Fork and Clone**
1. Fork the repository on GitHub
2. Clone your fork locally
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/uacp/miuacp.git
   ```

### **2. Create a Feature Branch**
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### **3. Make Your Changes**
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### **4. Commit Your Changes**
```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add new circuit breaker implementation

- Implements configurable failure thresholds
- Adds background monitoring capabilities
- Includes comprehensive test coverage"
```

### **5. Push and Create Pull Request**
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

## 📝 **Coding Standards**

### **Python Style Guide**
We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 88 characters (Black formatter)
- **Import sorting**: Use `isort` with Black profile
- **Type hints**: Required for all public functions
- **Docstrings**: Use Google-style docstrings

### **Code Formatting**
We use automated tools to maintain code quality:

```bash
# Format code with Black
black uacp_lib/

# Sort imports with isort
isort uacp_lib/

# Check code quality with flake8
flake8 uacp_lib/

# Type checking with mypy
mypy uacp_lib/
```

### **Pre-commit Hooks**
The repository includes pre-commit hooks that automatically:
- Format code with Black
- Sort imports with isort
- Check code quality with flake8
- Run basic tests

### **Code Structure**
```
uacp_lib/
├── __init__.py          # Package initialization
├── protocol.py          # Core protocol implementation
├── client.py            # Client implementation
├── server.py            # Server implementation
├── agent.py             # Agent implementation
├── discovery.py         # Service discovery
├── routing.py           # Routing and addressing
├── subscriptions.py     # Subscription management
├── reliability.py       # Reliability and QoS
├── timers.py            # Timer and scheduling
├── broker.py            # Broker and middleware
├── instrumentation.py   # Logging and metrics
├── resources.py         # Resource management
├── circuit_breaker.py   # Circuit breaker pattern
├── adaptive_timeout.py  # Adaptive timeout management
├── resource_pool.py     # Resource pooling
├── error_recovery.py    # Error recovery mechanisms
├── health_monitoring.py # Health monitoring
├── transport/           # Transport layer implementations
├── security/            # Security implementations
├── bridges/             # Protocol bridges
└── utils/               # Utility functions
```

## 🧪 **Testing**

### **Running Tests**
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/performance/    # Performance tests

# Run with coverage
pytest --cov=uacp_lib --cov-report=html

# Run specific test file
pytest tests/test_protocol.py

# Run specific test function
pytest tests/test_protocol.py::test_message_creation
```

### **Writing Tests**
- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test component interactions
- **Performance tests**: Benchmark critical operations
- **Property-based tests**: Use hypothesis for edge cases

### **Test Structure**
```python
import pytest
from uacp_lib import UACPProtocol, UACPVerb

class TestUACPProtocol:
    """Test suite for UACPProtocol class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.protocol = UACPProtocol()
    
    def test_message_creation(self):
        """Test message creation functionality."""
        message = self.protocol.create_message(
            verb=UACPVerb.TELL,
            payload="test".encode(),
            msg_id=1
        )
        assert message.header.verb == UACPVerb.TELL
        assert message.payload == "test".encode()
    
    @pytest.mark.integration
    def test_message_roundtrip(self):
        """Test message packing and unpacking."""
        # Test implementation
        pass
```

## 📚 **Documentation**

### **Code Documentation**
- **Docstrings**: Required for all public functions and classes
- **Type hints**: Required for all public APIs
- **Inline comments**: Explain complex logic

### **API Documentation**
- Update README.md for user-facing changes
- Update CHANGELOG.md for all releases
- Add docstrings for new public APIs

### **Example Documentation**
```python
def create_message(self, 
                  verb: UACPVerb,
                  payload: Optional[bytes] = None,
                  msg_id: Optional[int] = None,
                  options: Optional[List[UACPOption]] = None) -> UACPMessage:
    """Create a new µACP message.
    
    Args:
        verb: The message verb (PING, TELL, ASK, OBSERVE)
        payload: Optional message payload
        msg_id: Optional message ID (auto-generated if not provided)
        options: Optional list of TLV options
        
    Returns:
        A new UACPMessage instance
        
    Raises:
        ValueError: If verb is invalid or payload is too large
        
    Example:
        >>> protocol = UACPProtocol()
        >>> message = protocol.create_message(
        ...     verb=UACPVerb.TELL,
        ...     payload="Hello".encode(),
        ...     options=[UACPOption(UACPOptionType.TOPIC_PATH, "test")]
        ... )
        >>> message.header.verb
        <UACPVerb.TELL: 1>
    """
```

## 🔍 **Code Review Process**

### **Pull Request Guidelines**
1. **Title**: Clear, descriptive title
2. **Description**: Detailed description of changes
3. **Tests**: All tests must pass
4. **Documentation**: Update relevant documentation
5. **Changelog**: Update CHANGELOG.md if needed

### **Review Checklist**
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (or clearly documented)
- [ ] Performance impact considered
- [ ] Security implications reviewed

### **Review Process**
1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Address feedback** and make changes
4. **Final approval** and merge

## 🐛 **Bug Reports**

### **Reporting Bugs**
When reporting bugs, please include:

1. **Environment**: Python version, OS, µACP version
2. **Steps to reproduce**: Clear, step-by-step instructions
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Error messages**: Full error traceback
6. **Code example**: Minimal code to reproduce the issue

### **Bug Report Template**
```markdown
**Bug Description**
Brief description of the bug

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- Python version: 3.9.0
- µACP version: 5.0.0
- OS: Ubuntu 20.04

**Additional Information**
Any other relevant information
```

## 💡 **Feature Requests**

### **Requesting Features**
When requesting features, please:

1. **Describe the problem** you're trying to solve
2. **Explain the solution** you'd like to see
3. **Provide use cases** and examples
4. **Consider alternatives** you've explored
5. **Assess impact** on existing functionality

### **Feature Request Template**
```markdown
**Problem Statement**
Clear description of the problem

**Proposed Solution**
Description of the proposed feature

**Use Cases**
Specific scenarios where this would be useful

**Alternatives Considered**
Other approaches you've explored

**Impact Assessment**
How this affects existing functionality
```

## 🚀 **Release Process**

### **Version Numbering**
We follow [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

### **Release Checklist**
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Release notes prepared
- [ ] PyPI package built and uploaded

## 🤝 **Community Guidelines**

### **Code of Conduct**
- Be respectful and inclusive
- Focus on technical discussions
- Help others learn and grow
- Report inappropriate behavior

### **Communication Channels**
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code contributions
- **Email**: dev@uacp.dev (for sensitive matters)

## 📞 **Getting Help**

### **Resources**
- **Documentation**: [https://miuacp.readthedocs.io/](https://miuacp.readthedocs.io/)
- **Examples**: Check the `examples/` directory
- **Tests**: Look at test files for usage examples
- **Issues**: Search existing issues for similar problems

### **Asking Questions**
When asking for help:
1. **Search first**: Check existing issues and documentation
2. **Be specific**: Provide clear, detailed information
3. **Include code**: Show what you've tried
4. **Be patient**: Maintainers are volunteers

## 🙏 **Acknowledgments**

Thank you for contributing to µACP! Your contributions help make agent communication more efficient, robust, and accessible to everyone.

---

**Happy coding! 🚀**

For questions about contributing, please open an issue or contact the maintainers.
