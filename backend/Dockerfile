###########
# BUILDER #
###########

# pull official base image
FROM python:3.6-slim-buster as builder

# set work directory
WORKDIR /usr/src/impact-app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apt-get update \
    && apt-get install -y libpq-dev gcc python3-dev musl-dev postgresql-client

# install poppler, which is a  dependency of pdf2txt
RUN apt-get install -y build-essential libpoppler-cpp-dev pkg-config python-dev

#COPY . /usr/src/impact-app/

# install app dependencies
#RUN pip install --upgrade pip setuptools
COPY ./requirements.txt /usr/src/impact-app/requirements.txt
RUN pip install Cython
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/impact-app/wheels -r requirements.txt

#########
# FINAL #
#########
FROM python:3.6-slim-buster

# create directory for the app user
RUN mkdir -p /home/impact-app

# create the app user
RUN groupadd -g 10001 impactapp
RUN useradd -u 10002 -g 10001 impactapp

# create the appropriate directories
ENV HOME=/home/impact-app
ENV APP_HOME=/home/impact-app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
RUN mkdir $APP_HOME/media
WORKDIR $APP_HOME

# install dependencies
RUN apt-get update
COPY --from=builder /usr/src/impact-app/wheels /wheels
COPY --from=builder /usr/src/impact-app/requirements.txt .
#RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

RUN apt-get update & apt-get install -y netcat-openbsd libmariadb-dev libpoppler-cpp-dev

# copy entrypoint.sh
COPY ./entrypoint.sh $APP_HOME

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R impactapp:impactapp $APP_HOME

# change to the app user
USER impactapp

# run entrypoint.sh
ENTRYPOINT ["/home/impact-app/web/entrypoint.sh"]
