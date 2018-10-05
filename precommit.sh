black . --exclude venv/ --exclude env/ -S
pytest --cov=rectifier --cov-report html tests/
mypy .

