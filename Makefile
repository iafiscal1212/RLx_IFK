VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: venv dev prod run stop bundle lint test status

venv:
	@test -d $(VENV) || python3.11 -m venv $(VENV)
	@$(PIP) -q install -U pip

dev: venv
	bash scripts/mode_dev.sh

prod:
	bash scripts/mode_prod.sh

run: venv
	$(PIP) -q install fastapi uvicorn pyyaml regex psutil
	$(VENV)/bin/uvicorn app.main:app --host 127.0.0.1 --port 8717

stop:
	@pkill -f "uvicorn app.main:app" || true

bundle:
	bash scripts/build_offline_bundle.sh

lint: venv
	$(PIP) -q install ruff black bandit
	$(VENV)/bin/ruff check .
	$(VENV)/bin/black --check .
	$(VENV)/bin/bandit -r app || true

test: venv
	$(PIP) -q install pytest requests
	$(VENV)/bin/pytest -q || true

status:
	bash scripts/mode_status.sh
