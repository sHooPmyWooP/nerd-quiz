PYTHON = .venv/bin/python

.PHONY: run migrate load-fixture

run:
	$(PYTHON) manage.py runserver

migrate:
	$(PYTHON) manage.py makemigrations
	$(PYTHON) manage.py migrate

load-fixture:
	$(PYTHON) manage.py loaddata quizzes/*.yaml

serve:
	$(PYTHON) manage.py runserver
