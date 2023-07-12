FROM python:3.11-slim

# set environment variables
ENV PYTHONPATH /home/app
ENV APP_HOME /home/app
ENV GIT_STORE /home/app/download

RUN addgroup --system app && adduser --system --group app

WORKDIR $APP_HOME

RUN set -ex \
    \
    && apt-get update \
    && apt-get install -y git \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .

# install python dependencies
RUN pip install --upgrade pip
RUN pip install -U setuptools
RUN pip install -r requirements.txt

COPY main.py .

RUN mkdir -p $GIT_STORE

# autostart command
CMD python main.py -c -u devalv -d $GIT_STORE -w 2
