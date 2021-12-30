FROM python:3.9-buster

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

COPY /dev_scripts /app/dev_scripts

WORKDIR /app

RUN pip install -r requirements.txt

RUN pip install waitress

COPY /dist/ /app/



RUN pip install /app/*.whl

COPY candle_data_service/create_environment.py /app/
COPY candle_data_service/.dev.env /app/
COPY candle_data_service/.main.env /app/
COPY candle_data_service/database_create.sql /app/

ARG CACHEBUST=1
RUN echo "$CACHEBUST"
RUN ./dev_scripts/update_proto.sh

ENV PYTHONPATH="/app/:/app/candle_data_service:/app/candle_data_service/grpc_generated"


ENTRYPOINT ["sh", "-c"]

CMD [ "python -u create_environment.py && waitress-serve --call candle_data_service:create_app" ]

# entrypoint: ['sh', '-c']
# command: "'python -u create_environment.py && waitress-serve --call candle_data_service:create_app'"


