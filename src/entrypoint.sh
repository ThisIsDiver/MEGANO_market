#!/bin/sh
python manage.py makemigrations market_api_app --noinput
until python manage.py migrate --noinput; do
  echo "Waiting for db"
  sleep 2
done
for f in fixtures/*.json; do
  [ -e "$f" ] || continue
  python manage.py loaddata "$f"
done
python manage.py createsuperuser --noinput || echo "Superuser is ready"
echo "Superuser login: $DJANGO_SUPERUSER_USERNAME"
echo "Superuser password: $DJANGO_SUPERUSER_PASSWORD"
python manage.py runserver 0.0.0.0:8000