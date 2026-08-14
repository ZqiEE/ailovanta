PYTHON ?= python
API_HOST ?= 127.0.0.1
API_PORT ?= 8000

.PHONY: install install-coding validate test api legacy-api coding-up coding-gpu coding-public coding-model cost-status node smoke maintain demo-training worker-check worker-report worker-reports export-reports data-demo data-report ledger-demo ledger-report chain-demo chain-export chain-submit model-demo model-report clean

install:
	$(PYTHON) -m pip install -r requirements.txt

install-coding:
	$(PYTHON) -m pip install -r requirements-coding.txt

validate:
	$(PYTHON) -m compileall -q api node_client scripts
	$(PYTHON) -m pytest -q

test:
	$(PYTHON) -m pytest -q

api:
	uvicorn api.product_app:app --reload --host $(API_HOST) --port $(API_PORT)

legacy-api:
	uvicorn api.main:app --reload --host $(API_HOST) --port $(API_PORT)

coding-up:
	docker compose -f docker-compose.coding.yml up -d --build

coding-gpu:
	docker compose -f docker-compose.coding.yml -f docker-compose.gpu.yml up -d --build

coding-public:
	@test -n "$(AILOVANTA_DOMAIN)" || (echo "Set AILOVANTA_DOMAIN=code.example.com" && exit 1)
	AILOVANTA_DOMAIN=$(AILOVANTA_DOMAIN) docker compose -f docker-compose.coding.yml --profile public up -d --build

coding-model:
	docker compose -f docker-compose.coding.yml exec ollama ollama pull $${OLLAMA_MODEL:-qwen2.5-coder:7b}

cost-status:
	curl -fsS http://$(API_HOST):$(API_PORT)/coding/cost

node:
	$(PYTHON) node_client/client.py --api-url http://$(API_HOST):$(API_PORT) --contribution 30

smoke:
	$(PYTHON) scripts/smoke_api.py --api-url http://$(API_HOST):$(API_PORT)

maintain:
	$(PYTHON) scripts/queue_maintenance.py --api-url http://$(API_HOST):$(API_PORT)

demo-training:
	$(PYTHON) scripts/demo_training_flow.py --api-url http://$(API_HOST):$(API_PORT)

worker-check:
	$(PYTHON) scripts/worker_self_check.py

worker-report:
	$(PYTHON) scripts/worker_report_demo.py

worker-reports:
	$(PYTHON) scripts/list_worker_reports.py

export-reports:
	$(PYTHON) scripts/export_worker_reports.py

data-demo:
	$(PYTHON) scripts/seed_authorized_corpus_demo.py

data-report:
	$(PYTHON) scripts/corpus_report.py

ledger-demo:
	$(PYTHON) scripts/seed_decentralized_network_demo.py

ledger-report:
	$(PYTHON) scripts/decentralized_ledger_report.py

chain-demo:
	$(PYTHON) scripts/chain_adapter_demo.py

chain-export:
	$(PYTHON) scripts/export_ledger_for_chain.py

chain-submit:
	$(PYTHON) scripts/simulate_chain_submit.py

model-demo:
	$(PYTHON) scripts/seed_distributed_model_demo.py

model-report:
	$(PYTHON) scripts/model_report.py

clean:
	rm -rf runtime_data .pytest_cache __pycache__ api/__pycache__ node_client/__pycache__ tests/__pycache__
