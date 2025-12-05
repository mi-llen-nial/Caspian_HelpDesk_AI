# Caspian_HelpDeskAI

ИИ Help Desk сервис для автоматизации службы поддержки: принимает обращения из Telegram/портала/почты, автоматически классифицирует их, предлагает ответы из базы знаний, может авто-закрывать простые тикеты и показывает метрики в веб-панели.

## Архитектура
- Backend: FastAPI, SQLAlchemy, Pydantic v2, httpx, aiogram (опционально для Telegram-бота). Встроенный CORS и раздача собранного фронтенда.
- AI-интеграция: DeepSeek API (OpenAI-совместимый). При отсутствии ключа используется безопасный фолбэк без внешних запросов.
- DB: SQLite по умолчанию, можно переключить на Postgres через `DATABASE_URL`.
- Frontend: React 18 + Vite, SPA с роутером. Собранный `frontend/dist` автоматически раздается FastAPI.

### Визуальная карта модулей
| Слой       | Ключевые компоненты                                    | Описание |
|-----------|--------------------------------------------------------|----------|
| API       | `tickets`, `faq`, `analytics`                          | REST-ручки для CRUD тикетов/FAQ и метрик |
| AI        | `classifier`, `answer_generator`, `summarizer`         | Классификация, короткий ответ, саммари (фолбэк без ключа) |
| Services  | `routing_service`, `faq_service`, `analytics_service`  | Бизнес-логика тикета, FAQ-подбор, вычисление метрик |
| Data      | `ticket`, `message`, `faq`, `department`, `model_log`  | SQLAlchemy-модели БД |
| Integrations | `telegram_bot`, `telegram_sender`                   | Приём/отправка сообщений Telegram |
| Frontend  | `Dashboard`, `Leads`, `Ticket details`, `FAQ`          | SPA-страницы с таблицами и графиками |

## Основные возможности
- Создание тикетов из UI и внешних источников (`/api/v1/tickets/external`).
- Авто-классификация (категория, департамент, приоритет, язык, auto_resolvable) и логирование ответов модели.
- Авто-ответ и авто-закрытие, если уверенность модели >= 0.8 и есть подходящая статья FAQ.
- Управление базой знаний (CRUD для FAQ) через UI и REST.
- Просмотр тикетов и переписки, отправка ответов оператором (опционально отправляется в Telegram).
- Метрики дашборда: всего тикетов, новые за сегодня, % авто-закрытий, точность классификации.

### Таблица метрик дашборда
| Метрика | Источник | Расчёт |
|---------|----------|--------|
| total_tickets | БД (`tickets`) | COUNT(*) |
| new_today | БД (`tickets`) | COUNT(created_at >= today) |
| auto_closed_percent | БД (`tickets`) | auto_closed / total * 100 |
| avg_first_response_minutes | БД (`tickets`) | Среднее (closed_at - created_at) для auto_closed |
| classification_accuracy | `model_logs` | (all - corrected) / all * 100 |

### Визуализации на фронтенде
- Карточки: ключевые метрики overview.
- Бар-чарты: распределение тикетов по статусам, каналам, приоритетам.
- Таблица: последние тикеты с приоритетами/статусами.

## Быстрый старт (локально)
### 1) Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Создаст таблицы и запустит API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend (в dev-режиме)
```powershell
cd frontend
npm install
npm run dev
# Vite поднимет фронт на 5173 и прокинет запросы /api на 8000
```

### 3) Сборка фронтенда под prod
```powershell
cd frontend
npm install
npm run build
# Папка dist/ будет автоматически отдаваться FastAPI из backend/app/main.py
```

## Настройки окружения (`backend/.env`)
Пример переменных:
```
APP_NAME=HelpDeskAI
API_V1_PREFIX=/api/v1

# DB: для Postgres используйте postgres://user:pass@host:5432/dbname
DATABASE_URL=sqlite:///./helpdesk.db

# DeepSeek (опционально)
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Telegram (опционально для отправки/бота)
TELEGRAM_BOT_TOKEN=123:abc

# CORS
ALLOWED_ORIGINS=["*"]
```

Все переменные описаны в `app/core/config.py`. Если `DEEPSEEK_API_KEY` не задан, сервис использует фолбэк-эвристику без внешних вызовов.

### Таблица переменных окружения
| Переменная | Назначение | Значение по умолчанию |
|------------|------------|-----------------------|
| APP_NAME | Название приложения | HelpDeskAI |
| API_V1_PREFIX | Префикс REST | /api/v1 |
| DATABASE_URL | Строка подключения | sqlite:///./helpdesk.db |
| DEEPSEEK_API_KEY | Ключ DeepSeek | пусто (фолбэк) |
| DEEPSEEK_BASE_URL | База DeepSeek | https://api.deepseek.com |
| DEEPSEEK_MODEL | Модель DeepSeek | deepseek-chat |
| TELEGRAM_BOT_TOKEN | Токен бота | пусто |
| ALLOWED_ORIGINS | CORS список | ["*"] |

## Работа с данными
- При старте `app.main` вызывает `Base.metadata.create_all`, создавая таблицы в БД.
- Основные таблицы: `tickets`, `messages`, `departments`, `faq`, `model_logs`.
- Статусы тикетов: `new`, `in_progress`, `closed`, `auto_closed`.

## REST API (основные ручки)
| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/tickets` | Список тикетов, фильтры `status`, `channel` |
| POST | `/api/v1/tickets` | Создать тикет с авто-классификацией |
| POST | `/api/v1/tickets/external` | Создать тикет внешней системой, без AI |
| GET | `/api/v1/tickets/{id}` | Детали тикета + сообщения |
| POST | `/api/v1/tickets/{id}/messages` | Добавить сообщение (agent/customer/ai) |
| GET | `/api/v1/faq` | Список FAQ, фильтр `language` |
| POST | `/api/v1/faq` | Создать FAQ |
| PUT | `/api/v1/faq/{id}` | Обновить FAQ |
| DELETE | `/api/v1/faq/{id}` | Удалить FAQ |
| GET | `/api/v1/analytics/overview` | Метрики для дашборда |

## AI-логика
- Классификация: `app/ai/classifier.py` вызывает DeepSeek (`chat_json`) с системной подсказкой. Возвращает `category_code`, `department_code`, `priority`, `language`, `auto_resolvable`, `confidence`. Без ключа — фолбэк в категорию GENERAL/IT-SERVICE, P3.
- Авто-ответ: `app/ai/answer_generator.py` формирует короткий ответ (3–4 предложения) на выбранном языке, может опираться на сниппет из FAQ.
- Резюме: `app/ai/summarizer.py` (пока не выведено в UI), коротко суммирует переписку.
- Логи моделей сохраняются в `model_logs` (см. `ModelLog`).

## Бизнес-поток тикета
1. UI или Telegram создает тикет (POST `/tickets`).
2. `routing_service.process_new_ticket` вызывает классификатор и записывает первое сообщение клиента.
3. Если `auto_resolvable` и `confidence >= 0.8`, берется подходящая FAQ-статья (`faq_service.get_best_match`), генерируется ответ, тикет переводится в `auto_closed`, добавляется AI-сообщение.
4. Оператор может открыть тикет, написать ответ (`/tickets/{id}/messages`) — для Telegram-тикетов сообщение отправится в чат через `telegram_sender` (если настроен токен).

### Таблица статусов и приоритетов
| Статус | Назначение |
|--------|------------|
| new | Новый тикет |
| in_progress | В работе |
| closed | Закрыт |
| auto_closed | Закрыт автоматически AI |

| Приоритет | Описание |
|-----------|----------|
| P1 | Критичный |
| P2 | Высокий |
| P3 | Средний |
| P4 | Низкий |

## Веб-интерфейс (React)
- `Dashboard`: метрики из `/analytics/overview`.
- `Leads`: список тикетов, фильтр по статусу, поиск, создание лида вручную, переход в карточку.
- `Ticket details`: переписка, отправка ответа, панель AI (классификация, приоритет, статус).
- `FAQ`: CRUD по статьям базы знаний, признак авто-решения.
- Конфиг API-базы: `src/api.js` строит URL из origin, меняя порт на 8000.

## Telegram-бот (опционально)
- Файл: `app/integrations/telegram_bot.py` (aiogram v3).
- Команды: `/start` предлагает выбрать категорию, далее принимает текст обращения и создает тикет через ту же логику, что UI.
- Запуск (после настройки `TELEGRAM_BOT_TOKEN`):
```powershell
cd backend
.\.venv\Scripts\activate
python -m app.integrations.telegram_bot
```

## Зависимости проекта

### Backend (requirements.txt)
| Пакет | Версия | Назначение |
|-------|--------|-----------|
| fastapi | 0.103.2 | Web-фреймворк |
| uvicorn[standard] | 0.23.2 | ASGI-сервер |
| sqlalchemy | 1.4.52 | ORM для БД |
| pydantic | ≥2.0.0,<3.0.0 | Валидация данных |
| pydantic-settings | ≥2.0.0,<3.0.0 | Управление конфигурацией |
| httpx | 0.27.0 | HTTP-клиент для API-вызовов |
| psycopg2-binary | ≥2.9.0,<3.0.0 | Драйвер PostgreSQL |
| aiogram | ≥3.0.0,<4.0.0 | Библиотека Telegram-бота |

### Frontend (package.json)
| Пакет | Версия | Назначение |
|-------|--------|-----------|
| react | ^18.3.1 | UI-фреймворк |
| react-dom | ^18.3.1 | Рендеринг DOM |
| react-router-dom | ^6.28.0 | Маршрутизация |
| vite | ^5.4.0 | Сборка и dev-сервер |
| @vitejs/plugin-react-swc | ^3.7.0 | SWC-трансформер для React |

## Структура БД

### Таблица tickets
| Поле | Тип | Описание |
|------|-----|---------|
| id | INTEGER | Первичный ключ |
| subject | VARCHAR(255) | Тема тикета |
| description | TEXT | Описание проблемы |
| channel | VARCHAR(50) | Источник: telegram/email/portal/phone |
| language | VARCHAR(10) | Язык: ru/en/etc |
| customer_email | VARCHAR(255) | Email клиента |
| customer_username | VARCHAR(255) | Username клиента |
| external_user_id | VARCHAR(100) | ID из внешней системы (Telegram, etc) |
| request_type | VARCHAR(50) | Тип: difficulty/proposal/job/other |
| category_code | VARCHAR(100) | Категория проблемы |
| priority | VARCHAR(10) | P1/P2/P3/P4 |
| status | VARCHAR(50) | new/in_progress/closed/auto_closed |
| department_id | INTEGER (FK) | Связь на department |
| auto_closed_by_ai | BOOLEAN | Закрыто ли автоматически |
| created_at | DATETIME | Дата создания |
| updated_at | DATETIME | Последнее обновление |
| closed_at | DATETIME | Дата закрытия |

### Таблица messages
| Поле | Тип | Описание |
|------|-----|---------|
| id | INTEGER | Первичный ключ |
| ticket_id | INTEGER (FK) | Связь на ticket |
| role | VARCHAR(20) | customer/agent/ai |
| content | TEXT | Текст сообщения |
| created_at | DATETIME | Дата сообщения |

### Таблица faq
| Поле | Тип | Описание |
|------|-----|---------|
| id | INTEGER | Первичный ключ |
| title | VARCHAR(255) | Заголовок статьи |
| content | TEXT | Содержание |
| language | VARCHAR(10) | Язык статьи |
| category_code | VARCHAR(100) | Категория |
| auto_resolvable | BOOLEAN | Может ли решить тикет автоматически |
| created_at | DATETIME | Дата создания |
| updated_at | DATETIME | Последнее обновление |

### Таблица departments
| Поле | Тип | Описание |
|------|-----|---------|
| id | INTEGER | Первичный ключ |
| name | VARCHAR(255) | Название отдела |
| code | VARCHAR(50) | Код отдела |
| email | VARCHAR(255) | Email отдела |
| created_at | DATETIME | Дата создания |

### Таблица model_logs
| Поле | Тип | Описание |
|------|-----|---------|
| id | INTEGER | Первичный ключ |
| ticket_id | INTEGER (FK) | Связь на ticket |
| response | JSON | Полный ответ модели |
| corrected | BOOLEAN | Исправлен ли ответ оператором |
| created_at | DATETIME | Дата логирования |

## Категории и каналы

### Доступные каналы приема
| Канал | Описание | Интеграция |
|-------|---------|-----------|
| portal | Веб-портал | React UI, REST API |
| telegram | Telegram-бот | aiogram, REST API |
| email | Email | Интеграция (в планах) |
| phone | Телефонная система | Интеграция (в планах) |

### Типы запросов (request_type)
| Тип | Описание |
|-----|---------|
| difficulty | Техническая проблема |
| proposal | Предложение/пожелание |
| job | Заказ работы |
| other | Прочее |

## Примеры API-запросов

### Создание тикета
```bash
POST /api/v1/tickets
Content-Type: application/json

{
  "subject": "Не работает авторизация",
  "description": "При входе выдает ошибку 401",
  "channel": "portal",
  "language": "ru",
  "customer_email": "user@example.com",
  "customer_username": "john_doe",
  "request_type": "difficulty"
}
```

### Получение списка тикетов с фильтрацией
```bash
GET /api/v1/tickets?status=in_progress&channel=telegram&language=ru
```

### Добавление сообщения в тикет
```bash
POST /api/v1/tickets/1/messages
Content-Type: application/json

{
  "role": "agent",
  "content": "Спасибо за обращение. Мы разбираемся в проблеме."
}
```

### Получение аналитики
```bash
GET /api/v1/analytics/overview?days=7
```

### Работа с FAQ
```bash
# Создание статьи
POST /api/v1/faq
{
  "title": "Как сбросить пароль?",
  "content": "Нажмите 'Забыли пароль?' на странице входа...",
  "language": "ru",
  "category_code": "ACCOUNT",
  "auto_resolvable": true
}

# Обновление статьи
PUT /api/v1/faq/1
{
  "title": "Как сбросить пароль (обновлено)?",
  "content": "..."
}

# Удаление
DELETE /api/v1/faq/1
```

## Параметры классификации AI

### Уровни уверенности (confidence)
| Диапазон | Действие | Описание |
|----------|---------|---------|
| 0.0–0.5 | Требует оператора | Низкая уверенность, передать специалисту |
| 0.5–0.8 | Подсказка оператору | Предложить рекомендуемый ответ |
| 0.8–1.0 | Авто-закрытие | Закрыть автоматически, если есть FAQ |

### Коды приоритета
| Код | Время отклика | SLA  | Примеры |
|-----|----------------|------------|---------|
| P1 | Немедленно | 15 | Система неработающая, критическая потеря данных |
| P2 | Срочно | 60 | Существенное снижение функциональности |
| P3 | Стандартно | 480 | Обычная ошибка, не влияет на основной процесс |
| P4 | В удобное время | 1440 | Вопрос, пожелание, информационный запрос |

## Полезные команды

### Запуск проекта
```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (в другом терминале)
cd frontend
npm install
npm run dev -- --host
```

### Опубликование в production
```powershell
# Собрать frontend
cd frontend
npm run build

# Запустить backend с собранным фронтом
cd ../backend
.\.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Интеграция с Telegram
```powershell
# Запуск Telegram-бота
cd backend
.\.venv\Scripts\activate
python -m app.integrations.telegram_bot
```

### Отладка и администрирование
```powershell
# Просмотр логов
Get-Content helpdesk.log -Tail 50

# Проверка статуса API
curl http://localhost:8000/docs

# Очистка БД (осторожно!)
Remove-Item helpdesk.db
```
