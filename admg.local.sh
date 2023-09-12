case $1 in
  run) docker-compose -f docker-compose.local.yml up;;
  build) docker-compose -f docker-compose.local.yml build;;
  test-setup) docker-compose -f docker-compose.local.yml up db rabbitmq;;
  user) docker-compose -f docker-compose.local.yml run web python manage.py createsuperuser;;
  test) docker-compose -f docker-compose.local.yml run web pytest admin_ui;;
  coverage-test) docker-compose -f docker-compose.local.yml run web coverage run -m pytest;;
  coverage-report) docker-compose -f docker-compose.local.yml run web coverage report -m --skip-covered;;
  coverage-report-xml) docker-compose -f docker-compose.local.yml run web coverage xml -o coverage.xml;;
esac 