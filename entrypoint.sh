#!/bin/sh
echo "Checking for database $DB_NAME"
if [ ! -z "$DB_NAME" ]
then
    echo "Waiting for postgres..."
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
fi

if [ "$MIGRATE" = "true" ] ; then
    echo "Running migrate and collectstatic..."
    python manage.py migrate
    python manage.py collectstatic --no-input
    python manage.py migrate sites
fi

exec "$@"