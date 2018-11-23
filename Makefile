.PHONY: all
all: bbtest perf

.PHONY: candidate
candidate:
	@docker-compose build candidate

.PHONY: bbtest
bbtest: candidate
	@echo "removing older bbtest containers if present"
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest" -q) &> /dev/null || :)
	@echo "running bbtest container"
	@(docker exec -it $$(\
		docker run -d -ti \
		  --name=e2e_bbtest \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v $$(pwd)/bbtest:/opt/bbtest \
			-v $$(pwd)/reports:/reports \
			--privileged=true \
			--security-opt seccomp:unconfined \
		openbankdev/e2e_candidate \
	) rspec \
		--require /opt/bbtest/spec.rb \
		--format documentation \
		--format RspecJunitFormatter \
		--out junit.xml \
		--pattern /opt/bbtest/features/*.feature || :)
	@echo "removing bbtest container"
	@(docker rm -f $$(docker ps -a --filter="name=e2e_bbtest" -q) &> /dev/null || :)

.PHONY: perf
perf: candidate
	@echo "removing older perf containers if present"
	@(docker rm -f $$(docker ps -a --filter="name=e2e_perf" -q) &> /dev/null || :)
	@echo "running perf container"
	@(docker exec -it $$(\
		docker run -d -ti \
		  --name=e2e_perf \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			-v $$(pwd)/perf:/opt/bbtest \
			-v $$(pwd)/reports:/reports \
			--privileged=true \
			--security-opt seccomp:unconfined \
		openbankdev/e2e_candidate \
	) python3 \
		/opt/bbtest/main.py || :)
	@echo "removing perf container"
	@(docker rm -f $$(docker ps -a --filter="name=e2e_perf" -q) &> /dev/null || :)

.PHONY: run
run: candidate
	@echo "removing older containers if present"
	@(docker rm -f $$(docker ps -a --filter="name=e2e_run" -q) &> /dev/null || :)
	@echo "running perf container"
	@(docker exec -it $$(\
		docker run -d -ti \
		  --name=e2e_run \
			-v /sys/fs/cgroup:/sys/fs/cgroup:ro \
			--privileged=true \
			--security-opt seccomp:unconfined \
		openbankdev/e2e_candidate \
	) bash || :)
	@echo "removing container"
	@(docker rm -f $$(docker ps -a --filter="name=e2e_run" -q) &> /dev/null || :)
