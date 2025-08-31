VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: all venv install dev prod run stop bundle lint test status

all: install dev

venv:
	@test -d $(VENV) || python3.11 -m venv $(VENV)
	@$(PIP) -q install -U pip

install: venv
	$(PIP) -q install -r requirements.txt
	$(PIP) -q install -r requirements-dev.txt

dev: venv
	bash scripts/mode_dev.sh

prod:
	bash scripts/mode_prod.sh

run: install
	$(VENV)/bin/uvicorn app.main:app --host 127.0.0.1 --port 8717

stop:
	@pkill -f "uvicorn app.main:app" || true

bundle: venv
	bash scripts/build_offline_bundle.sh

lint: install
	$(VENV)/bin/ruff check .
	$(VENV)/bin/black --check .
	$(VENV)/bin/bandit -r app || true

test: install
	$(VENV)/bin/pytest -q || true

status:
	bash scripts/mode_status.sh
