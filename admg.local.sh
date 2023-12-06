case $1 in
  run) docker compose up;;
  build) docker compose build;;
  test-setup) docker compose up db rabbitmq;;
  user) docker compose run --rm -it web python manage.py createsuperuser;;
  test) docker compose run --rm -it web pytest admin_ui;;
  coverage-test) docker compose run --rm -it web coverage run -m pytest;;
  coverage-report) docker compose run --rm -it web coverage report -m --skip-covered;;
  coverage-report-xml) docker compose run --rm -it web coverage xml -o coverage.xml;;
esac 
