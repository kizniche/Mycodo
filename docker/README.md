# Docker

This effort is to get Mycodo running in Docker containers with all features working. many parts of the system work, however there are also many that do not.

***This is currently experimental***

Please do not submit github issues for Docker-related problems.

## Setup

### Notes

This has been tested to work with:

-  Raspberry Pi running Raspbian Buster
-  64-bit PC running Ubuntu Linux (18.04, 64-bit)

A Dockerized Mycodo instance cannot run if there is a local install of Mycodo also running. You can stop any local non-Docker Mycodo instances prior to building with the following commands. Note that this will only stop these services until reboot.

```shell script
sudo service mycodo stop
sudo service mycodoflask stop
sudo service nginx stop
```

### Prerequisites

Install prerequisites with the following command.

```shell script
sudo /bin/bash ~/Mycodo/docker/install-dependencies.sh install-dependencies
```

Log out then back in to make the group changes go into effect before attempting to build.

### Build and Start

```shell script
cd ~/Mycodo/docker
make build
```

### Access

#### Mycodo

Mycodo can be accessed at https://127.0.0.1

#### Grafana

Grafana can be accessed at http://127.0.0.1:3000

The default user is admin and the password admin.

## Docker Management

### Stop

```shell script
cd ~/Mycodo/docker
../env/bin/docker-compose down
```

### Clean

```shell script
cd ~/Mycodo/docker
make clean
```

### Disable Grafana and Telegraf

To disable these features (prior to building), just delete or comment out their lines in docker-compose.yml. For example:

```
#  telegraf:
#    image: telegraf:latest
#    container_name: telegraf
#    volumes:
#      - ./telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro
#    depends_on:
#      - influxdb

#  grafana:
#    image: grafana/grafana:latest
#    container_name: grafana
#    ports:
#      - "3000:3000"
#    env_file:
#      - 'grafana/env.grafana'
#    volumes:
#      - grafana-volume:/var/lib/grafana
#    depends_on:
#      - influxdb
```

As this part of Mycodo develops, a more elegant solution to disabling these options will form.

## Grafana

For reference, this is the guide used to implement Grafana and Telegraf: https://towardsdatascience.com/get-system-metrics-for-5-min-with-docker-telegraf-influxdb-and-grafana-97cfd957f0ac

### Add Mycodo as a data source

After logging in and changing the admin password, select "Add data source", then "InfluxDB". Enter the following information:

Name: InfluxDB-mycodo

Default: Checked

URL: http://influxdb:8086

Database: mycodo_db

User: mycodo

Password: mmdu77sj3nIoiajjs

Click "Save and Test"

### Add Telegraf plugin

Click the plus icon at the top-left, then Import. Enter 928 in the Grafana.com Dashboard field, then click Load. Select InfluxDB-mycodo as the data source for the ```InfluxDB telegraf``` field, then click Import. Once the dashboard has loaded, click ```Save dashboard``` at the top of the dashboard.
