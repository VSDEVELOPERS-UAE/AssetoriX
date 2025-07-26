#!/bin/bash

pip install --upgrade pip
pip install -r requirements.txt
pip install django-import-export
python manage.py collectstatic --noinput
python manage.py migrate
