PYTHON ?= python
POETRY ?= poetry
UV ?= uv
VENV ?= .venv_media
VENV_PYTHON = . $(VENV)/bin/activate && python

.PHONY: install
install:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip
	. $(VENV)/bin/activate && pip install -e .[dev]

.PHONY: install-extras
install-extras:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip
	. $(VENV)/bin/activate && pip install -e .[dev,aws,gcp]

.PHONY: lint
lint:
	. $(VENV)/bin/activate && ruff check .
	. $(VENV)/bin/activate && black --check switchboard apps tests scripts evals
	. $(VENV)/bin/activate && mypy .

.PHONY: test
test:
	. $(VENV)/bin/activate && pytest

.PHONY: test-container
test-container:
	bash scripts/run_tests_container.sh

.PHONY: coverage
coverage:
	. $(VENV)/bin/activate && pytest --cov=switchboard --cov-report=term-missing

.PHONY: mutation
mutation:
	. $(VENV)/bin/activate && mutmut run

.PHONY: qa
qa: lint test

.PHONY: dev
dev:
	docker compose up --build

.PHONY: dev-media
dev-media:
	SWITCHBOARD_APPROVAL_BACKEND=memory \
	SWITCHBOARD_ENABLE_TELEMETRY=false \
	SWITCHBOARD_API_URL=http://localhost:8000 \
	SWITCHBOARD_APPROVALS_URL=http://localhost:8501 \
	docker compose up --build -d
	$(VENV_PYTHON) -m playwright install chromium
	$(VENV_PYTHON) -m scripts.media.wait_for_services

.PHONY: dev-media-down
dev-media-down:
	docker compose down

.PHONY: media-hero
media-hero:
	$(VENV_PYTHON) scripts/media/walkthrough.py --video docs/media/generated/hero.mp4 --gif docs/media/generated/hero.gif

.PHONY: media-approvals-gif
media-approvals-gif:
	$(VENV_PYTHON) scripts/media/walkthrough.py --scene approvals --video docs/media/generated/approvals.mp4 --gif docs/media/generated/approvals.gif

.PHONY: media-screenshots
media-screenshots:
	$(VENV_PYTHON) scripts/media/screenshot_suite.py --output docs/media/screenshots

.PHONY: policy-heatmap
policy-heatmap:
	$(VENV_PYTHON) scripts/media/policy_heatmap.py --output docs/media/generated/policy_heatmap

.PHONY: poster
poster:
	$(VENV_PYTHON) scripts/media/export_poster.py

.PHONY: media-artifacts
media-artifacts:
	$(VENV_PYTHON) scripts/media/build_all.py

.PHONY: seed
seed:
	$(VENV_PYTHON) scripts/seed_policies.py

.PHONY: db-init
db-init:
	$(VENV_PYTHON) scripts/init_db.py

.PHONY: demo-e2e
demo-e2e:
	bash scripts/demo_change_request.sh

.PHONY: audit-verify
audit-verify:
	@if [ -z "$(AUDIT_ID)" ]; then \
		echo "AUDIT_ID is required: make audit-verify AUDIT_ID=<uuid> [REKOR_URL=<url>]"; \
		exit 1; \
	fi
	@if [ -n "$(REKOR_URL)" ]; then \
		bash scripts/verify_audit.sh $(AUDIT_ID) --rekor-url $(REKOR_URL); \
	else \
		bash scripts/verify_audit.sh $(AUDIT_ID); \
	fi

.PHONY: eval
eval:
	$(VENV_PYTHON) evals/runner.py

.PHONY: tox
tox:
	. $(VENV)/bin/activate && tox
