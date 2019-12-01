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
cd ~/Mycodo/docker
sudo /bin/bash ./setup.sh dependencies
```

Log out then back in to make the group changes go into effect before attempting to build.

### Build and Start

```shell script
cd ~/Mycodo/docker
make build
```


## Virtual Machine

For consistency, I will now go through the steps to installing Mycodo in Docker containers with the use of a virtual machine that can be run from Windows, Mac, or Linux. This ensures a consistent platform to test from and reduces the issues that can occur with the use of different Linux distributions. If you're having issues with the above installation steps, try the method below.

#### Install VirtualBox

Install Virtualbox from https://www.virtualbox.org/wiki/Downloads

#### Download Raspbian

Download the [Debian Buster with Raspberry Pi Desktop ISO](https://www.raspberrypi.org/downloads/raspberry-pi-desktop/).

#### Create New Virtual Machine

-  Start VirtualBox and click ```New``` to create a new virtual machine.
-  Enter a name, change the Type to ```Linux```, and version to ```Debian (64-bit)```, then click Next.
-  Select at least 1024 MB RAM to allocate to this virtual machine, then click Next.
-  Select ```Create a virtual hard disk now```, then click Next.
-  Select ```VDI (VirtualBox Disk Image)```, then click Next.
-  Select ```Dynamically allocated```, then click Next.
-  Raspbian will take up around 8 GB, so allocate at least 12 GB on the next screen, then click Create.
-  Select the new virtual machine that was just created, then click ```Settings```.
-  Click ```Storage``` on the left menu, then under ```Controller: IDE```, select ```Empty```, then under ```Attributes``` on the right, click the disc icon next to ```Optical Drive```, then select ```Choose Virtual Optical Disk File``` and select the Raspbian ISO that was downloaded.
-  Click OK to close the settings menu.
-  Start the virtual machine by clicking Start.

#### Installing Raspbian

-  Once the virtual machine starts, you will be presented with a menu titled ```Debian GNU/Linux menu (BIOS mode)```. Select ```install```.
-  Select your language, then press Enter.
-  On the ```Partition discs``` screen, select ```Guided - use entire disk```, then press Enter.
-  On the next screen, select the only disk that's presented, then press Enter.
-  On the next screen, select ```All files in one partition (recommended for new users)```, then press Enter.
-  On the next screen, select ```Finish partitioning and write changes to disk```, then press Enter.
-  On the next screen, select ```<Yes>``` to the ```Write the changes to disks?``` question, then press Enter.
-  On the ```Install the GRUB boot loader on a hard disk``` screen, select ```<Yes>``` to the ```Install the GRUB boot loader to the master boot record?``` question, then press Enter.
-  On the next screen, select ```/dev/sda```, then press Enter.
-  Give the next processes ample time to complete.
-  On the ```Finish the installation``` screen, select ```<Continue>```, then press Enter.
-  Once the virtual machine reboots, the Raspbian desktop should load and present a graphical setup to finish installing Raspbian. Follow the prompts to complete the install.
-  At this point is is recommended to open a terminal and run ```sudo apt update && sudo apt upgrade``` to upgrade your system software to the latest version (if you haven't already done this in the graphical setup).

#### Installing Mycodo with Docker

Open a terminal in Raspbian and run the following commands to retrieve and extract the latest Mycodo release.

```shell script
sudo apt-get install -y jq
cd ~
curl -s https://api.github.com/repos/kizniche/Mycodo/releases/latest | \
jq -r '.tarball_url' | wget -i - -O mycodo-latest.tar.gz
mkdir Mycodo
tar xzf mycodo-latest.tar.gz -C Mycodo --strip-components=1
rm -f mycodo-latest.tar.gz
```

Install prerequisites 

```shell script
cd ~/Mycodo/docker
sudo /bin/bash ./setup.sh dependencies
```

Finally, build with docker-compose

```shell script
make build
```


## Access

### Mycodo

Mycodo can be accessed at https://127.0.0.1

### Grafana

If Grafana was enabled prior to the build, it can be accessed at http://127.0.0.1:3000

The default user is admin and the password admin.



## Docker Management

### Stop Containers

```shell script
cd ~/Mycodo/docker
../env/bin/docker-compose down
```

### Start Containers

```shell script
cd ~/Mycodo/docker
../env/bin/docker-compose up
```

### Clean

```shell script
cd ~/Mycodo/docker
make clean
```



## Grafana

For reference, this is the guide used to implement Grafana and Telegraf: https://towardsdatascience.com/get-system-metrics-for-5-min-with-docker-telegraf-influxdb-and-grafana-97cfd957f0ac

### Enable Grafana and Telegraf

Grafana and Telegraf are disabled by default. To enable either or both of these features (prior to building), uncomment these lines in docker-compose.yml:

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
