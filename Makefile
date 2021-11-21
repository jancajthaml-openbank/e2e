ARCH := $(shell uname -m | sed 's/x86_64/amd64/')

export COMPOSE_DOCKER_CLI_BUILD = 1
export DOCKER_BUILDKIT = 1
export COMPOSE_PROJECT_NAME = e2e

.ONESHELL:
.PHONY: arm64
.PHONY: amd64

.PHONY: all
all: bootstrap bbtest perf

.PHONY: bootstrap
bootstrap:
	@ARCH=$(ARCH) docker-compose build

.PHONY: bbtest
bbtest:
	@$(MAKE) bbtest-$(ARCH)

.PHONY: perf
perf:
	@$(MAKE) perf-$(ARCH)

.PHONY: bbtest-%
bbtest-%: %
	@ARCH=$^ docker-compose up -d bbtest
	@docker exec -t $$(ARCH=$^ docker-compose ps -q bbtest) python3 /opt/app/bbtest/main.py
	@ARCH=$^ docker-compose down -v

.PHONY: perf-%
perf-%: %
	@ARCH=$^ docker-compose up -d perf
	@docker exec -t $$(ARCH=$^ docker-compose ps -q perf) python3 /opt/app/perf/main.py
	@ARCH=$^ docker-compose down -v
