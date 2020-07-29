
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

.PHONY: perf
perf:
	@$(MAKE) perf-amd64

.PHONY: bbtest-%
bbtest-%: %
	@\
		GITHUB_RELEASE_TOKEN=$(GITHUB_RELEASE_TOKEN) \
		docker-compose up -d bbtest-$^
	@docker exec -t $$(docker-compose ps -q bbtest-$^) python3 /opt/app/bbtest/main.py
	@docker-compose down -v

.PHONY: perf-%
perf-%: %
	@(docker pull jancajthaml/bbtest:$^)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_perf_$^" -q) &> /dev/null || :)
	@(docker exec -it $$(\
		docker run \
			-d \
			-t \
			--name=e2e_perf_$^ \
			-e GITHUB_RELEASE_TOKEN="$(GITHUB_RELEASE_TOKEN)" \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v /var/run/docker.sock:/var/run/docker.sock \
			-v /var/lib/docker/containers:/var/lib/docker/containers \
			-v $$(pwd)/perf:/opt/bbtest \
			-v $$(pwd)/reports:/reports \
		jancajthaml/bbtest:$^ \
	) python3 \
		/opt/bbtest/main.py || :)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_perf_$^" -q) &> /dev/null || :)
