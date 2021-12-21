FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app

CMD exec gunicorn --bind :$PORT --worker-class uvicorn.workers.UvicornWorker --timeout 0 --threads 8 app.main:app