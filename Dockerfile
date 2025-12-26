FROM tiangolo/uvicorn-gunicorn:python3.8-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
COPY Pipfile ./Pipfile

# install pipenv for managing packages & env
RUN pip install --no-cache-dir pipenv
# install all of the requirements
RUN pipenv install --deploy --clear --system

COPY ./app /app/app