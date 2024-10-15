FROM python:3.11

COPY main.py /app/
COPY main.sqlite /app/
COPY .env /app/
COPY plot.png /app/

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

CMD ["python", "./main.py"]

