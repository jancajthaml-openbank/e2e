.PHONY: all
all: bbtest perf

.PHONY: bbtest
bbtest:
	@echo "[info] stopping older runs"
	@(docker rm -f $$(docker-compose ps -q) 2> /dev/null || :) &> /dev/null
	@echo "[info] running bbtest"
	@docker-compose run --rm bbtest
	@echo "[info] stopping runs"
	@(docker rm -f $$(docker-compose ps -q) 2> /dev/null || :) &> /dev/null
	@(docker rm -f $$(docker ps -aqf "name=bbtest") || :) &> /dev/null

.PHONY: run
run:
	@docker-compose up

.PHONY: perf
perf:
	@cd perf && docker build -t e2e_perf .
	@./perf/performance

.PHONY: k8s
k8s:
	@(kubectl create namespace openbank 2> /dev/null || :)

	@kubectl create -f k8s/vault-test-journal-volume.yml
	@kubectl create -f k8s/vault-test-journal-claim.yml

	@kubectl create -f k8s/transaction-journal-volume.yml
	@kubectl create -f k8s/transaction-journal-claim.yml

	@kubectl apply -f k8s/lake-deployment.yml

	@kubectl apply -f k8s/vault-deployment.yml

	@kubectl apply -f k8s/wall-deployment.yml
	@kubectl apply -f k8s/wall-ingress.yml

	@kubectl apply -f k8s/haproxy-configmap.yml
	@kubectl apply -f k8s/haproxy-ingress-deployment.yml
	@kubectl apply -f k8s/haproxy-ingress-svc.yml

	#@kubectl scale deployment --namespace=openbank wall --replicas=4
	@(kubectl delete service --namespace=openbank haproxy-ingress-host 2> /dev/null || :)
	@kubectl expose deployment --namespace=openbank haproxy-ingress --type=LoadBalancer --port=80 --name=haproxy-ingress-host
	@kubectl get pods --namespace=openbank
	@kubectl get services --namespace=openbank

.PHONY: teardown
teardown:
	@kubectl delete --all ingresses --namespace=openbank --force
	@kubectl delete --all configmaps --namespace=openbank --force
	@kubectl delete --all persistentvolumeclaims --namespace=openbank --force
	@kubectl delete --all persistentvolumes --namespace=openbank --force
	@kubectl delete --all pods --namespace=openbank --force
	@kubectl delete --all deployments --namespace=openbank --force
	@kubectl delete --all services --namespace=openbank --force
