#!/bin/sh
echo "Checking for database $DB_NAME"
if [ ! -z "$DB_NAME" ]
then
    echo "Waiting for postgres at ${DB_HOST}:${DB_PORT}..."
    echo $(dig +short $DB_HOST)
    nc -vz $DB_HOST $DB_PORT
    echo "PostgreSQL started."
fi

if [ "$MIGRATE" = "true" ] ; then
    echo "Running migrate and collectstatic..."
    python manage.py migrate
    python manage.py collectstatic --no-input
    python manage.py migrate sites
fi

exec "$@"
