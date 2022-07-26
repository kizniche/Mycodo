build:
	docker-compose up --build -d

clean:
	docker-compose down
	docker system prune -a
