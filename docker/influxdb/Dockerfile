FROM influxdb:1.8.10

ENV DOCKER_CONTAINER TRUE

RUN mkdir -pv /var/influxdb/data

COPY ./docker/influxdb/run.sh /home/mycodo/docker/influxdb/run.sh
RUN chmod +x /home/mycodo/docker/influxdb/run.sh

ENV PRE_CREATE_DB mycodo_db
ENV ADMIN_USER mycodo
ENV PASS mmdu77sj3nIoiajjs

EXPOSE 8086

CMD /home/mycodo/docker/influxdb/run.sh
