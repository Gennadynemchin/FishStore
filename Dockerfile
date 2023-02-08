FROM python:3.8-slim-buster

WORKDIR /app

VOLUME /credentials

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python" ]

CMD ["bot.py" ]