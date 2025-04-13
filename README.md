# Foodgram - Продуктовый помощник

## Описание проекта
Foodgram - это веб-приложение для публикации кулинарных рецептов. Пользователи могут:
- Создавать и публиковать рецепты
- Добавлять рецепты в избранное
- Подписываться на других авторов
- Формировать список покупок для выбранных рецептов

## Технологии
Django, DRF, PostgreSQL, Docker, Nginx, GitHub Actions (CI/CD)

## Как запустить проект

### Требования
- Docker
- Docker Compose

### Инструкция по развертыванию

1. Клонируйте репозиторий:
git clone https://github.com/ваш-репозиторий/foodgram.git
cd foodgram

2. Настройка переменных окружения:
Создайте файл .env в папке infra/ и заполните по примеру:
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

SECRET_KEY=ваш-secret-key
DEBUG=False  # Для продакшена False
ALLOWED_HOSTS=ваш-домен,localhost,127.0.0.1

3. Запуск Docker-контейнеров:
docker compose up -d --build

4. Миграции и суперпользователь:
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser

5. Сбор статики:
docker compose exec backend python manage.py collectstatic

## Примеры запросов:
Получить список всех рецептов:

'GET /api/recipes/'

Добавить новый рецепт:

'POST /api/recipes/create/'

'{'
  '"name": "Омлет",'
  '"tags": [1],'
  '"ingredients": [1],'
  '"image": "string"'
  '"coocking_time": "integer"'
  '"text": "text"'
'}'


## Информация об авторе:
Валентин Смирнов. Студент Яндекс Практикума.