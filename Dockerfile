FROM python:3.13

WORKDIR /code

COPY ./pyproject.toml ./requirements.txt ./
COPY ./src ./src

RUN pip install --upgrade pip
RUN pip install .


EXPOSE 80

CMD ["uvicorn", "src.main:app","--host","0.0.0.0", "--port", "80"]
