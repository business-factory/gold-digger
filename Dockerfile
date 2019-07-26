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

FROM python:3.7.4
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

RUN pip install pipenv

# Set the default directory
WORKDIR /app

COPY ./Pipfile .
COPY ./Pipfile.lock .

# Install Python dependencies
RUN pipenv install --deploy --system

# Add all files to container
COPY ./ ./

EXPOSE 8080

CMD gunicorn --config=gold_digger/settings/settings_gunicorn.py --log-config=$LOGGING_GUNICORN gold_digger.api_server.app:app
