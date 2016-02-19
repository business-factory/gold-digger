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

# Install system dependencies
RUN apt-get update
RUN apt-get install -y git python3 python3-pip
RUN apt-get install -y libpq-dev

# Get GIT repository with project
RUN git clone https://github.com/business-factory/gold-digger.git

# Set the default directory
WORKDIR /gold-digger

# Install Python dependencies
RUN pip3 install -U pip wheel
RUN pip3 install --use-wheel -r requirements.txt

# Create local config file
ENV params_path gold_digger/config/params_local.py
RUN touch ${params_path}
RUN echo "LOCAL_CONFIG_PARAMS = {}" >> ${params_path}

# Command to execute
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "gold_digger.api_server.app:app"]
