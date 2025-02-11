FROM python:3.13

WORKDIR /code

COPY ./requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src

EXPOSE 80

CMD ["uvicorn", "src.main:app","--host","0.0.0.0", "--port", "80"]