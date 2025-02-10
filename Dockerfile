FROM python:3.10

WORKDIR /src

COPY requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /src

EXPOSE 80

CMD ["uvicorn", "main:app","--host","0.0.0.0","--port","80"]