FROM python:3

RUN mkdir -p /opt/src/voting_official
WORKDIR /opt/src/voting_official

COPY voting_official/application.py ./application.py
COPY voting_official/configuration.py ./configuration.py
COPY voting_official/models.py ./models.py
COPY voting_official/roleCheckDecorator.py ./roleCheckDecorator.py
COPY voting_official/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]