FROM python:3.8-slim-buster

WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip install numpy cyclonedds

COPY src src
COPY subscriber.py subscriber.py
COPY loop.py loop.py
COPY pub.py pub.py
COPY cyclonedds.xml cyclonedds.xml

ENV CYCLONEDDS_URI file:///app/cyclonedds.xml
CMD python subscriber.py
#CMD python loop.py