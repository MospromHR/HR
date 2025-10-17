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

# DOCKER

.PHONY: up
up: ## Up docker service
	docker compose up -d --build

.PHONY: down
down: ## Down docker service
	docker compose down
