# VK Comments Parser

Система мониторинга комментариев ВКонтакте с использованием FastAPI, PostgreSQL, Redis и Celery.

## 🚀 Cursor AI Integration

Этот проект настроен с современными **Cursor Project Rules** для улучшения разработки с ИИ:

### Активные правила:
- **Git** - Conventional Commits, Git Flow, решение конфликтов
- **Docker** - Security-first практики, multi-stage builds, production deployment
- **Python/FastAPI** - Async паттерны, dependency injection, современная архитектура
- **PostgreSQL** - SQLAlchemy 2.0, оптимизация запросов, миграции
- **Testing** - Pytest с async поддержкой, fixtures, интеграционные тесты

### Как использовать:
```bash
# Правила автоматически активируются при работе с соответствующими файлами
# Или используйте в чате:
@git-commit-standards
@dockerfile-best-practices  
@python-fastapi-best-practices
```

📖 **Подробная документация**: [.cursor/rules/README.md](.cursor/rules/README.md)

## 🛠 Технологический стек

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL с SQLAlchemy 2.0
- **Cache**: Redis
- **Background Tasks**: Celery
- **Deployment**: Docker, Docker Compose
- **Testing**: Pytest

## 📋 Требования

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose (для development)

## 🚀 Быстрый старт

### Development с Docker
```bash
# Клонировать репозиторий
git clone <repository-url>
cd parser

# Запустить в development режиме
docker-compose up --build

# API будет доступен на http://localhost:8000
```

### Локальная разработка
```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload
```

## 📁 Структура проекта

```
.
├── .cursor/rules/           # Cursor AI правила
├── app/
│   ├── api/                # API endpoints
│   ├── core/               # Конфигурация, настройки
│   ├── db/                 # Database модели и соединения
│   ├── services/           # Бизнес-логика
│   └── tasks/              # Celery tasks
├── tests/                  # Тесты
├── docker-compose.yml      # Development environment
└── requirements.txt        # Python зависимости
```

## 🔧 Конфигурация

### Environment Setup

1. **Скопируйте `.env.example` в `.env`**:
```bash
cp .env.example .env
```

2. **Настройте переменные окружения** в `.env` файле:

#### Database Configuration
```env
POSTGRES_DB=vk_monitor_dev
POSTGRES_USER=vk_monitor
POSTGRES_PASSWORD=your_secure_postgres_password_here
```

#### Redis Configuration
```env
REDIS_PASSWORD=your_secure_redis_password_here
```

#### Application Configuration
```env
DEBUG=true
LOG_LEVEL=info
SECRET_KEY=your_secret_key_for_jwt_tokens_here
```

#### VK API Configuration
```env
VK_API_TOKEN=your_vk_api_token_here
VK_API_VERSION=5.131
```

### 🔒 Security Notes

- **Никогда не коммитьте `.env` файл** в git репозиторий
- Используйте **сильные, уникальные пароли** для каждой среды
- **Регулярно ротируйте секреты** в production среде
- Все пароли и токены теперь настраиваются через `.env` файл

## 🧪 Тестирование

```bash
# Запустить все тесты
pytest

# С покрытием
pytest --cov=app

# Только интеграционные тесты
pytest tests/integration/
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔄 Background Tasks

Система использует Celery для фоновых задач:

```bash
# Запустить worker
celery -A app.tasks worker --loglevel=info

# Запустить scheduler
celery -A app.tasks beat --loglevel=info
```

## 🐳 Production Deployment

```bash
# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Мониторинг
docker-compose logs -f
```

## 🤝 Contribution

1. Форкните репозиторий
2. Создайте feature ветку: `git checkout -b feature/новая-функция`
3. Следуйте Conventional Commits: `git commit -m "feat: добавить новую функцию"`
4. Push и создайте Pull Request

### Git Flow:
- `main` - production код
- `develop` - development ветка  
- `feature/*` - новые функции
- `hotfix/*` - критические исправления

## 📄 Лицензия

[MIT License](LICENSE)

---

💡 **Tip**: Используйте Cursor AI с активированными правилами для более эффективной разработки! 