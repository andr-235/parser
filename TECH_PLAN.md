# 🚀 Технический план: Система мониторинга комментариев ВКонтакте

## 🎯 Цель проекта
Создание системы для мониторинга комментариев в группах ВКонтакте с поиском по ключевым словам, включающей современный веб-интерфейс и REST API.

## 🏗️ Технологический стек (2025)

### 🖥️ Сервер и инфраструктура
- **ОС:** Ubuntu Server 24.04 LTS
- **Python:** 3.13.x
- **Веб-сервер:** Nginx 1.27.x
- **SSL:** Certbot 3.x (Let's Encrypt)
- **Контейнеризация:** Docker 27.x + Docker Compose

### ⚡ Backend
- **Framework:** FastAPI 0.115.x
- **ASGI Server:** Uvicorn 0.34.3
- **VK API:** VKBottle 4.5.2
- **HTTP Client:** httpx 0.28.x
- **Validation:** Pydantic 2.10.x

### 🗄️ База данных
- **СУБД:** PostgreSQL 17
- **ORM:** SQLAlchemy 2.0.41 (асинхронная)
- **Миграции:** Alembic 1.14.x
- **Драйвер:** asyncpg 0.30.x
- **Пулы соединений:** SQLAlchemy async engine

### 📦 Кэширование и очереди
- **Cache:** Redis 7.4.x
- **Background Tasks:** Celery 5.5.x + Redis broker
- **Session Store:** Redis для веб-сессий

### 🧪 Тестирование
- **Framework:** pytest 8.3.x
- **Async Support:** pytest-asyncio 0.25.x
- **HTTP Testing:** httpx 0.28.x
- **Coverage:** pytest-cov 6.x

### 🔧 Дополнительные инструменты
- **Environment:** python-dotenv 1.0.x
- **Logging:** loguru 0.7.x
- **Scheduling:** APScheduler 3.11.x
- **Process Management:** systemd (Ubuntu)

## 📁 Структура проекта

```
vk-comments-monitor/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI приложение
│   ├── config.py              # Настройки приложения
│   ├── database.py            # Подключение к БД
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── group.py
│   │   ├── keyword.py
│   │   ├── comment.py
│   │   └── scan_log.py
│   ├── schemas/               # Pydantic схемы
│   │   ├── __init__.py
│   │   ├── group.py
│   │   ├── keyword.py
│   │   ├── comment.py
│   │   └── common.py
│   ├── api/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── deps.py           # Зависимости
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── groups.py
│   │   │   ├── keywords.py
│   │   │   ├── comments.py
│   │   │   └── scanning.py
│   ├── core/                  # Основная логика
│   │   ├── __init__.py
│   │   ├── security.py       # JWT, auth
│   │   ├── scanner.py        # VK API сканер
│   │   └── cache.py          # Redis кэширование
│   ├── workers/               # Celery задачи
│   │   ├── __init__.py
│   │   ├── celery.py
│   │   └── tasks.py
│   └── utils/                 # Утилиты
│       ├── __init__.py
│       ├── logging.py
│       └── helpers.py
├── static/                    # Статические файлы
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                 # HTML шаблоны
│   ├── base.html
│   ├── index.html
│   ├── groups.html
│   ├── keywords.html
│   └── comments.html
├── alembic/                   # Миграции БД
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── tests/                     # Тесты
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_core/
│   └── test_workers/
├── deployment/                # Развертывание
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── docker-compose.prod.yml
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── sites-available/
│   ├── systemd/
│   │   ├── vk-monitor.service
│   │   └── vk-celery.service
│   └── scripts/
│       ├── deploy.sh
│       └── backup.sh
├── requirements/              # Зависимости
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env.example              # Пример переменных окружения
├── .gitignore
├── alembic.ini
├── pytest.ini
├── pyproject.toml
└── README.md
```

## 🗄️ Схема базы данных

### Таблица groups
```sql
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    vk_group_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    screen_name VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    last_check TIMESTAMP,
    check_interval INTEGER DEFAULT 300,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_groups_vk_id ON groups(vk_group_id);
CREATE INDEX idx_groups_active ON groups(is_active);
```

### Таблица keywords
```sql
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    case_sensitive BOOLEAN DEFAULT false,
    whole_word BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_keywords_active ON keywords(is_active);
CREATE INDEX idx_keywords_category ON keywords(category);
```

### Таблица comments
```sql
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    vk_comment_id BIGINT NOT NULL,
    vk_post_id BIGINT NOT NULL,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    keyword_id INTEGER REFERENCES keywords(id) ON DELETE SET NULL,
    author_id BIGINT NOT NULL,
    author_name VARCHAR(255),
    author_screen_name VARCHAR(100),
    text TEXT NOT NULL,
    date TIMESTAMP NOT NULL,
    post_url VARCHAR(500),
    comment_url VARCHAR(500),
    is_reviewed BOOLEAN DEFAULT false,
    sentiment VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vk_comment_id, vk_post_id)
);

CREATE INDEX idx_comments_group ON comments(group_id);
CREATE INDEX idx_comments_keyword ON comments(keyword_id);
CREATE INDEX idx_comments_date ON comments(date);
CREATE INDEX idx_comments_author ON comments(author_id);
CREATE INDEX idx_comments_reviewed ON comments(is_reviewed);
```

### Таблица scan_logs
```sql
CREATE TABLE scan_logs (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL, -- 'started', 'completed', 'failed'
    comments_found INTEGER DEFAULT 0,
    new_comments INTEGER DEFAULT 0,
    posts_scanned INTEGER DEFAULT 0,
    error_message TEXT,
    scan_duration INTERVAL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_scan_logs_group ON scan_logs(group_id);
CREATE INDEX idx_scan_logs_status ON scan_logs(status);
CREATE INDEX idx_scan_logs_date ON scan_logs(started_at);
```

## 🚀 requirements.txt (2025)

### base.txt
```txt
# Web Framework
fastapi==0.115.12
uvicorn[standard]==0.34.3

# VK API
vkbottle==4.5.2

# Database
sqlalchemy[asyncio]==2.0.41
alembic==1.14.0
asyncpg==0.30.0

# Validation
pydantic==2.10.7
pydantic-settings==2.7.0

# HTTP Client
httpx==0.28.1

# Caching & Tasks
redis==5.2.1
celery==5.5.0

# Environment & Config
python-dotenv==1.0.1

# Logging
loguru==0.7.3

# Scheduling
apscheduler==3.11.0

# Templating
jinja2==3.1.5

# Date/Time
python-dateutil==2.9.0

# Utilities
python-multipart==0.0.17
email-validator==2.2.0
```

### development.txt
```txt
-r base.txt

# Testing
pytest==8.3.4
pytest-asyncio==0.25.0
pytest-cov==6.0.0

# Development
black==24.10.0
isort==5.13.2
flake8==7.1.1
mypy==1.13.0

# Documentation
mkdocs==1.6.1
mkdocs-material==9.5.47

# Database tools
psycopg2-binary==2.9.10
```

### production.txt
```txt
-r base.txt

# Production WSGI
gunicorn==23.0.0

# Monitoring
sentry-sdk[fastapi]==2.18.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

## 🔧 Конфигурация

### .env файл
```env
# Application
APP_NAME="VK Comments Monitor"
APP_VERSION="1.0.0"
DEBUG=false
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://vk_monitor:password@localhost:5432/vk_monitor
DATABASE_TEST_URL=postgresql+asyncpg://vk_monitor:password@localhost:5432/vk_monitor_test

# VK API
VK_ACCESS_TOKEN=your_vk_group_token_here
VK_API_VERSION=5.131
VK_REQUESTS_PER_SECOND=3

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/vk-monitor/app.log

# Scanning
DEFAULT_SCAN_INTERVAL=300
MAX_POSTS_PER_SCAN=100
MAX_COMMENTS_PER_POST=1000

# Web Interface
STATIC_FILES_DIR=static
TEMPLATES_DIR=templates

# Security
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
ALLOWED_HOSTS=["localhost", "127.0.0.1", "yourdomain.com"]
```

## 🐳 Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://vk_monitor:password@db:5432/vk_monitor
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: vk_monitor
      POSTGRES_USER: vk_monitor
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7.4-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  celery:
    build: .
    command: celery -A app.workers.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://vk_monitor:password@db:5432/vk_monitor
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A app.workers.celery beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://vk_monitor:password@db:5432/vk_monitor
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./static:/var/www/static:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## 🔐 Nginx Configuration

### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web:10m rate=2r/s;

    upstream fastapi {
        server app:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security Headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # Static Files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API Routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://fastapi;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Web Interface
        location / {
            limit_req zone=web burst=10 nodelay;
            proxy_pass http://fastapi;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 🔧 Systemd Services

### vk-monitor.service
```ini
[Unit]
Description=VK Comments Monitor FastAPI application
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=vk-monitor
Group=vk-monitor
WorkingDirectory=/opt/vk-monitor
Environment=PATH=/opt/vk-monitor/venv/bin
ExecStart=/opt/vk-monitor/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/vk-monitor/logs

[Install]
WantedBy=multi-user.target
```

### vk-celery.service
```ini
[Unit]
Description=VK Comments Monitor Celery Worker
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=vk-monitor
Group=vk-monitor
WorkingDirectory=/opt/vk-monitor
Environment=PATH=/opt/vk-monitor/venv/bin
ExecStart=/opt/vk-monitor/venv/bin/celery -A app.workers.celery worker --loglevel=info --concurrency=4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/vk-monitor/logs

[Install]
WantedBy=multi-user.target
```

## 📋 План развертывания

### Этап 1: Подготовка сервера
1. Установка Ubuntu Server 24.04 LTS
2. Обновление системы
3. Установка Docker и Docker Compose
4. Настройка файрвола
5. Создание пользователя для приложения

### Этап 2: Настройка базы данных
1. Установка PostgreSQL 17
2. Создание базы данных и пользователя
3. Настройка соединений
4. Настройка репликации (для продакшена)

### Этап 3: Развертывание приложения
1. Клонирование репозитория
2. Настройка переменных окружения
3. Сборка Docker образов
4. Запуск контейнеров
5. Выполнение миграций

### Этап 4: Настройка веб-сервера
1. Установка и настройка Nginx
2. Получение SSL сертификатов
3. Настройка reverse proxy
4. Тестирование конфигурации

### Этап 5: Мониторинг и логирование
1. Настройка логирования
2. Установка системы мониторинга
3. Настройка алертов
4. Создание дашбордов

### Этап 6: Автоматизация
1. Настройка CI/CD пайплайна
2. Автоматические бэкапы
3. Скрипты обновления
4. Мониторинг безопасности

## 🔍 Команды для развертывания

### Быстрый старт с Docker
```bash
# Клонирование репозитория
git clone https://github.com/username/vk-comments-monitor.git
cd vk-comments-monitor

# Настройка переменных окружения
cp .env.example .env
# Редактируем .env файл

# Сборка и запуск
docker-compose up -d

# Выполнение миграций
docker-compose exec app alembic upgrade head

# Создание суперпользователя
docker-compose exec app python -m app.cli create-superuser
```

### Установка на Ubuntu
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3.13 python3.13-venv python3-pip postgresql-17 redis-server nginx

# Создание пользователя
sudo useradd -m -s /bin/bash vk-monitor

# Клонирование и настройка
sudo -u vk-monitor git clone https://github.com/username/vk-comments-monitor.git /opt/vk-monitor
cd /opt/vk-monitor

# Создание виртуального окружения
sudo -u vk-monitor python3.13 -m venv venv
sudo -u vk-monitor ./venv/bin/pip install -r requirements/production.txt

# Настройка базы данных
sudo -u postgres createdb vk_monitor
sudo -u postgres createuser vk_monitor

# Выполнение миграций
sudo -u vk-monitor ./venv/bin/alembic upgrade head

# Установка systemd сервисов
sudo cp deployment/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vk-monitor vk-celery
sudo systemctl start vk-monitor vk-celery

# Настройка Nginx
sudo cp deployment/nginx/sites-available/vk-monitor /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/vk-monitor /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

## 📊 Мониторинг и метрики

### Health Check Endpoints
- `GET /health` - общее состояние приложения
- `GET /health/db` - состояние базы данных
- `GET /health/redis` - состояние Redis
- `GET /health/vk-api` - доступность VK API

### Ключевые метрики
- Количество активных групп
- Количество найденных комментариев за день/час
- Время выполнения сканирования
- Частота ошибок VK API
- Использование ресурсов (CPU, память, диск)

### Логирование
```python
# Структурированные логи в JSON формате
{
    "timestamp": "2025-01-20T10:30:00Z",
    "level": "INFO",
    "service": "vk-monitor",
    "module": "scanner",
    "action": "scan_group",
    "group_id": 123456,
    "comments_found": 15,
    "duration_ms": 2340,
    "request_id": "req-123-456"
}
```

Этот технический план обеспечивает создание современной, масштабируемой и надежной системы мониторинга комментариев ВКонтакте с использованием последних стабильных версий всех компонентов на 2025 год. 