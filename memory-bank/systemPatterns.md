# MEMORY BANK: SYSTEM PATTERNS

## 🏗️ ARCHITECTURAL PATTERNS

### Primary Architecture Style
**Pattern:** Microservices with Background Task Processing
**Rationale:** Separates concerns between web API, background scanning, and data processing
**Implementation:** FastAPI for API layer + Celery for background tasks + Redis for coordination

### Core Design Patterns
- **Repository Pattern:** SQLAlchemy ORM with async patterns for data access
- **Dependency Injection:** FastAPI's built-in DI for service layer management
- **Observer Pattern:** Celery tasks for monitoring and notification workflows
- **Factory Pattern:** Database session and VK API client factories
- **Adapter Pattern:** VKBottle integration for VK API access

### Data Patterns
- **Input Processing:** VK API → Celery tasks → Structured data storage
- **Output Handling:** REST API + Web interface for data consumption
- **Storage:** PostgreSQL with optimized indexing for comment search

## 🔧 TECHNICAL STACK DECISIONS

### Core Technologies
- **Language:** Python 3.13.x (latest stable)
- **Framework:** FastAPI 0.115.x (modern async web framework)
- **API Integration:** VKBottle 4.5.2 (VK API specialized library)
- **Database:** PostgreSQL 17 + SQLAlchemy 2.0.41 (async ORM)
- **Caching:** Redis 7.4.x (caching + task broker)
- **Task Queue:** Celery 5.5.x (background processing)
- **Server:** Uvicorn 0.34.3 (ASGI server)

### Infrastructure
- **Platform:** Linux Ubuntu 24.04 LTS (confirmed)
- **Containerization:** Docker 27.x + Docker Compose
- **Web Server:** Nginx 1.27.x (reverse proxy + static files)
- **SSL:** Certbot 3.x (Let's Encrypt automation)
- **Monitoring:** Health checks + structured logging

## 📊 PERFORMANCE PATTERNS

### Scalability Approach
- **Horizontal Scaling:** Multiple Celery workers for parallel comment scanning
- **Vertical Scaling:** Database connection pooling + async processing
- **Caching Strategy:** Redis for VK API responses and frequent queries
- **Optimization:** Database indexing on comment search fields

### Background Processing
- **Task Distribution:** Redis as Celery broker for task distribution
- **Rate Limiting:** VK API rate limiting (3 requests/second)
- **Error Handling:** Retry mechanisms with exponential backoff
- **Monitoring:** Task status tracking and failure notifications

## 🔒 SECURITY PATTERNS

### Authentication & Authorization
- **API Security:** JWT tokens for API access
- **Password Hashing:** bcrypt for credential storage
- **Rate Limiting:** API endpoint protection against abuse
- **CORS:** Configured for frontend integration

### Data Protection
- **Input Validation:** Pydantic schemas for all API inputs
- **SQL Injection:** SQLAlchemy ORM provides protection
- **XSS Protection:** Framework-level security headers
- **Data Encryption:** HTTPS enforcement + database encryption at rest

### VK API Security
- **Token Management:** Secure storage of VK access tokens
- **Scope Limitation:** Minimal required permissions
- **Error Handling:** Secure error messages without token exposure

## 📝 INTEGRATION PATTERNS

### VK API Integration
- **Pattern:** Adapter + Factory pattern for VK API client
- **Rate Limiting:** Built-in request throttling
- **Error Handling:** Comprehensive VK API error response handling
- **Data Transformation:** VK response → internal data models

### Database Integration
- **Connection Pattern:** Async session factory with connection pooling
- **Migration Strategy:** Alembic for database schema management
- **Query Optimization:** Eager loading for related data
- **Transaction Management:** Context managers for data consistency

### External Service Integration
- **Health Checks:** Dependency health verification
- **Circuit Breaker:** Failure isolation for external services
- **Monitoring:** Service availability tracking
- **Logging:** Structured logging for integration debugging 