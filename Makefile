.PHONY: all
all: bbtest

.PHONY: bbtest
bbtest:
	@docker-compose run --rm bbtest

.PHONY: run
run:
	docker-compose up
