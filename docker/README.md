# Docker

This effort is to get Mycodo running in Docker containers with all features working. Many parts of the system work, however there are also many that do not.

***This is currently experimental***

Please do not submit github issues for Docker-related problems. Also do not expect this feature to remain consistent (i.e. previous builds may not be compatible with future builds). Join [Docker Issue (#637)](https://github.com/kizniche/Mycodo/issues/637) for Mycodo Docker discussion.

## Setup

### Notes

This has been tested to work with:

- Raspberry Pi running Raspberry Pi OS
- PC running Ubuntu Linux (20.04, 64-bit)

A Dockerized Mycodo instance cannot run if there is a local install of Mycodo also running because they use the same ports. You can stop any local, non-Docker Mycodo instances prior to building with the following commands. Note that this will only stop these services until reboot.

```shell script
sudo service mycodo stop
sudo service mycodoflask stop
sudo service nginx stop
```

If you are building for a Pi Zero, you will need to change `FROM influxdb:1.8.10` to `FROM mendhak/arm32v6-influxdb` in docker/influxdb/Dockerfile prior to building.

### Install Prerequisites

Install Docker Engine for your operating system using the instructions at https://docs.docker.com/engine/install/

Add your user to the docker group to be able to execute doker commands.

```
sudo usermod -aG docker $USER
```

Log out then back in to make the group changes go into effect before attempting to build.

### Configure

Edit docker-compose.yaml and change both (2) instances of TZ=America/New_York to your time zone. This setting is located under both mycodo_daemon and mycodo_flask

### Build and Start

```shell script
cd Mycodo
docker compose up --build -d
```

### Access

If successfully built, Mycodo can be accessed at https://127.0.0.1

## Virtual Machine

For consistency, I will now go through the steps to installing Mycodo in Docker containers with the use of a virtual machine that can be run from Windows, Mac, or Linux. This ensures a consistent platform to test from and reduces the issues that can occur with the use of different Linux distributions. If you're having issues with the above installation steps, try the method below.

### Install VirtualBox

Install Virtualbox from https://www.virtualbox.org/wiki/Downloads

### Download Raspbian

Download the [Raspberry Pi OS (64-bit) with Desktop ISO](https://www.raspberrypi.com/software/operating-systems/) or ISO of another Debian-based Linux distribution, such as Xubuntu.

### Create New Virtual Machine

- Start VirtualBox and click ```New``` to create a new virtual machine.
- Enter a name, change the Type to ```Linux```, and version to ```Debian (64-bit)```, then click Next.
- Select at least 1024 MB RAM to allocate to this virtual machine, then click Next.
- Select ```Create a virtual hard disk now```, then click Next.
- Select ```VDI (VirtualBox Disk Image)```, then click Next.
- Select ```Dynamically allocated```, then click Next.
- Raspbian will take up around 8 GB, so allocate at least 12 GB on the next screen, then click Create.
- Select the new virtual machine that was just created, then click ```Settings```.
- Click ```Storage``` on the left menu, then under ```Controller: IDE```, select ```Empty```, then under ```Attributes``` on the right, click the disc icon next to ```Optical Drive```, then select ```Choose Virtual Optical Disk File``` and select the Raspbian ISO that was downloaded.
- Click OK to close the settings menu.
- Start the virtual machine by clicking Start.

### Installing Raspbian

- Once the virtual machine starts, you will be presented with a menu titled ```Debian GNU/Linux menu (BIOS mode)```. Select ```install```.
- Select your language, then press Enter.
- On the ```Partition discs``` screen, select ```Guided - use entire disk```, then press Enter.
- On the next screen, select the only disk that's presented, then press Enter.
- On the next screen, select ```All files in one partition (recommended for new users)```, then press Enter.
- On the next screen, select ```Finish partitioning and write changes to disk```, then press Enter.
- On the next screen, select ```<Yes>``` to the ```Write the changes to disks?``` question, then press Enter.
- On the ```Install the GRUB boot loader on a hard disk``` screen, select ```<Yes>``` to the ```Install the GRUB boot loader to the master boot record?``` question, then press Enter.
- On the next screen, select ```/dev/sda```, then press Enter.
- Give the next processes ample time to complete.
- On the ```Finish the installation``` screen, select ```<Continue>```, then press Enter.
- Once the virtual machine reboots, the Raspbian desktop should load and present a graphical setup to finish installing Raspbian. Follow the prompts to complete the install.
- At this point is is recommended to open a terminal and run ```sudo apt update && sudo apt upgrade``` to upgrade your system software to the latest version (if you haven't already done this in the graphical setup).

### Install Mycodo in Docker containers

Open a terminal in Raspbian and run the following commands.

#### Retrieve and extract the latest Mycodo release

```shell script
sudo apt-get install git
git clone https://github.com/kizniche/Mycodo
```

Then follow the instructions to [Install Prerequisites](#install-prerequisites) and [Build and Start](#build-and-start).

### Grafana

If Grafana was enabled prior to the build, it can be accessed at http://127.0.0.1:3000

The default user is admin and the password admin.

## Docker Management

### Rebuild

If you change code and want to rebuild to incorporate it into the running containers, all you need to do is rebuild and restart the containers.

```shell script
cd ~/Mycodo
```

### Bring Down

To stop the running containers and prevent them from automatically starting when the system start.

```shell script
cd ~/Mycodo/docker
docker compose down
```

### Bring Back Up

If the containers have been stopped or brought down, you can bring them back up or start them again. The system has to have been previously built for this to work.

```shell script
cd ~/Mycodo
docker compose up -d
```

### Clean

To bring down all containers and delete all image data (volume data is preserved).

```shell script
cd ~/Mycodo
docker compose down
docker system prune -a
```

## Grafana and Telegraf

For reference, this is the guide used to implement Grafana and Telegraf: https://towardsdatascience.com/get-system-metrics-for-5-min-with-docker-telegraf-influxdb-and-grafana-97cfd957f0ac

### Enable Grafana and Telegraf

Grafana and Telegraf are disabled by default. To enable either or both of these features (prior to building), open docker-compose.yml and uncomment the blocks that follow the statement "Uncomment the following blocks and rebuild to enable Grafana and/or Telegraf", save, then rebuild.

Grafana will be accessible at http://127.0.0.1:3000

### Add Mycodo as a data source

After logging in and changing the admin password, select "Add data source", then "InfluxDB". Enter the following information:

-  Name: InfluxDB-mycodo
-  Default: Checked
-  URL: http://mycodo_influxdb:8086
-  Database: mycodo_db
-  User: mycodo
-  Password: mmdu77sj3nIoiajjs

Click "Save and Test"

### Add Telegraf Dashboard

Hover over Dashboards at the top-left, then click Import. Enter 928 as the Grafana Dashboard URL, then click Load. Select InfluxDB-mycodo as the data source for the ```InfluxDB telegraf``` field, then click Import. Once the dashboard has loaded, click ```Save Dashboard``` at the top of the dashboard.
