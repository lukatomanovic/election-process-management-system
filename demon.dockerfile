FROM python:3

RUN mkdir -p /opt/src/demon
WORKDIR /opt/src/demon

COPY demon/application.py ./application.py
COPY demon/configuration.py ./configuration.py
COPY demon/models.py ./models.py
COPY demon/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]