# Guardrails and Monitoring RAG with RBAC

A comprehensive solution for implementing guardrails, monitoring, and Role-Based Access Control (RBAC) in Retrieval-Augmented Generation (RAG) systems.

## Overview

This project provides a robust framework for:
- **Guardrails**: Implementing safety mechanisms and content validation in RAG pipelines
- **Monitoring**: Real-time tracking and logging of RAG system performance and behavior
- **RBAC**: Role-Based Access Control for secure access management to RAG resources and data

## Features

### 🛡️ Guardrails
- Input validation and sanitization
- Output content filtering and safety checks
- PII (Personally Identifiable Information) detection and redaction
- Token limit management
- Response quality validation

### 📊 Monitoring
- Real-time performance metrics
- Query tracking and analytics
- Response quality monitoring
- System health checks
- Audit logging

### 🔐 RBAC
- User role management
- Permission-based access control
- Resource authorization
- Audit trail for access events
- Multi-tenant support

## Project Structure

```
.
├── README.md
├── .gitignore
├── requirements.txt
├── setup.py
│
├── guardrails/
│   ├── __init__.py
│   ├── input_validation.py
│   ├── output_filtering.py
│   └── pii_detection.py
│
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py
│   ├── logger.py
│   └── analytics.py
│
├── rbac/
│   ├── __init__.py
│   ├── roles.py
│   ├── permissions.py
│   └── access_control.py
│
├── rag/
│   ├── __init__.py
│   ├── retriever.py
│   ├── generator.py
│   └── pipeline.py
│
├── config/
│   ├── __init__.py
│   └── config.yaml
│
├── tests/
│   ├── __init__.py
│   ├── test_guardrails.py
│   ├── test_monitoring.py
│   └── test_rbac.py
│
└── examples/
    └── basic_usage.py
```

## Installation

### Prerequisites
- Python 3.10+
- pip or conda

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/charu-86/Guardrails-and-Monitoring-RAG-with-RBAC-.git
cd Guardrails-and-Monitoring-RAG-with-RBAC-
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from guardrails import InputValidator, OutputFilter
from monitoring import MetricsCollector
from rbac import RoleBasedAccessControl
from rag import RAGPipeline

# Initialize RBAC
rbac = RoleBasedAccessControl()
user = rbac.authenticate(username="user", password="pass")

# Check permissions
if rbac.check_permission(user, "query_rag"):
    # Initialize guardrails
    input_validator = InputValidator()
    output_filter = OutputFilter()
    
    # Initialize monitoring
    metrics = MetricsCollector()
    
    # Initialize RAG pipeline
    rag = RAGPipeline()
    
    # Process query with guardrails
    validated_query = input_validator.validate(user_query)
    
    # Generate response
    response = rag.generate(validated_query)
    
    # Filter output
    safe_response = output_filter.filter(response)
    
    # Track metrics
    metrics.record_query(validated_query, safe_response)
else:
    print("Access denied")
```

## Configuration

Edit `config/config.yaml` to customize:
- Guardrail thresholds
- Monitoring settings
- RBAC policies
- RAG model parameters

```yaml
guardrails:
  enable_pii_detection: true
  max_token_limit: 2000
  
monitoring:
  enable_logging: true
  log_level: INFO
  
rbac:
  enable_rbac: true
  default_role: viewer
  
rag:
  model: "gpt-3.5-turbo"
  temperature: 0.7
```

## API Documentation

### Guardrails Module
- `InputValidator()`: Validates and sanitizes user inputs
- `OutputFilter()`: Filters and validates generated responses
- `PIIDetector()`: Detects and redacts PII

### Monitoring Module
- `MetricsCollector()`: Collects performance metrics
- `Logger()`: Handles audit logging
- `Analytics()`: Provides analytics and insights

### RBAC Module
- `RoleBasedAccessControl()`: Main RBAC manager
- `Role()`: Define user roles
- `Permission()`: Manage permissions

### RAG Module
- `RAGPipeline()`: Main RAG processing pipeline
- `Retriever()`: Document retrieval engine
- `Generator()`: Response generation engine

## Testing

Run tests using pytest:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_guardrails.py

# Run with coverage
pytest --cov=. tests/
```

## Monitoring & Logging

The system logs all activities including:
- User queries
- Access control decisions
- Guardrail violations
- System performance metrics

Access logs at: `logs/rag_system.log`

## Security Considerations

- All user inputs are validated and sanitized
- PII is automatically detected and redacted
- RBAC enforces least-privilege access
- All operations are audited and logged
- Environment variables are used for sensitive configuration

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## Development

### Setting up development environment

```bash
pip install -r requirements-dev.txt
```

### Code style

This project uses:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

```bash
black .
flake8 .
mypy .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions:
- Open an [issue](https://github.com/charu-86/Guardrails-and-Monitoring-RAG-with-RBAC-/issues)
- Check existing [documentation](https://github.com/charu-86/Guardrails-and-Monitoring-RAG-with-RBAC-/wiki)

## Roadmap

- [ ] Multi-model support
- [ ] Advanced analytics dashboard
- [ ] API gateway implementation
- [ ] Performance optimization
- [ ] Extended RBAC features

## Authors

- **Charu Kashyap** - Initial work

## Acknowledgments

- RAG research community
- Security best practices from OWASP
- RBAC design patterns

---

**Note**: This is a comprehensive RAG framework with enterprise-grade security and monitoring. Ensure all sensitive configurations are properly secured before deployment.
