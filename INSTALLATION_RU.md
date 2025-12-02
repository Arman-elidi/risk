# AI Risk Orchestrator - Инструкция по Установке и Использованию

## Содержание
1. [Системные Требования](#системные-требования)
2. [Установка для Разработки](#установка-для-разработки)
3. [Настройка Базы Данных](#настройка-базы-данных)
4. [Интеграция с Dify AI](#интеграция-с-dify-ai)
5. [Запуск Приложения](#запуск-приложения)
6. [Руководство Пользователя](#руководство-пользователя)
7. [Документация API](#документация-api)
8. [Решение Проблем](#решение-проблем)

---

## 1. Системные Требования

### Минимальное Оборудование
- **CPU**: 4 ядра
- **RAM**: 8 GB
- **Storage**: 50 GB SSD

### Программное Обеспечение
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Redis**: 7+ (опционально)
- **Node.js**: 18+ (для фронтенда)
- **Docker**: 24+ (для контейнеризации)

---

## 2. Установка для Разработки

### Шаг 1: Клонирование Репозитория

```bash
cd ~/Documents
# Репозиторий уже существует в RISK/
cd RISK
```

### Шаг 2: Создание Виртуального Окружения

```bash
# Создать виртуальное окружение
python3.11 -m venv venv

# Активировать
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate  # Windows
```

### Шаг 3: Установка Python Зависимостей

```bash
# Обновить pip
pip install --upgrade pip

# Установить зависимости
pip install -r requirements.txt

# Установить библиотеку risk-core
pip install -e risk-core/
```

### Шаг 4: Установка Фронтенд Зависимостей

```bash
cd risk-frontend
npm install
cd ..
```

---

## 3. Настройка Базы Данных

### Вариант А: Используя Docker (Рекомендуется)

```bash
# Запустить PostgreSQL
docker run -d \
  --name risk-postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=risk_orchestrator \
  -e POSTGRES_USER=riskuser \
  -e POSTGRES_PASSWORD=ваш_пароль \
  -v risk_postgres_data:/var/lib/postgresql/data \
  postgres:15

# Запустить Redis (опционально)
docker run -d \
  --name risk-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### Вариант Б: Ручная Установка PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15

# Создать базу данных
createdb risk_orchestrator
createuser riskuser -P  # Ввести пароль
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-15
sudo systemctl start postgresql

# Создать пользователя и базу
sudo -u postgres psql
postgres=# CREATE USER riskuser WITH PASSWORD 'ваш_пароль';
postgres=# CREATE DATABASE risk_orchestrator OWNER riskuser;
postgres=# \q
```

### Шаг 5: Настройка Переменных Окружения

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Редактировать .env
nano .env
```

**Обязательные настройки в `.env`:**

```bash
# Безопасность (ОБЯЗАТЕЛЬНО)
SECRET_KEY=ваш-256-битный-секретный-ключ
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# База данных (ОБЯЗАТЕЛЬНО)
DATABASE_URL=postgresql+asyncpg://riskuser:ваш_пароль@localhost:5432/risk_orchestrator

# Redis (опционально)
REDIS_URL=redis://localhost:6379/0

# Dify AI (см. раздел 4)
DIFY_API_URL=http://localhost:3001/v1
DIFY_API_KEY=ваш-dify-api-ключ

# Email/SMS (опционально)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ваш-email@gmail.com
SMTP_PASSWORD=пароль-приложения

# Окружение
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Шаг 6: Запуск Миграций БД

```bash
# Применить миграции
alembic upgrade head
```

---

## 4. Интеграция с Dify AI

### Что такое Dify?

**Dify** — это low-code платформа для создания AI-агентов. В этой системе Dify используется **только для генерации текста**:

- ✅ Ежедневные резюме для руководства
- ✅ Объяснения алертов
- ✅ Черновики писем для совета директоров

**Важно**: Dify **НЕ** занимается расчётами рисков, лимитами или интерпретацией данных.

---

### Шаг 1: Установка Dify (Self-Hosted)

**Используя Docker Compose:**

```bash
# Создать директорию для Dify
mkdir -p ~/dify
cd ~/dify

# Скачать Dify
git clone https://github.com/langgenius/dify.git
cd dify/docker

# Запустить Dify
docker-compose up -d
```

**Подождать 2-3 минуты для запуска всех сервисов, затем открыть:**
- **Dify UI**: http://localhost:3001
- **API**: http://localhost:3001/v1

---

### Шаг 2: Создание Аккаунта в Dify

1. Открыть http://localhost:3001
2. Нажать "Sign Up" (Регистрация)
3. Ввести email/пароль
4. Подтвердить email (в dev-режиме можно пропустить)

---

### Шаг 3: Настройка AI Моделей в Dify

1. **Перейти в Settings** (верхний правый угол)
2. **Нажать "Model Provider"**
3. **Добавить OpenAI API Key** (или другого провайдера):
   - Provider: OpenAI
   - API Key: `sk-...` (ваш OpenAI ключ)
   - Model: `gpt-4` или `gpt-3.5-turbo`
4. **Сохранить**

**Альтернативные провайдеры:**
- Azure OpenAI
- Anthropic Claude
- Cohere
- Локальные модели (Ollama, LM Studio)

---

### Шаг 4: Создание AI Workflows в Dify

#### Workflow 1: Ежедневное Резюме для Руководства

1. **Нажать "Create Workflow"** → "Text Generation"
2. **Название**: `Risk Executive Summary`
3. **Добавить входные переменные**:
   - `snapshot_date` (текст)
   - `var_1d_95` (число)
   - `stressed_var` (число)
   - `dv01_total` (число)
   - `capital_ratio` (число)
   - `lcr_ratio` (число)
   - `critical_alerts` (текст)
4. **Добавить LLM Node**:
   - Model: GPT-4
   - System Prompt:
     ```
     Вы — эксперт по риск-менеджменту для инвестиционной компании, регулируемой CySEC.
     Создайте краткое резюме (максимум 300 слов) для совета директоров.
     
     Сосредоточьтесь на:
     - Изменениях ключевых показателей риска
     - Критических алертах и их влиянии на бизнес
     - Статусе регуляторного соответствия
     - Практических рекомендациях
     
     Используйте профессиональный, понятный язык.
     ```
   - User Prompt:
     ```
     Дата: {{snapshot_date}}
     
     Рыночный риск:
     - VaR (1d 95%): {{var_1d_95}} EUR
     - Stressed VaR: {{stressed_var}} EUR
     - DV01: {{dv01_total}} EUR
     
     Капитал и Ликвидность:
     - Capital Ratio: {{capital_ratio}}%
     - LCR: {{lcr_ratio}}%
     
     Критические Алерты:
     {{critical_alerts}}
     
     Создайте резюме для руководства.
     ```
5. **Опубликовать Workflow**
6. **Получить API Key**: Settings → API Keys → Create → Copy

---

#### Workflow 2: Объяснение Алертов

1. **Создать новый Workflow**: `Alert Explanation`
2. **Входные переменные**:
   - `alert_type` (текст)
   - `metric_name` (текст)
   - `current_value` (число)
   - `limit_value` (число)
   - `severity` (текст)
3. **LLM Node**:
   - System Prompt:
     ```
     Вы — риск-аналитик. Объясните алерты простым языком для риск-офицеров.
     Включите:
     1. Что произошло
     2. Почему это важно
     3. Какие действия предпринять
     ```
   - User Prompt:
     ```
     Тип алерта: {{alert_type}}
     Метрика: {{metric_name}}
     Текущее значение: {{current_value}}
     Лимит: {{limit_value}}
     Критичность: {{severity}}
     
     Объясните этот алерт и порекомендуйте действия.
     ```
4. **Опубликовать** → **Скопировать API Key**

---

### Шаг 5: Настройка Dify в Risk Orchestrator

**Редактировать `.env`:**

```bash
# Конфигурация Dify
DIFY_API_URL=http://localhost:3001/v1
DIFY_API_KEY_SUMMARY=app-xxx...  # Из Workflow 1
DIFY_API_KEY_ALERT=app-yyy...    # Из Workflow 2
```

**Сервис Dify уже реализован в коде:**

Файл: `app/services/dify_service.py` (создайте его):

```python
"""
Dify AI Integration Service
Generates text using Dify workflows
"""
import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()


async def generate_executive_summary(snapshot_data: dict) -> str:
    """
    Генерирует резюме для руководства через Dify
    
    Args:
        snapshot_data: Данные риск-snapshot
    
    Returns:
        Текст резюме (до 300 слов)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.DIFY_API_URL}/workflows/run",
                headers={
                    "Authorization": f"Bearer {settings.DIFY_API_KEY_SUMMARY}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": {
                        "snapshot_date": str(snapshot_data["snapshot_date"]),
                        "var_1d_95": float(snapshot_data["var_1d_95"]),
                        "stressed_var": float(snapshot_data["stressed_var"]),
                        "dv01_total": float(snapshot_data["dv01_total"]),
                        "capital_ratio": float(snapshot_data["capital_ratio"]),
                        "lcr_ratio": float(snapshot_data["lcr_ratio"]),
                        "critical_alerts": snapshot_data["critical_alerts"],
                    },
                    "response_mode": "blocking",
                    "user": "risk-system",
                },
            )
            
            response.raise_for_status()
            result = response.json()
            
            summary = result["data"]["outputs"]["text"]
            logger.info("executive_summary_generated", length=len(summary))
            return summary
            
    except Exception as e:
        logger.error("dify_summary_failed", error=str(e))
        return f"[Ошибка генерации резюме: {str(e)}]"


async def generate_alert_explanation(alert_data: dict) -> str:
    """
    Генерирует объяснение алерта через Dify
    
    Args:
        alert_data: Данные алерта
    
    Returns:
        Текст объяснения
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.DIFY_API_URL}/workflows/run",
                headers={
                    "Authorization": f"Bearer {settings.DIFY_API_KEY_ALERT}",
                    "Content-Type": "application/json",
                },
                json={
                    "inputs": alert_data,
                    "response_mode": "blocking",
                    "user": "risk-system",
                },
            )
            
            response.raise_for_status()
            result = response.json()
            
            explanation = result["data"]["outputs"]["text"]
            logger.info("alert_explanation_generated")
            return explanation
            
    except Exception as e:
        logger.error("dify_alert_failed", error=str(e))
        return f"[Ошибка генерации объяснения: {str(e)}]"
```

---

## 5. Запуск Приложения

### Запуск Backend (API)

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить с uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API будет доступен по адресу**: http://localhost:8000

**Swagger Документация**: http://localhost:8000/docs

---

### Запуск Frontend (React)

```bash
# В новом терминале
cd risk-frontend

# Запустить dev server
npm run dev
```

**Frontend будет доступен по адресу**: http://localhost:3000

---

### Запуск полного стека через Docker Compose

```bash
# Собрать и запустить все сервисы
docker-compose up -d

# Просмотр логов
docker-compose logs -f risk-api

# Остановить все сервисы
docker-compose down
```

**Сервисы:**
- API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001

---

## 6. Руководство Пользователя

### 6.1 Первый Вход в Систему

**Создание Admin Аккаунта** (вручную в БД):

```sql
-- Подключиться к БД
psql -U riskuser -d risk_orchestrator

-- Создать пользователя
INSERT INTO users (username, email, hashed_password, role, is_active, created_at)
VALUES (
  'admin',
  'admin@yourcompany.com',
  '$2b$12$...', -- Используйте bcrypt для хеширования пароля
  'ADMIN',
  true,
  NOW()
);
```

**Генерация Hash Пароля:**

```python
# В Python консоли
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(pwd_context.hash("ваш_пароль"))
```

**Вход:**
1. Открыть http://localhost:3000
2. Username: `admin`
3. Password: `ваш_пароль`

---

### 6.2 Создание Портфелей

**Через API:**

```bash
curl -X POST http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer ВАШ_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_name": "Cyprus Main Fund",
    "entity_id": 1,
    "base_currency": "EUR",
    "is_active": true
  }'
```

**Через Web UI:**
1. Dashboard → "Portfolios"
2. Нажать "Create Portfolio"
3. Заполнить поля
4. Сохранить

---

### 6.3 Загрузка Позиций

**Формат CSV** (`positions.csv`):

```csv
portfolio_name,instrument_type,isin,notional,clean_price,coupon_rate,maturity_date
Cyprus Main Fund,BOND,US912828Z230,1000000,98.5,0.025,2030-12-31
Cyprus Main Fund,BOND,DE0001102408,500000,102.0,0.035,2028-06-30
```

**Загрузка через API:**

```bash
curl -X POST http://localhost:8000/api/v1/batch/upload-positions \
  -H "Authorization: Bearer ВАШ_JWT_TOKEN" \
  -F "file=@positions.csv"
```

---

### 6.4 Запуск Расчётов Рисков

**On-Demand Расчёт:**

```bash
curl -X POST http://localhost:8000/api/v1/risk/calculate \
  -H "Authorization: Bearer ВАШ_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "as_of_date": "2024-12-01",
    "calculation_type": "FULL"
  }'
```

**Автоматический Ночной Batch:**
- Запускается автоматически в **00:00 UTC**
- Настроен в `app/scheduler/jobs.py`

---

### 6.5 Просмотр Risk Dashboard

1. **Открыть Dashboard**: http://localhost:3000
2. **Выбрать Портфель**: Dropdown сверху
3. **Просмотр Метрик**:
   - VaR (1d 95%)
   - DV01
   - Capital Ratio
   - LCR
   - Активные Алерты
4. **Проверка Графиков**:
   - VaR Time Series (30 дней)
   - Capital Adequacy Breakdown
5. **Просмотр Таблицы Алертов**:
   - Фильтр по критичности
   - Подтверждение алертов

---

### 6.6 Генерация PDF Отчётов

**Ручная Генерация:**

```bash
curl -X POST http://localhost:8000/api/v1/reports/pdf/generate \
  -H "Authorization: Bearer ВАШ_JWT_TOKEN" \
  -d '{"report_date": "2024-12-01"}'
```

**Автоматические Ежедневные Отчёты:**
- Генерируются в **01:00 UTC** ежедневно
- Сохраняются в `/var/risk-reports/`
- Включают:
  - Executive Summary (от Dify)
  - Графики VaR
  - Критические Алерты
  - Топ-5 новостных событий

---

### 6.7 Установка Лимитов Рисков

**Создание Лимита:**

```bash
curl -X POST http://localhost:8000/api/v1/limits \
  -H "Authorization: Bearer ВАШ_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "limit_type": "VAR_1D_95",
    "limit_value": 100000,
    "warning_threshold": 0.8,
    "critical_threshold": 0.95,
    "is_active": true
  }'
```

**Типы Лимитов:**
- `VAR_1D_95` - Value at Risk (1-дневный, 95%)
- `STRESSED_VAR` - Stressed VaR
- `DV01` - Процентная чувствительность
- `CAPITAL_RATIO` - Регуляторный капитал
- `LCR` - Коэффициент покрытия ликвидностью

---

### 6.8 Управление Алертами

**Просмотр Активных Алертов:**

```bash
curl http://localhost:8000/api/v1/alerts?acknowledged=false \
  -H "Authorization: Bearer ВАШ_JWT_TOKEN"
```

**Подтверждение Алерта:**

```bash
curl -X POST http://localhost:8000/api/v1/alerts/123/acknowledge \
  -H "Authorization: Bearer ВАШ_JWT_TOKEN"
```

**Уровни Критичности:**
- 🟢 **GREEN**: Всё в порядке
- 🟡 **YELLOW**: Предупреждение (80% лимита)
- 🔴 **RED**: Критично (95% лимита)
- 🔴 **CRITICAL**: Превышение (>100% лимита)

---

## 7. Документация API

### Аутентификация

**Получение JWT Token:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "ваш_пароль"
  }'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Использование Token в Запросах:**

```bash
curl http://localhost:8000/api/v1/portfolios \
  -H "Authorization: Bearer ВАШ_JWT_TOKEN"
```

---

### Основные Endpoints

**Health Check:**
```
GET /api/v1/health
```

**Портфели:**
```
GET    /api/v1/portfolios           # Список всех
POST   /api/v1/portfolios           # Создать
GET    /api/v1/portfolios/{id}      # Получить один
PUT    /api/v1/portfolios/{id}      # Обновить
DELETE /api/v1/portfolios/{id}      # Удалить
```

**Расчёты Рисков:**
```
POST   /api/v1/risk/calculate       # On-demand расчёт
GET    /api/v1/risk_snapshots       # Список snapshots
GET    /api/v1/risk_snapshots/{id}  # Детали snapshot
```

**Алерты:**
```
GET    /api/v1/alerts               # Список алертов
POST   /api/v1/alerts/{id}/acknowledge
```

**Отчёты:**
```
POST   /api/v1/reports/pdf/generate
GET    /api/v1/reports/pdf/download?report_date=2024-12-01
```

**Мониторинг:**
```
GET    /api/v1/metrics              # Prometheus метрики
GET    /api/v1/audit                # Аудит (только admin)
```

**Полная Документация API:**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 8. Решение Проблем

### Проблема: Ошибка Подключения к БД

**Ошибка:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Решение:**
1. Проверить, что PostgreSQL запущен:
   ```bash
   docker ps | grep postgres
   # или
   pg_isready -h localhost -p 5432
   ```
2. Проверить `DATABASE_URL` в `.env`
3. Проверить настройки firewall

---

### Проблема: Dify API Возвращает 401 Unauthorized

**Ошибка:**
```
{"detail": "Invalid API key"}
```

**Решение:**
1. Проверить, что API key в `.env` совпадает с Dify workflow
2. Убедиться, что Dify запущен: http://localhost:3001
3. Пересоздать API key в Dify при необходимости

---

### Проблема: Frontend Не Может Подключиться к Backend

**Ошибка:**
```
Network Error: Failed to fetch
```

**Решение:**
1. Проверить, что backend запущен на порту 8000
2. Проверить CORS настройки в `.env`:
   ```bash
   CORS_ORIGINS=http://localhost:3000
   ```
3. Проверить proxy настройки в `vite.config.ts`

---

### Проблема: Тесты Падают

**Ошибка:**
```
ERROR: could not connect to database
```

**Решение:**
1. Создать тестовую базу:
   ```bash
   createdb risk_orchestrator_test
   ```
2. Запустить тесты с правильным env:
   ```bash
   export DATABASE_URL=postgresql+asyncpg://riskuser:password@localhost:5432/risk_orchestrator_test
   pytest
   ```

---

### Проблема: Docker Compose Не Запускается

**Ошибка:**
```
Error: port 5432 already in use
```

**Решение:**
1. Остановить локальный PostgreSQL:
   ```bash
   brew services stop postgresql@15
   # или
   sudo systemctl stop postgresql
   ```
2. Или изменить порт в `docker-compose.yml`:
   ```yaml
   ports:
     - "5433:5432"  # Использовать 5433 на хосте
   ```

---

## Поддержка и Документация

- **GitHub Issues**: Сообщения об ошибках и запросы функций
- **API Docs**: http://localhost:8000/docs
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3001

---

## Best Practices по Безопасности

1. **Изменить дефолтные пароли** в production
2. **Использовать сильный SECRET_KEY** (256-bit случайный)
3. **Включить HTTPS** с Let's Encrypt
4. **Ограничить доступ к БД** только localhost или VPN
5. **Использовать Vault** для секретов в production
6. **Включить rate limiting** на API endpoints
7. **Регулярно проверять audit logs**
8. **Обновлять зависимости** (`pip install --upgrade`)

---

## Следующие Шаги

1. ✅ Установить и настроить Dify
2. ✅ Запустить миграции БД
3. ✅ Создать admin пользователя
4. ✅ Загрузить тестовые позиции
5. ✅ Запустить первый расчёт рисков
6. ✅ Сгенерировать PDF отчёт
7. ✅ Просмотреть алерты и установить лимиты
8. ✅ Настроить email/SMS уведомления

**Система готова к production!** 🚀

---

## Примеры Использования Dify в Системе

### Пример 1: Автоматическое Резюме в PDF Отчёте

```python
# В app/services/pdf_report.py
from app.services.dify_service import generate_executive_summary

async def generate_daily_pdf(session, report_date):
    # ... загрузка данных ...
    
    # Подготовка данных для Dify
    snapshot_data = {
        "snapshot_date": str(report_date),
        "var_1d_95": snapshot.var_1d_95,
        "stressed_var": snapshot.stressed_var,
        "dv01_total": snapshot.dv01_total,
        "capital_ratio": snapshot.capital_ratio,
        "lcr_ratio": snapshot.lcr_ratio,
        "critical_alerts": format_critical_alerts(alerts),
    }
    
    # Генерация резюме через Dify
    executive_summary = await generate_executive_summary(snapshot_data)
    
    # Вставка в PDF
    html_content = f"""
    <div class="executive-summary">
        <h2>Executive Summary</h2>
        <p>{executive_summary}</p>
    </div>
    """
    # ... остальной код PDF ...
```

### Пример 2: Объяснение Алерта при Создании

```python
# В app/services/alert_engine.py
from app.services.dify_service import generate_alert_explanation

async def create_alert_with_explanation(session, alert_data):
    # Создать алерт
    alert = Alert(**alert_data)
    session.add(alert)
    
    # Сгенерировать объяснение через Dify
    explanation = await generate_alert_explanation({
        "alert_type": alert.alert_type,
        "metric_name": alert.metric_name,
        "current_value": alert.current_value,
        "limit_value": alert.limit_value,
        "severity": alert.severity,
    })
    
    # Сохранить объяснение
    alert.ai_explanation = explanation
    await session.commit()
    
    return alert
```

### Пример 3: API Endpoint для Генерации Резюме

```python
# В app/api/reports.py
from app.services.dify_service import generate_executive_summary

@router.post("/reports/summary")
async def get_executive_summary(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(auth_bearer),
):
    """Генерирует Executive Summary для snapshot"""
    snapshot = await db.get(RiskSnapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(404, "Snapshot not found")
    
    snapshot_data = {
        "snapshot_date": str(snapshot.snapshot_date),
        "var_1d_95": snapshot.var_1d_95,
        "stressed_var": snapshot.stressed_var,
        # ... остальные поля ...
    }
    
    summary = await generate_executive_summary(snapshot_data)
    
    return {"summary": summary, "snapshot_id": snapshot_id}
```

---

**Готово! Система полностью документирована и готова к использованию.** 📚
