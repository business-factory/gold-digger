########################################################
# Dockerfile to build Python application 'gold-digger'
# Based on Ubuntu
########################################################

FROM ubuntu
MAINTAINER ROI Hunter

# Setup system locale
RUN locale-gen en_US.utf8
ENV LANG en_US.utf8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.utf8
RUN update-locale LANG=en_US.utf8

# Install system dependencies
RUN apt-get update && \
	apt-get install -y git python3 python3-pip && \
	apt-get install -y libpq-dev supervisor cron

# Get GIT repository with project
RUN git clone -b master https://github.com/business-factory/gold-digger.git

# Set the default directory
WORKDIR /gold-digger

# Install Python dependencies
RUN pip3 install -U pip wheel && \
	pip3 install --use-wheel -r requirements.txt

# Create local config file
ADD gold_digger/config/params_local.py gold_digger/config/params_local.py

# Setup supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN mkdir -p /var/log/gold-digger

# Command to execute
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
