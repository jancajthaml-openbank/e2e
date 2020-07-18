ifndef GITHUB_RELEASE_TOKEN
$(warning GITHUB_RELEASE_TOKEN is not set)
endif

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
	@(docker pull jancajthaml/bbtest:$^)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_postgres" -q) &> /dev/null || :)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_$^" -q) &> /dev/null || :)
	@(docker build -f bbtest/postgres/Dockerfile -t e2e_postgres bbtest/postgres)
	@(docker run -d --shm-size=256MB --name=e2e_postgres e2e_postgres &> /dev/null || :)
	@docker exec -t $$(\
		docker run \
			-d \
			-t \
			--cpuset-cpus=1 \
			--link=e2e_postgres:postgres \
			--name=e2e_bbtest_$^ \
			-e GITHUB_RELEASE_TOKEN="$(GITHUB_RELEASE_TOKEN)" \
			-e UNIT_ARCH="$^" \
			-v /var/run/docker.sock:/var/run/docker.sock:rw \
			-v /var/lib/docker/containers:/var/lib/docker/containers:rw \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v $$(pwd)/bbtest:/opt/app \
			-v $$(pwd)/reports:/tmp/reports \
			-w /opt/app \
		jancajthaml/bbtest:$^ \
	) python3 /opt/app/main.py
	@(docker rm -f $$(docker ps -a --filter="name=e2e_postgres" -q) &> /dev/null || :)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_$^" -q) &> /dev/null || :)

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
