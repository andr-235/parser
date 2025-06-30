# 🚀 VK Comments Parser

> **Современная система мониторинга комментариев ВКонтакте с FastAPI и uv**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-0.7+-green.svg)](https://github.com/astral-sh/uv)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Высокопроизводительное FastAPI приложение для мониторинга и анализа комментариев в группах ВКонтакте с поддержкой асинхронной обработки, background задач и современным стеком разработки.

## ✨ Возможности

### 🔍 **VK API Integration**
- Мониторинг комментариев в группах ВКонтакте
- Поиск по ключевым словам
- Получение информации о пользователях и группах
- Rate limiting и обработка ошибок API

### 🚀 **FastAPI Application**
- 22 современных API endpoints
- Async/await архитектура
- Автоматическая документация (OpenAPI/Swagger)
- Pydantic валидация данных
- JWT аутентификация

### 🗄️ **Database & Storage**
- PostgreSQL с async SQLAlchemy 2.0
- Alembic миграции
- Redis для кеширования и очередей

### ⚡ **Background Processing**
- Celery для фоновых задач
- Redis как message broker
- Мониторинг задач

### 🛡️ **Security & Quality**
- Pre-commit hooks с Ruff, Black, mypy
- Банdit для безопасности
- 80%+ test coverage
- Type hints везде

## 🚀 Быстрый старт

### 📋 Требования
- Python 3.11+
- uv 0.7+
- PostgreSQL 15+
- Redis 7+

### 🔧 Установка

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd parser
```

2. **Установка uv** (если не установлен)
```bash
# Linux/Mac/Windows
curl -LsSf https://astral.sh/uv/install.sh | sh
# или через pip
pip install uv
```

3. **Установка зависимостей**
```bash
# Development окружение
make setup-dev
# или напрямую
uv sync --all-extras
uv run pre-commit install
```

4. **Настройка окружения**
```bash
# Копирование примера конфигурации
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

5. **Запуск базы данных**
```bash
# Через Docker Compose
make docker-dev
# или локально настройте PostgreSQL и Redis
```

6. **Применение миграций**
```bash
make db-upgrade
```

7. **Запуск приложения**
```bash
# Development сервер
make dev
# или
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

🎉 **Готово!** Приложение доступно по http://localhost:8000

## 📚 Документация API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🛠️ Development Commands

uv и Makefile предоставляют удобные команды для разработки:

### 📦 **Управление зависимостями**
```bash
# Установка production зависимостей
make install

# Установка development зависимостей
make install-dev

# Обновление зависимостей
make update

# Экспорт requirements для совместимости
make requirements-export
```

### 🧪 **Тестирование**
```bash
# Запуск всех тестов с coverage
make test

# Быстрые тесты без coverage
make test-fast

# Только integration тесты
make test-integration

# Запуск конкретного теста
uv run pytest tests/test_api/test_vk.py::test_get_group_info -v
```

### 🔍 **Code Quality**
```bash
# Все проверки качества кода
make lint

# Автоисправление и форматирование
make lint-fix

# Только форматирование
make format

# Pre-commit hooks на всех файлах
make pre-commit

# Комплексная проверка (lint + test + security)
make check
```

### 🗄️ **База данных**
```bash
# Применить миграции
make db-upgrade

# Откатить миграцию на одну назад
make db-downgrade

# Создать новую миграцию
make db-migration MSG="add new table"

# Сброс БД (ОСТОРОЖНО!)
make db-reset
```

### 🐳 **Docker**
```bash
# Сборка Docker образа
make docker-build

# Запуск в development режиме
make docker-dev

# Запуск в production режиме
make docker-prod

# Просмотр логов
make docker-logs

# Очистка контейнеров
make docker-clean
```

### 🔒 **Безопасность**
```bash
# Проверка безопасности
make security

# Проверка уязвимостей в зависимостях
make deps-check

# Обновление зависимостей с проверкой безопасности
make update-deps
```

## 🏗️ Архитектура проекта

```
parser/
├── app/                          # 🐍 Основное приложение
│   ├── api/                      # 🛣️ API маршруты
│   │   └── v1/                   # 📍 API версия 1
│   │       ├── health.py         # ❤️ Health checks
│   │       ├── monitoring.py     # 📊 Мониторинг
│   │       ├── vk_integration.py # 🔗 VK API endpoints
│   │       └── vk.py            # 🎯 VK основные методы
│   ├── core/                     # ⚙️ Ядро приложения
│   │   ├── config.py            # 🔧 Конфигурация
│   │   ├── database.py          # 🗄️ База данных
│   │   └── vk_client.py         # 📡 VK API клиент
│   ├── models/                   # 🏗️ SQLAlchemy модели
│   ├── schemas/                  # 📋 Pydantic схемы
│   ├── services/                 # 💼 Бизнес логика
│   └── main.py                   # 🚀 FastAPI приложение
├── tests/                        # 🧪 Тесты
├── memory-bank/                  # 🧠 Документация проекта
├── docker-compose.dev.yml        # 🐳 Docker для разработки
├── Dockerfile                    # 📦 Docker образ
├── pyproject.toml               # 📄 Poetry + инструменты конфигурация
├── Makefile                     # 🔧 Удобные команды
└── README.md                    # 📖 Эта документация
```

## 🔧 Конфигурация

### Environment Variables

Основные переменные окружения (подробнее в `.env.example`):

```bash
# 🔐 Безопасность
SECRET_KEY="your-secret-key"
VK_API_TOKEN="your-vk-token"

# 🗄️ База данных
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"
REDIS_URL="redis://localhost:6379/0"

# 🎛️ Приложение
APP_NAME="VK Comments Parser"
DEBUG=true
ENVIRONMENT="development"
```

### Poetry Configuration

Проект использует современную конфигурацию в `pyproject.toml`:

```toml
[tool.poetry]
name = "vk-comments-parser"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115.14"
# ... другие зависимости

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.3"
ruff = "^0.9.4"
# ... dev зависимости

[tool.poetry.scripts]
dev = "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
prod = "gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker"
```

## 🔄 CI/CD & Deployment

### GitHub Actions
- ✅ Автоматическое тестирование
- 🔍 Code quality проверки
- 🔒 Security scanning
- 🐳 Docker builds
- 📊 Coverage reporting

### Production Deployment
```bash
# Production установка
poetry install --only=main --with=production

# Запуск с Gunicorn
make prod
# или
poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🤝 Contributing

1. **Fork** репозиторий
2. Создайте **feature branch**: `git checkout -b feature/amazing-feature`
3. **Установите pre-commit**: `poetry run pre-commit install`
4. Внесите изменения и **добавьте тесты**
5. **Запустите проверки**: `make check`
6. **Commit**: `git commit -m 'feat: add amazing feature'`
7. **Push**: `git push origin feature/amazing-feature`
8. Создайте **Pull Request**

### Code Style
- ✅ **Black** для форматирования
- 🔍 **Ruff** для linting
- 🎯 **mypy** для type checking
- 🛡️ **Bandit** для безопасности
- 📝 **Docstrings** для всех публичных методов
- 🏷️ **Type hints** везде

## 📊 Мониторинг & Logging

### Health Checks
- `GET /health` - Базовый health check
- `GET /api/v1/health/db` - Проверка БД
- `GET /api/v1/health/redis` - Проверка Redis
- `GET /api/v1/health/vk` - Проверка VK API

### Metrics
- Prometheus metrics на порту 9090
- Structured logging с loguru
- Sentry интеграция для production

## 🐛 Troubleshooting

### Частые проблемы

**Poetry не найден**
```bash
# Добавьте Poetry в PATH или переустановите
curl -sSL https://install.python-poetry.org | python3 -
```

**VK API ошибки**
```bash
# Проверьте токен и права доступа
make test-integration  # Запустит VK API тесты
```

**База данных недоступна**
```bash
# Проверьте connection string и запустите PostgreSQL
make docker-dev  # Поднимет все сервисы в Docker
```

**Медленные тесты**
```bash
# Запустите только быстрые тесты
make test-fast

# Или только unit тесты
poetry run pytest tests/unit/ -v
```

## 📄 License

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Современный веб фреймворк
- [Poetry](https://python-poetry.org/) - Управление зависимостями
- [Ruff](https://docs.astral.sh/ruff/) - Супербыстрый Python linter
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM для работы с БД

---

💡 **Нужна помощь?** Создайте [Issue](../../issues) или обратитесь к [документации API](http://localhost:8000/docs)

🚀 **Готов к продакшену!** Следуйте best practices и наслаждайтесь современной разработкой на Python!
