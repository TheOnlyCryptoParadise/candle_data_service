FROM python:3.9-buster

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

RUN pip install waitress

COPY /dist/ /app/



RUN pip install /app/*.whl

COPY candle_data_service/create_environment.py /app/
COPY candle_data_service/.dev.env /app/
COPY candle_data_service/.main.env /app/
COPY candle_data_service/database_create.sql /app/

ENTRYPOINT ["waitress-serve", "--call", "candle_data_service:create_app"]

# CMD [ "flask", "run" ]
