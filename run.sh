#!/bin/bash

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаем папку для загрузок если её нет
mkdir -p uploads

# Запускаем gunicorn
gunicorn --bind 0.0.0.0:5001 app:app
