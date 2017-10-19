########################################################
# Dockerfile to build Python application 'gold-digger'
# Based on Ubuntu
########################################################
#
# BUILD IMAGE
#   docker build --rm=true -t gold-digger:latest .
#
# RUN CONTAINER
#   docker run --rm -it --publish=8000:8000 --name=gold-digger gold-digger:latest
#   docker run --rm -it --publish=8000:8000 --name=gold-digger -v "<path to you gold_digger project>:/app" gold-digger:latest
#   docker run --rm --detach --restart=always --publish=8000:8000 --name=gold-digger gold-digger:latest
#
#   docker run --name gold-digger-cron -ti gold-digger:latest cron -f
#   docker run --rm --detach --restart=always --name gold-digger-cron gold-digger:latest cron -f
#

FROM python:3.6
MAINTAINER ROI Hunter

# Install system dependencies
RUN apt-get update && apt-get install -y libpq-dev cron locales locales-all

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

ADD ./requirements.txt /app

# Install Python dependencies
RUN pip install -U pip wheel && pip install --use-wheel -r requirements.txt

# Add all files to container
ADD . /app

# Setup cron for daily updates
# Add crontab file in the cron directory
ADD crontab.conf /etc/cron.d/daily-exchange-rates
RUN chmod 600 /etc/cron.d/daily-exchange-rates
RUN touch cron.log

EXPOSE 8000

ENV GUNICORN_WORKERS=4
ENV GUNICORN_BIND="0.0.0.0:8000"

CMD ["gunicorn", "--config=gold_digger/settings/settings_gunicorn.py", "gold_digger.api_server.app:app"]
