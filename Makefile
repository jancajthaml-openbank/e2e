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
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_$^" -q) &> /dev/null || :)
	@(docker exec -it $$(\
		docker run -d -ti \
			--name=e2e_bbtest_$^ \
			-e GITHUB_RELEASE_TOKEN="$(GITHUB_RELEASE_TOKEN)" \
			-e UNIT_ARCH="$^" \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v /var/run/docker.sock:/var/run/docker.sock \
			-v /var/lib/docker/containers:/var/lib/docker/containers \
			-v $$(pwd)/bbtest:/opt/bbtest \
			-v $$(pwd)/reports:/reports \
		jancajthaml/bbtest:$^ \
	) rspec \
		--require /opt/bbtest/spec.rb \
		--format documentation \
		--format RspecJunitFormatter \
		--out junit.xml \
		--pattern /opt/bbtest/features/*.feature || :)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_$^" -q) &> /dev/null || :)

.PHONY: perf-%
perf-%: %
	@(docker pull jancajthaml/bbtest:$^)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_perf_$^" -q) &> /dev/null || :)
	@(docker exec -it $$(\
		docker run -d -ti \
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
