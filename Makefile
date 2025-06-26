build:
	docker compose --profile build build
deploy: build
	docker compose --profile deploy up --build -d
	docker compose exec web alembic upgrade head
list:
	docker ps -a | grep latex