docker-build:
	docker build . -f Dockerfile -t devalv/repo-cloner:0.1.0 -t devalv/repo-cloner:latest

docker-push:
	docker push devalv/repo-cloner:0.1.0
	docker push devalv/repo-cloner:latest

docker-up:
	docker compose up

format:
	pre-commit run --all-files
