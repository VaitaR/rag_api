# 🚀 Dash Assistant - Quick Start Guide

Простой способ запустить и протестировать Dash Assistant на вашей машине.

## 📋 Требования

- Docker и Docker Compose
- Git
- curl и jq (для тестирования)

## 🎯 Демо режим (рекомендуется для начала)

Запустите с тестовыми данными без настройки:

```bash
# 1. Клонируйте репозиторий
git clone <your-repo-url>
cd rag_api_project

# 2. Запустите демо
./demo-start.sh
```

**Что включает демо:**
- ✅ 5 примеров дашбордов (User Retention, Revenue Analytics, и др.)
- ✅ 7 примеров графиков с реальными метаданными  
- ✅ Mock embeddings (не нужен OpenAI API ключ)
- ✅ Полная функциональность поиска и feedback
- ✅ Slack интеграция (тестовый режим)

## 🧪 Тестирование

После запуска демо:

```bash
# Автоматическое тестирование всех endpoints
./test-api.sh

# Мониторинг системы
./monitor.sh

# Ручное тестирование
curl -X POST "http://localhost:8000/dash/query" \
  -H "Content-Type: application/json" \
  -d '{"q": "retention analysis", "top_k": 3}'
```

**Доступные endpoints:**
- 🌐 API: http://localhost:8000
- 📖 Документация: http://localhost:8000/docs
- 🏥 Здоровье: http://localhost:8000/dash/health
- 📊 Статистика: http://localhost:8000/dash/stats

## 🚀 Продакшен режим

Когда готовы использовать свои данные:

### 1. Подготовьте данные

```bash
# Создайте директорию для ваших данных
mkdir -p data/production

# Скопируйте шаблоны для начала
cp tests/fixtures/superset/* data/production/

# Отредактируйте файлы под ваши данные:
# - dashboards.csv (метаданные дашбордов)
# - charts.csv (метаданные графиков)
# - enrichment.yaml (правила обогащения)
# - md/ (markdown документация)
```

### 2. Настройте окружение

```bash
# Скопируйте и отредактируйте конфигурацию
cp .env.production .env

# Обязательно настройте:
# - RAG_OPENAI_API_KEY=sk-your-key-here
# - POSTGRES_PASSWORD=secure-password
# - JWT_SECRET=secure-jwt-secret
```

### 3. Запустите продакшен

```bash
./production-start.sh
```

## 🛠️ Управление

```bash
# Остановить все сервисы
docker-compose down

# Перезапустить
docker-compose restart

# Посмотреть логи
docker-compose logs -f fastapi

# Очистить данные (осторожно!)
docker-compose down -v
```

## 🔧 Troubleshooting

### Проблемы с запуском
```bash
# Проверьте статус Docker
docker-compose ps

# Проверьте логи
docker-compose logs

# Перезапустите сервисы
docker-compose restart
```

### API не отвечает
```bash
# Проверьте здоровье
curl http://localhost:8000/dash/health

# Проверьте порты
netstat -tulpn | grep 8000
```

### База данных недоступна
```bash
# Проверьте PostgreSQL
docker-compose logs db

# Перезапустите БД
docker-compose restart db
```

## 📞 Поддержка

- 📖 Полная документация: [README.md](README.md)
- 🐛 Issues: [GitHub Issues](your-repo-issues-url)
- 💬 Slack: #dash-assistant

## 🎯 Что дальше?

1. **Протестируйте демо** - убедитесь что все работает
2. **Добавьте свои данные** - замените тестовые данные
3. **Настройте Slack** - интегрируйте с вашим workspace
4. **Мониторинг** - настройте алерты и логирование
5. **Продакшен** - разверните на сервере

Удачи! 🚀
