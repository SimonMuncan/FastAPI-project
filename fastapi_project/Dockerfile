FROM python:3.10.12

WORKDIR /app

COPY requirements.txt .

RUN pip installl --no-chache-dir -r requirements.txt

COPY ./app /app

EXPOSE 80

CMD ["uvicoen",main:app","--host","0.0.0.0","--port","80"]
