# Foodgram
Foodgram - онлайн сервис для публикации рецептов, подписки на других пользователей.
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