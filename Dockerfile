FROM python:3.9-slim

WORKDIR /app
ADD . .
RUN pip3 install -r requirements.txt

CMD ["python", "-u", "rebootpoedevice.py" ]
