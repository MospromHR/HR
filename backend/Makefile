ifneq (,$(findstring xterm,${TERM}))
	GREEN := $(shell tput -Txterm setaf 2)
	NC    := $(shell tput -Txterm sgr0)
else
	GREEN := ""
	NC    := ""
endif

.PHONY: help
.DEFAULT_GOAL := help
help: ## Help
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: api
api: ## Run api
	uv run fastapi dev api/app.py

.PHONY: worker
worker: ## Run worker
	uv run celery -A worker.app worker --loglevel=DEBUG -Q files -c 2

# DOCKER

.PHONY: run
run: ## Run docker
	docker compose up --build

.PHONY: up
up: ## Up docker service
	docker compose up -d --build

.PHONY: down
down: ## Down docker service
	docker compose down

.PHONY: prune
prune: ## Down docker service and remove volumes
	docker compose down -v
