#!/bin/sh
python manage.py graph_models data_models -v 3 -S -E -l dot -o dot.svg
python manage.py graph_models data_models -v 3 -S -E -l fdp -o fdp.svg
python manage.py graph_models data_models -v 3 -S -E -l sfdp -o sfdp.svg
