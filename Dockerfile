FROM tiangolo/uvicorn-gunicorn:python3.8-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
COPY Pipfile ./Pipfile

# opencv dependencies
# RUN apt-get update
# RUN apt-get install ffmpeg libsm6 libxext6  -y

# install pipenv for managing packages & env
RUN pip install --no-cache-dir pipenv
# install all of the requirements
RUN pipenv install --deploy --clear --system

COPY ./app /app/app