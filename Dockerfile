FROM python:3.13

WORKDIR /code

COPY pyproject.toml alembic.ini ./
COPY src src
COPY alembic alembic

RUN pip install --upgrade pip
RUN pip install .


EXPOSE 80

CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 80
