# 📋 Техническая спецификация: Система мониторинга комментариев ВКонтакте

## 🎯 Описание проекта
Система мониторинга комментариев в группах ВКонтакте с поиском по ключевым словам, веб-интерфейсом и REST API на FastAPI + VKBottle.

## 🏗️ Технологический стек (версии 2025)

### Backend Framework
- **FastAPI** 0.115.x - современный веб-фреймворк
- **VKBottle** 4.5.2 - работа с VK API
- **Uvicorn** 0.34.3 - ASGI сервер

### База данных
- **PostgreSQL** 17 - основная БД
- **SQLAlchemy** 2.0.41 - ORM
- **Alembic** 1.14.x - миграции БД
- **asyncpg** 0.30.x - асинхронный драйвер PostgreSQL

### Кэширование и очереди
- **Redis** 7.4.x - кэширование и задачи
- **Celery** 5.5.x - фоновые задачи

### Веб-сервер и прокси
- **Nginx** 1.27.x - reverse proxy + статика
- **Certbot** 3.x - SSL сертификаты

### Валидация данных
- **Pydantic** 2.10.x - валидация и сериализация
- **pydantic-settings** 2.7.x - настройки приложения

### Тестирование и разработка
- **pytest** 8.3.x - фреймворк тестирования
- **pytest-asyncio** 0.25.x - асинхронное тестирование
- **httpx** 0.28.x - HTTP тестирование
- **pytest-cov** 6.x - покрытие тестами

### Операционная система
- **Ubuntu Server** 24.04 LTS - операционная система
- **Python** 3.13.x - язык программирования

### Дополнительные компоненты
- **Docker** 27.x + Docker Compose - контейнеризация
- **httpx** 0.28.x - HTTP клиент
- **loguru** 0.7.x - логирование
- **python-dotenv** 1.0.x - переменные окружения

## 🗂️ Структура приложения

```
vk-comments-monitor/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI приложение
│   ├── config.py              # Настройки
│   ├── database.py            # Подключение к БД
│   ├── models/                # SQLAlchemy модели
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
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── groups.py
│   │       ├── keywords.py
│   │       ├── comments.py
│   │       └── scanning.py
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
├── templates/                 # HTML шаблоны
├── alembic/                   # Миграции БД
├── tests/                     # Тесты
├── deployment/                # Развертывание
│   ├── docker/
│   ├── nginx/
│   ├── systemd/
│   └── scripts/
├── requirements/              # Зависимости
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env.example
├── .gitignore
├── alembic.ini
├── pytest.ini
├── pyproject.toml
└── README.md
```

## 🗄️ Схема базы данных

### Основные таблицы

#### groups (группы ВКонтакте)
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
```

#### keywords (ключевые слова)
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
```

#### comments (найденные комментарии)
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
```

#### scan_logs (логи сканирования)
```sql
CREATE TABLE scan_logs (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    comments_found INTEGER DEFAULT 0,
    new_comments INTEGER DEFAULT 0,
    posts_scanned INTEGER DEFAULT 0,
    error_message TEXT,
    scan_duration INTERVAL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

## 🔧 Конфигурация

### Переменные окружения (.env)
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

# Security
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
ALLOWED_HOSTS=["localhost", "127.0.0.1", "yourdomain.com"]
```

### requirements/base.txt
```txt
# Web Framework (последние стабильные версии 2025)
fastapi==0.115.12
uvicorn[standard]==0.34.3

# VK API (последняя версия)
vkbottle==4.5.2

# Database (SQLAlchemy 2.x с async)
sqlalchemy[asyncio]==2.0.41
alembic==1.14.0
asyncpg==0.30.0

# Validation (Pydantic v2)
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

### requirements/production.txt
```txt
-r base.txt

# Production WSGI/ASGI
gunicorn==23.0.0

# Monitoring
sentry-sdk[fastapi]==2.18.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### requirements/development.txt
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

## 🔌 API спецификация

### Основные эндпоинты
```
GET    /                        # Веб-интерфейс
GET    /health                  # Health check
GET    /health/db               # Проверка БД
GET    /health/redis            # Проверка Redis

GET    /api/v1/groups           # Список групп
POST   /api/v1/groups           # Создать группу
GET    /api/v1/groups/{id}      # Получить группу
PUT    /api/v1/groups/{id}      # Обновить группу
DELETE /api/v1/groups/{id}      # Удалить группу

GET    /api/v1/keywords         # Список ключевых слов
POST   /api/v1/keywords         # Создать ключевое слово
PUT    /api/v1/keywords/{id}    # Обновить ключевое слово
DELETE /api/v1/keywords/{id}    # Удалить ключевое слово

GET    /api/v1/comments         # Список комментариев
GET    /api/v1/comments/{id}    # Получить комментарий
PUT    /api/v1/comments/{id}    # Обновить комментарий (отметить как просмотренный)

POST   /api/v1/scan/group/{id}  # Запустить сканирование группы
POST   /api/v1/scan/all         # Запустить сканирование всех групп
GET    /api/v1/scan/status      # Статус сканирования
GET    /api/v1/scan/logs        # Логи сканирования

GET    /docs                    # Swagger UI документация
GET    /redoc                   # ReDoc документация
```

## 🚀 Развертывание

### Системные требования
- **ОС:** Ubuntu Server 24.04 LTS
- **RAM:** минимум 2GB, рекомендуется 4GB+
- **CPU:** минимум 2 ядра
- **Диск:** минимум 20GB SSD
- **Python:** 3.13.x
- **PostgreSQL:** 17
- **Redis:** 7.4.x
- **Nginx:** 1.27.x

### Docker развертывание
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
    depends_on:
      - db
      - redis

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: vk_monitor
      POSTGRES_USER: vk_monitor
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7.4-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### Ручная установка
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3.13 python3.13-venv python3-pip \
    postgresql-17 redis-server nginx git

# Клонирование проекта
git clone https://github.com/username/vk-comments-monitor.git
cd vk-comments-monitor

# Создание виртуального окружения
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements/production.txt

# Настройка переменных окружения
cp .env.example .env
# Редактирование .env файла

# Настройка PostgreSQL
sudo -u postgres createdb vk_monitor
sudo -u postgres createuser vk_monitor

# Выполнение миграций
alembic upgrade head

# Запуск приложения
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔒 Безопасность

### Аутентификация и авторизация
- JWT токены для API доступа
- Хэширование паролей с bcrypt
- Rate limiting для API эндпоинтов

### Защита данных
- HTTPS обязательно для production
- Валидация входных данных с Pydantic
- SQL injection защита через SQLAlchemy ORM
- CORS настройки

### Мониторинг безопасности
- Логирование всех API запросов
- Мониторинг подозрительной активности
- Регулярное обновление зависимостей

## 📊 Мониторинг и логирование

### Метрики
- Время отклика API
- Количество запросов в секунду
- Использование ресурсов (CPU, RAM, диск)
- Количество найденных комментариев
- Ошибки VK API

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

### Health Check
- `/health` - общий статус приложения
- `/health/db` - статус базы данных
- `/health/redis` - статус Redis
- Автоматические проверки каждые 30 секунд

## 🔧 Производительность

### Оптимизации
- Асинхронное программирование (async/await)
- Пулы соединений к БД
- Кэширование Redis для VK API ответов
- Background tasks для тяжелых операций
- Индексы в PostgreSQL

### Масштабирование
- Горизонтальное: несколько worker процессов
- Вертикальное: увеличение ресурсов сервера
- Load balancing через Nginx
- Репликация PostgreSQL

Эта техническая спецификация обеспечивает создание современной, производительной и безопасной системы мониторинга комментариев ВКонтакте с использованием последних стабильных версий всех компонентов на 2025 год. 