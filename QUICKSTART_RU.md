# Быстрый Старт - AI Risk Orchestrator

## 5-минутная установка для тестирования

### 1. Установка Зависимостей

```bash
# Перейти в директорию проекта
cd ~/Documents/RISK

# Создать виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
pip install -e risk-core/
```

### 2. Запуск БД через Docker

```bash
# PostgreSQL
docker run -d --name risk-postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=risk_orchestrator \
  -e POSTGRES_USER=riskuser \
  -e POSTGRES_PASSWORD=password123 \
  postgres:15

# Redis (опционально)
docker run -d --name risk-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 3. Настройка .env

```bash
# Скопировать пример
cp .env.example .env

# Минимальная конфигурация для теста
cat > .env << 'EOF'
SECRET_KEY=test-secret-key-change-in-production
DATABASE_URL=postgresql+asyncpg://riskuser:password123@localhost:5432/risk_orchestrator
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
EOF
```

### 4. Инициализация БД

```bash
# Применить миграции
alembic upgrade head
```

### 5. Запуск API

```bash
# Запустить FastAPI
uvicorn app.main:app --reload
```

**API доступен**: http://localhost:8000/docs

---

## Опциональная Установка Dify (для AI-генерации текста)

### 1. Установка Dify

```bash
# Создать директорию
mkdir -p ~/dify && cd ~/dify

# Клонировать репозиторий
git clone https://github.com/langgenius/dify.git
cd dify/docker

# Запустить Dify
docker-compose up -d
```

**Подождать 2-3 минуты, затем открыть**: http://localhost:3001

### 2. Настройка Dify

1. **Зарегистрироваться** в Dify UI
2. **Settings → Model Provider → Add OpenAI**
   - API Key: `sk-...` (ваш OpenAI ключ)
   - Model: `gpt-4` или `gpt-3.5-turbo`

### 3. Создание Workflow для Резюме

1. **Create Workflow** → Text Generation
2. **Name**: `Risk Executive Summary`
3. **Input Variables**:
   ```
   - snapshot_date (text)
   - var_1d_95 (number)
   - stressed_var (number)
   - dv01_total (number)
   - capital_ratio (number)
   - lcr_ratio (number)
   - critical_alerts (text)
   ```

4. **Add LLM Node**:
   - **System Prompt**:
     ```
     You are a risk management expert. 
     Generate a concise executive summary (max 300 words) for the board.
     Focus on key risk metrics, critical alerts, and actionable recommendations.
     ```
   - **User Prompt**:
     ```
     Date: {{snapshot_date}}
     
     Risk Metrics:
     - VaR (1d 95%): {{var_1d_95}}
     - Stressed VaR: {{stressed_var}}
     - DV01: {{dv01_total}}
     - Capital Ratio: {{capital_ratio}}%
     - LCR: {{lcr_ratio}}%
     
     Critical Alerts:
     {{critical_alerts}}
     
     Generate executive summary.
     ```

5. **Publish** → Скопировать API Key

### 4. Добавить Dify в .env

```bash
# Добавить в .env
echo "DIFY_API_URL=http://localhost:3001/v1" >> .env
echo "DIFY_API_KEY_SUMMARY=app-xxx..." >> .env  # Вставить скопированный ключ
```

### 5. Тестирование Dify Integration

```bash
# Проверить статус
curl http://localhost:8000/api/v1/dify/health \
  -H "Authorization: Bearer YOUR_TOKEN"

# Тест генерации резюме
curl -X POST http://localhost:8000/api/v1/dify/summary \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_date": "2024-12-01",
    "var_1d_95": -50000,
    "stressed_var": -75000,
    "dv01_total": 5000,
    "capital_ratio": 15.5,
    "lcr_ratio": 125.0,
    "critical_alerts": "1 critical alert: VaR limit breach"
  }'
```

---

## Первые Шаги

### 1. Создать Admin Пользователя

```python
# В Python консоли
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("admin123")
print(hashed)
```

```sql
-- В psql
psql -U riskuser -d risk_orchestrator

INSERT INTO users (username, email, hashed_password, role, is_active, created_at)
VALUES ('admin', 'admin@test.com', 'ВСТАВИТЬ_HASH', 'ADMIN', true, NOW());
```

### 2. Получить JWT Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 3. Создать Портфель

```bash
curl -X POST http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_name": "Test Portfolio",
    "entity_id": 1,
    "base_currency": "EUR",
    "is_active": true
  }'
```

### 4. Запустить Расчёт Рисков

```bash
curl -X POST http://localhost:8000/api/v1/risk/calculate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "as_of_date": "2024-12-01",
    "calculation_type": "FULL"
  }'
```

---

## Доступные API Endpoints

### Основные
- `GET /api/v1/health` - Health check
- `GET /api/v1/docs` - Swagger UI
- `GET /api/v1/metrics` - Prometheus metrics

### Портфели
- `GET /api/v1/portfolios` - Список портфелей
- `POST /api/v1/portfolios` - Создать портфель

### Риски
- `POST /api/v1/risk/calculate` - Расчёт рисков
- `GET /api/v1/risk_snapshots` - История расчётов

### Алерты
- `GET /api/v1/alerts` - Список алертов
- `POST /api/v1/alerts/{id}/acknowledge` - Подтвердить

### Отчёты
- `POST /api/v1/reports/pdf/generate` - Генерация PDF

### Dify AI (опционально)
- `GET /api/v1/dify/health` - Статус Dify
- `POST /api/v1/dify/summary` - Генерация резюме
- `POST /api/v1/dify/alert-explanation` - Объяснение алерта

---

## Мониторинг

### Prometheus Metrics
http://localhost:9090

### Grafana (если используете docker-compose)
http://localhost:3001

---

## Остановка Сервисов

```bash
# Остановить API
Ctrl+C

# Остановить Docker контейнеры
docker stop risk-postgres risk-redis

# Или полный docker-compose
docker-compose down
```

---

## Полная Документация

См. `INSTALLATION_RU.md` для подробной инструкции.

---

## Быстрая Диагностика

```bash
# Проверка PostgreSQL
docker ps | grep postgres
pg_isready -h localhost -p 5432

# Проверка API
curl http://localhost:8000/api/v1/health

# Проверка Dify
curl http://localhost:3001/health

# Просмотр логов
docker logs risk-postgres
docker logs -f dify_api  # Если используете Dify
```

---

**Готово! Система работает.** 🚀

Следующие шаги см. в `INSTALLATION_RU.md`
