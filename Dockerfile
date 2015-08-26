FROM python:3.4

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ADD ./app/requirements.txt /usr/src/app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ADD ./app /usr/src/app

CMD [ "python", "./update.py" ]
