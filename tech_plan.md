# 🚀 Технический план: Система мониторинга комментариев ВКонтакте

## 🎯 Цель проекта
Создание системы для мониторинга комментариев в группах ВКонтакте с поиском по ключевым словам, включающей современный веб-интерфейс и REST API.

## 🏗️ Технологический стек (версии 2025)

### 🖥️ Сервер и инфраструктура
- **ОС:** Ubuntu Server 24.04 LTS
- **Python:** 3.13.x (последняя стабильная)
- **Веб-сервер:** Nginx 1.27.x
- **SSL:** Certbot 3.x (Let's Encrypt)
- **Контейнеризация:** Docker 27.x + Docker Compose

### ⚡ Backend Framework
- **Framework:** FastAPI 0.115.x (последняя стабильная)
- **ASGI Server:** Uvicorn 0.34.3 (последняя версия)
- **VK API:** VKBottle 4.5.2 (последняя версия)
- **HTTP Client:** httpx 0.28.x
- **Validation:** Pydantic 2.10.x (последняя)

### 🗄️ База данных
- **СУБД:** PostgreSQL 17 (последняя LTS)
- **ORM:** SQLAlchemy 2.0.41 (асинхронная, последняя)
- **Миграции:** Alembic 1.14.x
- **Драйвер:** asyncpg 0.30.x (асинхронный PostgreSQL)
- **Пулы соединений:** SQLAlchemy async engine

### 📦 Кэширование и очереди
- **Cache:** Redis 7.4.x (последняя стабильная)
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

## 📦 requirements.txt (актуальные версии 2025)

### base.txt
```txt
# Web Framework (последние стабильные версии)
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

### production.txt
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

## 🐳 Docker Configuration (2025)

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

### docker-compose.yml (актуальные образы)
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
    image: postgres:17-alpine  # PostgreSQL 17
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
    image: redis:7.4-alpine  # Redis 7.4
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

  nginx:
    image: nginx:1.27-alpine  # Nginx 1.27
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

## 🔧 Конфигурация FastAPI (2025)

### main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings
from app.database import create_tables
from app.api.v1 import groups, keywords, comments, scanning


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="VK Comments Monitor",
    version="1.0.0",
    description="Система мониторинга комментариев ВКонтакте",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# API routes
app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
app.include_router(keywords.router, prefix="/api/v1/keywords", tags=["keywords"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["comments"])
app.include_router(scanning.router, prefix="/api/v1/scan", tags=["scanning"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

## 🗄️ База данных (PostgreSQL 17)

### models/comment.py (SQLAlchemy 2.0)
```python
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    vk_comment_id = Column(BigInteger, nullable=False)
    vk_post_id = Column(BigInteger, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="SET NULL"))
    author_id = Column(BigInteger, nullable=False)
    author_name = Column(String(255))
    text = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    post_url = Column(String(500))
    comment_url = Column(String(500))
    is_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    group = relationship("Group", back_populates="comments")
    keyword = relationship("Keyword", back_populates="comments")

    __table_args__ = (
        Index("idx_comments_vk_ids", "vk_comment_id", "vk_post_id", unique=True),
        Index("idx_comments_group", "group_id"),
        Index("idx_comments_date", "date"),
    )
```

## 🔌 API с FastAPI 0.115 + Pydantic 2.10

### schemas/comment.py
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CommentBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    author_name: Optional[str] = Field(None, max_length=255)


class CommentCreate(CommentBase):
    vk_comment_id: int = Field(..., gt=0)
    vk_post_id: int = Field(..., gt=0)
    group_id: int = Field(..., gt=0)
    keyword_id: Optional[int] = Field(None, gt=0)
    author_id: int = Field(..., gt=0)
    date: datetime
    post_url: Optional[str] = Field(None, max_length=500)
    comment_url: Optional[str] = Field(None, max_length=500)


class CommentResponse(CommentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    vk_comment_id: int
    vk_post_id: int
    group_id: int
    keyword_id: Optional[int] = None
    author_id: int
    date: datetime
    post_url: Optional[str] = None
    comment_url: Optional[str] = None
    is_reviewed: bool = False
    created_at: datetime


class CommentsListResponse(BaseModel):
    comments: list[CommentResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
```

## 🔧 VKBottle 4.5.2 интеграция

### core/scanner.py
```python
import asyncio
from typing import List, Optional
from vkbottle import API
from loguru import logger

from app.core.config import settings
from app.models.comment import Comment
from app.schemas.comment import CommentCreate


class VKScanner:
    def __init__(self):
        self.api = API(settings.VK_ACCESS_TOKEN)
        self.version = settings.VK_API_VERSION
        
    async def scan_group_comments(
        self, 
        group_id: int, 
        keywords: List[str],
        posts_limit: int = 100
    ) -> List[CommentCreate]:
        """Сканирование комментариев в группе"""
        comments = []
        
        try:
            # Получаем посты группы
            posts = await self.api.wall.get(
                owner_id=-group_id,
                count=posts_limit,
                v=self.version
            )
            
            for post in posts.items:
                # Получаем комментарии к посту
                post_comments = await self.api.wall.get_comments(
                    owner_id=-group_id,
                    post_id=post.id,
                    count=100,
                    v=self.version
                )
                
                for comment in post_comments.items:
                    # Проверяем наличие ключевых слов
                    for keyword in keywords:
                        if keyword.lower() in comment.text.lower():
                            comment_data = CommentCreate(
                                vk_comment_id=comment.id,
                                vk_post_id=post.id,
                                group_id=group_id,
                                author_id=comment.from_id,
                                author_name=getattr(comment, 'author_name', ''),
                                text=comment.text,
                                date=comment.date,
                                post_url=f"https://vk.com/wall-{group_id}_{post.id}",
                                comment_url=f"https://vk.com/wall-{group_id}_{post.id}?reply={comment.id}"
                            )
                            comments.append(comment_data)
                            break
                
                # Задержка для соблюдения лимитов API
                await asyncio.sleep(1 / settings.VK_REQUESTS_PER_SECOND)
                
        except Exception as e:
            logger.error(f"Ошибка сканирования группы {group_id}: {e}")
            
        return comments
```

## 🧪 Тестирование (pytest 8.3 + httpx)

### tests/test_api.py
```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "version": "1.0.0"}


@pytest.mark.asyncio
async def test_create_group():
    async with AsyncClient(app=app, base_url="http://test") as client:
        group_data = {
            "vk_group_id": 123456789,
            "name": "Test Group",
            "screen_name": "testgroup"
        }
        response = await client.post("/api/v1/groups/", json=group_data)
        assert response.status_code == 201
        data = response.json()
        assert data["vk_group_id"] == 123456789
        assert data["name"] == "Test Group"


@pytest.mark.asyncio
async def test_get_comments():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/comments/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert "comments" in data
        assert "total" in data
        assert "page" in data
```

## 🚀 Команды развертывания (Ubuntu 24.04)

### Быстрый старт
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.13 и зависимостей
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
# Редактируем .env

# Настройка базы данных
sudo -u postgres createdb vk_monitor
sudo -u postgres createuser vk_monitor

# Выполнение миграций
alembic upgrade head

# Запуск приложения
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker развертывание
```bash
# Клонирование и настройка
git clone https://github.com/username/vk-comments-monitor.git
cd vk-comments-monitor
cp .env.example .env

# Сборка и запуск
docker-compose up -d --build

# Выполнение миграций
docker-compose exec app alembic upgrade head

# Проверка статуса
docker-compose ps
```

## 📊 Мониторинг (2025)

### Health Endpoints
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "database"}
    except Exception as e:
        return {"status": "unhealthy", "service": "database", "error": str(e)}

@router.get("/health/redis")
async def health_redis():
    try:
        redis_client = Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        return {"status": "healthy", "service": "redis"}
    except Exception as e:
        return {"status": "unhealthy", "service": "redis", "error": str(e)}
```

Этот обновленный технический план использует все последние стабильные версии компонентов на 2025 год и обеспечивает современную, производительную архитектуру для системы мониторинга комментариев ВКонтакте.