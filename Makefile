
export COMPOSE_DOCKER_CLI_BUILD = 1
export DOCKER_BUILDKIT = 1
export COMPOSE_PROJECT_NAME = e2e

.ONESHELL:
.PHONY: arm64
.PHONY: amd64
.PHONY: armhf

.PHONY: all
all: bbtest perf

.PHONY: bbtest
bbtest:
	@$(MAKE) bbtest-amd64

.PHONY: bbtest-%
bbtest-%: %
	@docker-compose up -d bbtest-$^
	@docker exec -t $$(docker-compose ps -q bbtest-$^) python3 /opt/app/bbtest/main.py
	@docker-compose down -v

.PHONY: perf
perf:
	@docker-compose up -d perf
	@docker exec -t $$(docker-compose ps -q perf) python3 /opt/app/perf/main.py
	@docker-compose down -v
