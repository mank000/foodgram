
# Foodgram

Foodgram — это приложение, которое позволяет пользователям публиковать рецепты, подписываться на обновления от других авторов и сохранять рецепты в избранное. Кроме того, список покупок поможет составить список необходимых продуктов для приготовления выбранных блюд и отправить PDF-файл с ингридиентами.

### Как развернуть на удаленном сервере?

Для начала необходимо заполнить файл .env
Структура выглядит так:

``
POSTGRES_DB=
``
``
POSTGRES_USER=
``
``
POSTGRES_PASSWORD=
``
``
DB_NAME=
``
``
DB_HOST=
``
``
DB_PORT=
``
``
SECRET_KEY=
``
``
DEBUG=
``

Далее необходимо использовать Docker из корневой папки:
``
sudo docker compose up
``
Далее необходимо загрузить список ингредиентов:
``
python manage.py upload_data
``

Далее, вы сможете зайти на сайт по адресу http://localhost:8000

Ссылка на сайт: https://manko.hopto.org/
```
username: reviewer
email: reviewer@mail.ru
password: reviewer12
```

## Стек
- python==3.9
- Django==3.2.15
- djangorestframework==3.12.4
- Pillow==9.3.0
- reportlab==4.2.2
- psycopg2-binary==2.9.3
## Автор
Артем Козьмин