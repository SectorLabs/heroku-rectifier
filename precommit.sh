black . --exclude venv/ -S
pytest --cov=rectifier --cov-report html tests/
mypy .

