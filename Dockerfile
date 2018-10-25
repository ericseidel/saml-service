FROM ubuntu:16.04 as common

RUN apt-get update --fix-missing \
    && apt-get install -y wget git

COPY keys keys
COPY git.sh ./

ARG lumavate_exceptions_branch=master
ARG lumavate_signer_branch=master
ARG lumavate_token_branch=master
ARG lumavate_request_branch=master
ARG lumavate_properties_branch=master
ARG lumavate_service_util=master

COPY requirements.txt /

RUN apt-get update && apt-get install -y git python3-pip libpq-dev libffi-dev libffi-dev xmlsec1 \
  && mkdir /root/.ssh/ \
  && touch /root/.ssh/known_hosts \
  && ssh-keyscan github.com >> /root/.ssh/known_hosts \
  && chmod 400 /keys/* \
  && mkdir /python_packages \
  && cd /python_packages \
  && /git.sh -i /keys/python-exceptions-rsa clone git@github.com:LabelNexus/python-exceptions.git lumavate_exceptions \
  && cd lumavate_exceptions \
  && git checkout $lumavate_exceptions_branch \
  && rm -rf /python_packages/lumavate_exceptions/.git \
  && cd .. \
  && git clone https://github.com/Lumavate-Team/python-signer.git lumavate_signer \
  && cd lumavate_signer \
  && git checkout $lumavate_signer_branch \
  && rm -rf /python_packages/lumavate_signer/.git \
  && cd .. \
  && /git.sh -i /keys/python-token-rsa clone git@github.com:LabelNexus/python-token.git lumavate_token \
  && cd lumavate_token \
  && git checkout $lumavate_token_branch \
  && rm -rf /python_packages/lumavate_token/.git \
  && cd .. \
  && /git.sh -i /keys/python-api-request-rsa clone git@github.com:LabelNexus/python-api-request.git lumavate_request \
  && cd lumavate_request \
  && git checkout $lumavate_request_branch \
  && rm -rf /python_packages/lumavate_request/.git \
  && cd .. \
  && /git.sh -i /keys/python-widget-properties-rsa clone git@github.com:LabelNexus/python-widget-properties.git lumavate_properties \
  && cd lumavate_properties \
  && git checkout $lumavate_properties_branch \
  && rm -rf /python_packages/lumavate_properties/.git \
  && cd .. \
  && /git.sh -i /keys/python-service-util-rsa clone git@github.com:Lumavate-Team/python-service-util.git lumavate_service_util \
  && cd lumavate_service_util \
  && git checkout $lumavate_service_util_branch \
  && rm -rf /python_packages/lumavate_service_util/.git \
  && cd / \
  && pip3 install -r requirements.txt \
  && mkdir -p /app

ENV PYTHONPATH /python_packages
WORKDIR /app
COPY app /app

ENV APP_SETTINGS config/dev.cfg

CMD gunicorn app:app -b 0.0.0.0:5000 --workers 4 --worker-class eventlet --reload
