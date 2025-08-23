# 🚀 Dash Assistant - Готовое решение для продакшена

## ✅ Что готово

### 🎯 Демо режим (готов к использованию)
```bash
# Запуск за одну команду - никаких настроек не нужно!
./scripts/demo-start.sh
```

**Что включает:**
- ✅ 2 примера дашбордов с поиском
- ✅ Mock embeddings (не нужен OpenAI API ключ)
- ✅ Полная функциональность API
- ✅ Query и feedback логирование
- ✅ Swagger UI документация: http://localhost:8000/docs

### 🚀 Продакшен режим (готов к настройке)
```bash
# 1. Добавьте свои данные
mkdir -p data/production
cp tests/fixtures/superset/* data/production/
# Отредактируйте файлы под ваши данные

# 2. Настройте окружение
cp .env.production .env
# Добавьте ваш OpenAI API ключ и другие настройки

# 3. Запустите
./scripts/production-start.sh
```

## 📋 Файловая структура

```
rag_api_project/
├── 🎯 ДЕМО РЕЖИМ
│   ├── demo-simple.sh              # Быстрый запуск демо
│   ├── docker-compose.demo.yaml    # Docker конфигурация для демо
│   └── .env.demo                   # Настройки демо
│
├── 🚀 ПРОДАКШЕН РЕЖИМ  
│   ├── production-start.sh         # Запуск продакшена
│   ├── .env.production            # Шаблон настроек продакшена
│   └── data/production/           # Ваши данные (создается автоматически)
│
├── 🛠️ УТИЛИТЫ
│   ├── test-api.sh                # Тестирование всех endpoints
│   ├── monitor.sh                 # Мониторинг системы
│   └── QUICK_START.md             # Инструкции для пользователей
│
└── 📊 ДАННЫЕ
    ├── tests/fixtures/superset/   # Примеры данных для демо
    └── tests/dash_assistant/      # E2E тесты
```

## 🎯 Использование

### Для разработчиков
```bash
# Тестирование
./scripts/demo-start.sh
./scripts/test-api.sh

# Разработка
make test-all
make lint
```

### Для пользователей
```bash
# Быстрый старт
./scripts/demo-start.sh
# Откройте http://localhost:8000/docs

# Продакшен
./scripts/production-start.sh
```

## 🔧 API Endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/dash/health` | GET | Проверка здоровья системы |
| `/dash/stats` | GET | Статистика базы данных |
| `/dash/query` | POST | Поиск дашбордов |
| `/dash/feedback` | POST | Запись feedback/кликов |
| `/slack/command` | POST | Slack интеграция |
| `/docs` | GET | Swagger UI документация |

## 📊 Тестовые данные

**Демо включает:**
- User Retention Dashboard (retention, cohort analysis)
- Revenue Analytics (revenue tracking, forecasting)
- Полнотекстовый поиск по названиям и описаниям
- Mock embeddings для семантического поиска

**Примеры запросов:**
```bash
# Поиск по retention
curl -X POST "http://localhost:8000/dash/query" \
  -H "Content-Type: application/json" \
  -d '{"q": "retention", "top_k": 3}'

# Поиск по revenue  
curl -X POST "http://localhost:8000/dash/query" \
  -H "Content-Type: application/json" \
  -d '{"q": "revenue analytics", "top_k": 2}'
```

## 🎉 Готово к использованию!

1. **Демо**: `./scripts/demo-start.sh` → http://localhost:8000/docs
2. **Продакшен**: Настройте данные → `./scripts/production-start.sh`
3. **Slack**: Настройте токены → используйте `/dash-search`
4. **Мониторинг**: `./scripts/monitor.sh`

Все работает из коробки! 🚀
