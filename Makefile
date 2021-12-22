export ARCH = $(shell uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')
export COMPOSE_DOCKER_CLI_BUILD = 1
export DOCKER_BUILDKIT = 1
export COMPOSE_PROJECT_NAME = e2e

.ONESHELL:

.PHONY: all
all: bootstrap bbtest perf

.PHONY: bootstrap
bootstrap:
	@docker compose build

.PHONY: bbtest
bbtest:
	@docker compose up -d bbtest
	@docker exec -t $$(docker compose ps -q bbtest) python3 /opt/app/bbtest/main.py
	@docker compose down -v

.PHONY: perf
perf:
	@docker compose up -d perf
	@docker exec -t $$(docker compose ps -q perf) python3 /opt/app/perf/main.py
	@docker compose down -v
