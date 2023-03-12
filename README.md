# Yatube

### Описание проекта:

Проект Yatube. Социальная сеть.

### Как запустить проект на тестовом сервере:
Клонировать репозиторий, перейти в директорию с проектом.

```
git clone git@github.com:sugunos/api_yamdb.git
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
. venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py makemigrations
```
```
python manage.py migrate
```


