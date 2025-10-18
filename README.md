![Превью](assets/header.png)

# HR Platform

![Backend FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white) ![Frontend Angular](https://img.shields.io/badge/Frontend-Angular-dd0031?logo=angular&logoColor=white) ![Database PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white) ![Reverse Proxy Nginx](https://img.shields.io/badge/Proxy-Nginx-009639?logo=nginx&logoColor=white) ![Docker Compose](https://img.shields.io/badge/Orchestration-Docker%20Compose-2496ed?logo=docker&logoColor=white) ![MIT License](https://img.shields.io/badge/License-MIT-yellow)

> 💼 Готовое решение для управления наймом, стажировками и вакансиями: веб-приложение для HR-специалистов, соискателей и ВУЗов!

## 📚 Оглавление
- [Быстрый старт (демо)](#⚡️-быстрый-старт-демо)
- [Требования](#🧩-требования)
- [Структура репозитория](#🗂️-структура-репозитория)
- [Настройка backend](#🛠️-настройка-backend)
  - [Конфигурационный файл `config.yaml`](#📄-конфигурационный-файл-configyaml)
  - [Переменные окружения](#🌐-переменные-окружения)
  - [Использование внешней базы данных](#🗄️-использование-внешней-базы-данных)
  - [Хранилище медиа-файлов](#🗃️-хранилище-медиа-файлов)
- [Настройка frontend](#🎨-настройка-frontend)
  - [Готовый собранный пакет](#📦-готовый-собранный-пакет)
  - [Сборка из исходников](#🛠️-сборка-из-исходников)
- [Полезные команды](#🧰-полезные-команды)

## ⚡️ Быстрый старт (демо)
Проект уже полностью готов к запуску в демонстрационном режиме. Вся инфраструктура поднимается одной командой через Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

После успешного старта:
- фронтенд доступен на `http://localhost:8180`
- API работает по адресу `http://localhost:8180/api`
- статика и загруженные файлы доступны по `http://localhost:8180/backend-media/`

По умолчанию backend запускается в режиме `demo_mode=true`: при каждом старте пересоздаётся схема БД и загружаются демонстрационные данные, включая администратора. Это поведение можно отключить в конфигурации (см. ниже).

Также некоторое время доступен уже развернутый [демо-стенд](https://hackathon.silkslime.ru/), который является полной копией приложения, запущенного по данной инструкции.

## 🧩 Требования
- Docker 24+
- Docker Compose v2
- Свободные порты `8180` (настраивается)
- Не менее 2 ГБ свободного места на диске для образов и данных

## 🗂️ Структура репозитория
```
compose.yml         # docker-compose стек (PostgreSQL, backend, nginx)
backend/            # сервис FastAPI + конфигурация
frontend/           # Angular-приложение и артефакты сборки
nginx/              # конфигурация reverse-proxy
.env.example        # пример переменных окружения для docker compose
```

## 🛠️ Настройка backend
Backend построен на FastAPI и читает конфигурацию из трёх источников (в порядке убывания приоритета):
1. переменные окружения с префиксом `APP_`
2. файл `.env` в корне каталога backend (поддерживает тот же префикс)
3. YAML-файл `config.yaml`

Все значения приводятся к модели `Config` (`backend/config/config.py`) с вложенными секциями.

### 📄 Конфигурационный файл `config.yaml`
Базовый файл поставляется вместе с проектом (`backend/config.yaml`) и содержит следующие параметры:

| Путь                | Описание |
|---------------------|----------|
| `env`               | Название окружения (`dev`, `stage`, `prod`) — влияет на логику, привязанную к конкретной среде (например, можно использовать в своих условиях). |
| `demo_mode`         | Если `true`, при запуске база очищается и наполняется демо-данными. Для рабочих окружений выставьте `false`. |
| `postgres.*`        | Настройки подключения к базе данных PostgreSQL: `host`, `port`, `database`, `username`, `password`, `debug`. |
| `security.jwt_secret` | Секрет для подписи JWT-токенов. Обязательно замените на уникальное значение в продакшене. |
| `security.access_token_expire_minutes` | Время жизни access-токена в минутах. |
| `security.refresh_token_expire_minutes` | Время жизни refresh-токена в минутах. |
| `superuser.email`   | Email суперпользователя, создаваемого/обновляемого при старте. |
| `superuser.password`| Пароль суперпользователя. |
| `storage.media_root` | Путь к директории хранения загруженных файлов. |
| `storage.public_path_prefix` | URL-префикс, по которому Nginx отдаёт медиа backend (`/backend-media`). |
| `analytics.cache_ttl_seconds` | Время жизни кэша статистики (в секундах). Значение `0` отключает кэширование. |

Для использования кастомного файла конфигурации достаточно смонтировать его при запуске контейнера backend:
```yaml
services:
  backend:
    volumes:
      - ./my-config.yaml:/app/config.yaml:ro
```

### 🌐 Переменные окружения
Переменные окружения перекрывают значения из `config.yaml`. Все ключи начинаются с префикса `APP_`, вложенность разделяется подчёркиваниями и переводится в нижний регистр.

Основные переменные:

| Переменная | Значение по умолчанию | Описание |
|------------|-----------------------|----------|
| `APP_ENV` | `dev` | Название окружения. |
| `APP_DEMO_MODE` | `true` | Управляет режимом демо-данных. |
| `APP_POSTGRES_HOST` | `localhost` | Адрес сервера PostgreSQL. |
| `APP_POSTGRES_PORT` | `5432` | Порт PostgreSQL. |
| `APP_POSTGRES_DATABASE` | `appdb` | Имя базы данных. |
| `APP_POSTGRES_USERNAME` | `user` | Пользователь БД. |
| `APP_POSTGRES_PASSWORD` | `pass` | Пароль пользователя БД. |
| `APP_POSTGRES_DEBUG` | `true` | Включает SQLAlchemy echo. |
| `APP_SECURITY_JWT_SECRET` | `change-me` | Секрет JWT. |
| `APP_SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Срок жизни access-токена. |
| `APP_SECURITY_REFRESH_TOKEN_EXPIRE_MINUTES` | `10080` | Срок жизни refresh-токена. |
| `APP_SUPERUSER_EMAIL` | `admin@example.com` | Email суперпользователя. |
| `APP_SUPERUSER_PASSWORD` | `admin123` | Пароль суперпользователя. |
| `APP_STORAGE_MEDIA_ROOT` | `./backend_media` | Каталог хранения медиа в контейнере. |
| `APP_STORAGE_PUBLIC_PATH_PREFIX` | `backend-media` | URL-префикс для раздачи медиа. |
| `APP_ANALYTICS_CACHE_TTL_SECONDS` | `60` | TTL кэша аналитических эндпоинтов. `0` — отключить кэширование. |
| `APP_ROOT_PATH` | пусто | Префикс для FastAPI (используется Nginx, см. compose). |

Переменные, относящиеся к Docker Compose (без префикса `APP_`), описаны в `.env.example` и влияют на инфраструктуру (например, параметры подключения к PostgreSQL внутри кластера).

### 🗄️ Использование внешней базы данных
Чтобы подключить внешний PostgreSQL, настройте переменные окружения в `.env` перед запуском:
```bash
POSTGRES_HOST=db.example.com
POSTGRES_PORT=5432
POSTGRES_USERNAME=myuser
POSTGRES_PASSWORD=mypass
POSTGRES_DATABASE=hr
```

Затем поднимите стек без встроенного сервиса `postgres` или исключите этот сервис из `compose.yml`:
```bash
docker compose up --build backend nginx
```

### 🗃️ Хранилище медиа-файлов
По умолчанию медиа сохраняются в volume `backend-media-storage`, который шарится между backend и Nginx. Для использования внешнего хранилища смонтируйте нужную директорию в контейнер backend и обновите `APP_STORAGE_MEDIA_ROOT`:
```yaml
services:
  backend:
    volumes:
      - /srv/hr/media:/var/lib/hr/backend-media
    environment:
      - APP_STORAGE_MEDIA_ROOT=/var/lib/hr/backend-media
  nginx:
    volumes:
      - /srv/hr/media:/var/lib/hr/backend-media:ro
```

## 🎨 Настройка frontend
Фронтенд — это Angular-приложение, уже собранное в директорию `frontend/dist/hakaton/browser`. Nginx раздаёт статический контент из этой папки, поэтому дополнительных действий не требуется.

### 📦 Готовый собранный пакет
Собранный бандл не привязан к конкретному домену: Nginx проксирует API по `/api`, поэтому можно развернуть фронтенд на любом хосте c любым доменным именем или IP адресом.

### 🛠️ Сборка из исходников
Если нужно пересобрать бандл фронтенда (необходимо предварительно установить [Node](https://nodejs.org/en/download) версии v22.18.0 или любой совместимой):
```bash
cd frontend
npm install
npm run build   # или ng build, если установлен @angular/cli глобально
```
Сборка появится в `frontend/dist/hakaton/browser`. Убедитесь, что Nginx указывает на эту директорию.

## 🧰 Полезные команды
- `docker compose up --build` — запустить весь стек в foreground-режиме
- `docker compose up -d` — запустить в фоне
- `docker compose logs -f backend` — посмотреть логи backend
- `docker compose down -v` — остановить и удалить контейнеры вместе с томами