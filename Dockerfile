FROM python:3.4

RUN mkdir -p /usr/src/
ADD ./app /usr/src/app
WORKDIR /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./update.py" ]
