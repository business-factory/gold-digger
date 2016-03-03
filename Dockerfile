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
RUN apt-get update
RUN apt-get install -y git python3 python3-pip
RUN apt-get install -y libpq-dev supervisor

# Get GIT repository with project
RUN git clone https://github.com/business-factory/gold-digger.git

# Set the default directory
WORKDIR /gold-digger

# Install Python dependencies
RUN pip3 install -U pip wheel
RUN pip3 install --use-wheel -r requirements.txt

# Create local config file
ADD gold_digger/config/params_local.py gold_digger/config/params_local.py

# Setup cron for daily updates
# Add crontab file in the cron directory
ADD crontab.conf /etc/cron.d/daily-exchange-rates
RUN chmod 600 /etc/cron.d/daily-exchange-rates
RUN touch cron.log

# Setup supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN mkdir -p /var/log/gold-digger

# Command to execute
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
