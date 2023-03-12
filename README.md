# Yatube

### Описание проекта:

Проект Yatube. Социальная сеть.

### Как запустить проект на тестовом сервере:
Клонировать репозиторий, перейти в директорию с проектом.

```
git clone git@github.com:sugunos/hw05_final.git
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
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
python3 manage.py makemigrations
```
```
python3 manage.py migrate
```


