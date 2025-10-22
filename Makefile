PYTHON ?= python3
POETRY ?= poetry
UV ?= uv

.PHONY: install
install:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -e .[dev]

.PHONY: install-extras
install-extras:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -e .[dev,aws,gcp]

.PHONY: lint
lint:
	. .venv/bin/activate && ruff check .
	. .venv/bin/activate && black --check switchboard apps tests scripts evals
	. .venv/bin/activate && mypy .

.PHONY: test
test:
	. .venv/bin/activate && pytest

.PHONY: test-container
test-container:
	bash scripts/run_tests_container.sh

.PHONY: coverage
coverage:
	. .venv/bin/activate && pytest --cov=switchboard --cov-report=term-missing

.PHONY: mutation
mutation:
	. .venv/bin/activate && mutmut run

.PHONY: qa
qa: lint test

.PHONY: dev
dev:
	docker compose up --build

.PHONY: seed
seed:
	. .venv/bin/activate && $(PYTHON) scripts/seed_policies.py

.PHONY: db-init
db-init:
	. .venv/bin/activate && $(PYTHON) scripts/init_db.py

.PHONY: demo-e2e
demo-e2e:
	bash scripts/demo_change_request.sh

.PHONY: audit-verify
audit-verify:
	bash scripts/verify_audit.sh

.PHONY: eval
eval:
	. .venv/bin/activate && python evals/runner.py

.PHONY: tox
tox:
	. .venv/bin/activate && tox
