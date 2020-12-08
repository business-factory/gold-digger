########################################################
# Dockerfile to build Python application 'gold-digger'
# Based on Ubuntu
########################################################
#
# BUILD IMAGE
#   docker build --rm=true -t gold-digger:latest .
#
# RUN CONTAINER
#   docker run --rm -it --publish=8080:8080 --name=gold-digger gold-digger:latest
#   docker run --rm -it --publish=8080:8080 --name=gold-digger -v "<path to you gold_digger project>:/app" gold-digger:latest
#   docker run --detach --restart=always --publish=8080:8080 --name=gold-digger gold-digger:latest
#
#   docker run --rm --name gold-digger-cron -ti gold-digger:latest python -m gold_digger cron
#   docker run --detach --restart=always --name gold-digger-cron gold-digger:latest python -m gold_digger cron
#

FROM python:3.9.1
MAINTAINER ROI Hunter

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev locales locales-all

# Setup system locale
RUN locale-gen en_US.utf8
ENV LANG en_US.utf8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.utf8
RUN update-locale LANG=en_US.utf8

# Timezone
ENV TZ=Europe/Prague
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set the default directory
WORKDIR /app

COPY ./requirements.txt .

# Install Python dependencies
RUN pip install -U pip wheel && pip install -r requirements.txt

# Add all files to container
COPY ./ ./

EXPOSE 8080

CMD gunicorn --config=gold_digger/settings/settings_gunicorn.py --logger-class=gold_digger.utils.gunicorn_logging.GunicornLogger gold_digger.api_server.app:app
