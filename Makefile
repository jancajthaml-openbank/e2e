.PHONY: all
all: bbtest

.PHONY: bbtest
bbtest:
	@docker-compose run --rm bbtest

.PHONY: run
run:
	@docker-compose up

.PHONY: perf
perf:
	@cd perf && docker build -t e2e_perf .
	@./perf/performance
