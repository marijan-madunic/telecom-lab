build:
	docker build -t aaa-service ./aaa-service
	docker build -t udm-service ./udm-service
	docker build -t pcrf-service ./pcrf-service
	docker build -t ocs-service ./ocs-service

deploy:
	kubectl apply -f kubernetes/

restart:
	kubectl rollout restart deployment aaa-service
	kubectl rollout restart deployment udm-service
	kubectl rollout restart deployment pcrf-service
	kubectl rollout restart deployment ocs-service

pods:
	kubectl get pods

logs-aaa:
	kubectl logs -f deployment/aaa-service

logs-udm:
	kubectl logs -f deployment/udm-service

logs-pcrf:
	kubectl logs -f deployment/pcrf-service

logs-ocs:
	kubectl logs -f deployment/ocs-service
