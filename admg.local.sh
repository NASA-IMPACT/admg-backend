case $1 in
  run) docker-compose -f docker-compose.local.yml up;;
  test) docker-compose -f docker-compose.local.yml run web pytest admin_ui;;
  coverage-test) docker-compose -f docker-compose.local.yml run web coverage run -m pytest;;
  coverage-report) docker-compose -f docker-compose.local.yml run web coverage report -m --skip-covered;;
  coverage-report-xml) docker-compose -f docker-compose.local.yml run web coverage xml -o coverage.xml;;
esac 


