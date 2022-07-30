CONTAINER_NAME=mycodo_influxdb
BUCKET=mycodo_db
PASSWORD=mmdu77sj3nIoiajjs
ORGANIZATION=mycodo
USERNAME=mycodo 

build:
	docker-compose up --build -d

clean:
	docker-compose down
	docker system prune -a

rmvolume:
	rm -rf /Users/mswhiskers/temp/influxdbv2/*

initialize-influx-2-db:
	docker exec -it ${CONTAINER_NAME} influx setup \
            --username ${USERNAME} \
            --password ${PASSWORD} \
            --org ${ORGANIZATION} \
            --bucket ${BUCKET}