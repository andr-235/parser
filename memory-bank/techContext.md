# MEMORY BANK: TECHNICAL CONTEXT

## 💻 DEVELOPMENT ENVIRONMENT
- **OS:** Linux 6.14.0-22-generic (Ubuntu-based)
- **Architecture:** x86_64
- **Shell:** /usr/bin/zsh
- **Workspace:** /home/andrey/Документы/parser

## 🔧 COMPREHENSIVE TECHNICAL REQUIREMENTS

### Platform Requirements
- **Target OS:** Ubuntu Server 24.04 LTS
- **Python Version:** 3.13.x (latest stable)
- **Database:** PostgreSQL 17 with async drivers
- **Runtime Dependencies:** Docker 27.x + Docker Compose

### Performance Requirements
- **API Response Time:** <200ms for typical requests
- **Concurrent Users:** Support for 100+ simultaneous users
- **VK API Rate Limiting:** 3 requests/second compliance
- **Database Performance:** Optimized for comment search operations
- **Memory Usage:** Efficient with async processing patterns
- **Storage:** Scalable for large comment datasets

## 📚 TECHNOLOGY STACK ANALYSIS

### Backend Framework Stack
```python
# Core Web Framework
fastapi==0.115.12           # Modern async web framework
uvicorn[standard]==0.34.3   # ASGI server
pydantic==2.10.7           # Data validation
pydantic-settings==2.7.0   # Configuration management

# VK API Integration
vkbottle==4.5.2            # Specialized VK API library
httpx==0.28.1              # Modern HTTP client

# Database & ORM
sqlalchemy[asyncio]==2.0.41 # Async ORM
alembic==1.14.0            # Database migrations
asyncpg==0.30.0            # Async PostgreSQL driver

# Background Tasks & Caching
celery==5.5.0              # Task queue
redis==5.2.1               # Cache & message broker
apscheduler==3.11.0        # Task scheduling
```

### Infrastructure & Deployment
```dockerfile
# Production Infrastructure
FROM python:3.13-slim      # Base image
postgres:17-alpine         # Database
redis:7.4-alpine           # Caching
nginx:1.27-alpine          # Web server
```

## 🛠️ IMPLEMENTATION CONSIDERATIONS

### Database Architecture
- **Tables:** 4 core tables (groups, keywords, comments, scan_logs)
- **Relationships:** Foreign keys with CASCADE/SET NULL constraints
- **Indexing:** Optimized for comment search and group filtering
- **Connection Pooling:** SQLAlchemy async engine management

### API Architecture
- **RESTful Design:** Standard HTTP methods and status codes
- **OpenAPI Documentation:** Auto-generated with FastAPI
- **Versioning:** /api/v1/ prefix for future compatibility
- **Error Handling:** Structured error responses with proper HTTP codes

### Background Processing Architecture
- **Celery Workers:** Parallel comment scanning processes
- **Task Distribution:** Redis-based task broker
- **Monitoring:** Task status tracking and logging
- **Error Recovery:** Retry mechanisms with exponential backoff

## 🔄 DEVELOPMENT WORKFLOW REQUIREMENTS

### Version Control
- **Git Strategy:** Feature branch workflow with main/develop branches
- **Commit Standards:** Conventional commits for clear history
- **Pre-commit Hooks:** Code formatting and linting automation

### Testing Strategy
```python
# Testing Dependencies
pytest==8.3.4             # Testing framework
pytest-asyncio==0.25.0    # Async testing support
pytest-cov==6.0.0         # Coverage reporting
httpx==0.28.1              # HTTP testing client
```

### Code Quality Tools
```python
# Development Tools
black==24.10.0             # Code formatting
isort==5.13.2              # Import sorting
flake8==7.1.1              # Linting
mypy==1.13.0               # Type checking
```

## 🎯 TECHNICAL DECISIONS ANALYSIS

### 1. **Framework Selection: FastAPI**
**Rationale:** Modern async support, automatic API documentation, excellent performance
**Trade-offs:** Learning curve vs. Django, smaller ecosystem vs. Flask
**Implementation Impact:** Requires async patterns throughout

### 2. **Database: PostgreSQL 17**
**Rationale:** ACID compliance, advanced indexing, JSON support for flexible data
**Trade-offs:** More complex than SQLite, resource requirements
**Implementation Impact:** Requires connection pooling and migration strategy

### 3. **VK API Library: VKBottle**
**Rationale:** Specialized for VK API, async support, active maintenance
**Trade-offs:** Dependency on third-party library vs. direct API calls
**Implementation Impact:** Simplified VK integration but abstraction layer

### 4. **Background Tasks: Celery + Redis**
**Rationale:** Proven solution for distributed task processing
**Trade-offs:** Additional infrastructure complexity vs. simpler alternatives
**Implementation Impact:** Requires Redis deployment and worker management

### 5. **Deployment: Docker + Nginx**
**Rationale:** Consistent deployment, easy scaling, production-ready
**Trade-offs:** Initial complexity vs. direct deployment
**Implementation Impact:** Requires container orchestration knowledge

## 🔒 SECURITY & COMPLIANCE REQUIREMENTS

### Data Protection
- **GDPR Compliance:** User data anonymization options
- **Data Retention:** Configurable comment retention policies
- **Access Control:** Role-based access to sensitive operations

### API Security
- **Authentication:** JWT token-based authentication
- **Rate Limiting:** Protection against API abuse
- **Input Validation:** Comprehensive data sanitization
- **HTTPS:** Mandatory SSL/TLS encryption

### VK API Security
- **Token Security:** Secure storage and rotation of VK tokens
- **Scope Limitation:** Minimal required permissions
- **Error Handling:** No sensitive data in error responses

## 📊 MONITORING & OBSERVABILITY

### Application Monitoring
- **Health Checks:** Multi-level health verification
- **Metrics Collection:** Performance and usage metrics
- **Logging Strategy:** Structured JSON logging
- **Error Tracking:** Comprehensive error capture and alerting

### Infrastructure Monitoring
- **Resource Usage:** CPU, memory, disk monitoring
- **Database Performance:** Query performance tracking
- **Network Monitoring:** API response times and availability
- **Security Monitoring:** Access pattern analysis 