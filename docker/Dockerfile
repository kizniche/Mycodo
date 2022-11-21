FROM debian:stable-slim

ENV DOCKER_CONTAINER TRUE

RUN useradd -ms /bin/bash pi
RUN useradd -ms /bin/bash mycodo

COPY ./mycodo/scripts/upgrade_commands.sh /home/mycodo/mycodo/scripts/upgrade_commands.sh

RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh docker-create-files-directories-symlinks
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh update-apt
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh update-packages
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh ssl-certs-generate
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh install-docker

COPY ./install/requirements.txt /home/mycodo/install

RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh docker-update-pip
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh docker-update-pip-packages

COPY . /home/mycodo
WORKDIR /home/mycodo/mycodo

RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh docker-compile-translations
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh compile-mycodo-wrapper
