ifndef GITHUB_RELEASE_TOKEN
$(warning GITHUB_RELEASE_TOKEN is not set)
endif

.PHONY: all
all: bbtest perf

.PHONY: bbtest
	$(MAKE) -j3 \
		bbtest-amd64 \
		bbtest-armhf \
		bbtest-arm64

.PHONY: bbtest-amd64
bbtest-amd64:
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_amd64" -q) &> /dev/null || :)
	@(docker exec -it $$(\
		docker run -d -ti \
			--name=e2e_bbtest_amd64 \
			-e GITHUB_RELEASE_TOKEN="$(GITHUB_RELEASE_TOKEN)" \
			-e UNIT_ARCH="amd64" \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v /var/run/docker.sock:/var/run/docker.sock \
			-v /var/lib/docker/containers:/var/lib/docker/containers \
			-v $$(pwd)/bbtest:/opt/bbtest \
			-v $$(pwd)/reports:/reports \
			--privileged=true \
			--security-opt seccomp:unconfined \
		jancajthaml/bbtest:amd64 \
	) rspec \
		--require /opt/bbtest/spec.rb \
		--format documentation \
		--format RspecJunitFormatter \
		--out junit.xml \
		--pattern /opt/bbtest/features/*.feature || :)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_amd64" -q) &> /dev/null || :)

.PHONY: bbtest-armhf
bbtest-armhf:
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_armhf" -q) &> /dev/null || :)
	@(docker exec -it $$(\
		docker run -d -ti \
			--name=e2e_bbtest_armhf \
			-e GITHUB_RELEASE_TOKEN="$(GITHUB_RELEASE_TOKEN)" \
			-e UNIT_ARCH="armhf" \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v /var/run/docker.sock:/var/run/docker.sock \
			-v /var/lib/docker/containers:/var/lib/docker/containers \
			-v $$(pwd)/bbtest:/opt/bbtest \
			-v $$(pwd)/reports:/reports \
			--privileged=true \
			--security-opt seccomp:unconfined \
		jancajthaml/bbtest:armhf \
	) rspec \
		--require /opt/bbtest/spec.rb \
		--format documentation \
		--format RspecJunitFormatter \
		--out junit.xml \
		--pattern /opt/bbtest/features/*.feature || :)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_armhf" -q) &> /dev/null || :)

.PHONY: bbtest-arm64
bbtest-arm64:
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_arm64" -q) &> /dev/null || :)
	@(docker exec -it $$(\
		docker run -d -ti \
			--name=e2e_bbtest_arm64 \
			-e GITHUB_RELEASE_TOKEN="$(GITHUB_RELEASE_TOKEN)" \
			-e UNIT_ARCH="arm64" \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v /var/run/docker.sock:/var/run/docker.sock \
			-v /var/lib/docker/containers:/var/lib/docker/containers \
			-v $$(pwd)/bbtest:/opt/bbtest \
			-v $$(pwd)/reports:/reports \
			--privileged=true \
			--security-opt seccomp:unconfined \
		jancajthaml/bbtest:arm64 \
	) rspec \
		--require /opt/bbtest/spec.rb \
		--format documentation \
		--format RspecJunitFormatter \
		--out junit.xml \
		--pattern /opt/bbtest/features/*.feature || :)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest_arm64" -q) &> /dev/null || :)

.PHONY: perf
perf:
	@(docker rm -f $$(docker ps -a --filter="name=e2e_perf" -q) &> /dev/null || :)
	@(docker exec -it $$(\
		docker run -d -ti \
			--name=e2e_perf \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v /var/run/docker.sock:/var/run/docker.sock \
			-v /var/lib/docker/containers:/var/lib/docker/containers \
			-v $$(pwd)/perf:/opt/bbtest \
			-v $$(pwd)/reports:/reports \
			--privileged=true \
			--security-opt seccomp:unconfined \
		jancajthaml/bbtest:amd64 \
	) python3 \
		/opt/bbtest/main.py || :)
	@(docker rm -f $$(docker ps -a --filter="name=e2e_perf" -q) &> /dev/null || :)
