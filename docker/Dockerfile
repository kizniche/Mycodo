FROM python:3.7-slim-buster

ENV DOCKER_CONTAINER TRUE

RUN useradd -ms /bin/bash pi
RUN useradd -ms /bin/bash mycodo

COPY . /home/mycodo

WORKDIR /home/mycodo/mycodo

RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh create-files-directories
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh update-packages
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh install-docker-ce-cli
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh docker-update-pip
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh docker-update-pip-packages
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh ssl-certs-generate
RUN /home/mycodo/mycodo/scripts/upgrade_commands.sh docker-compile-translations
