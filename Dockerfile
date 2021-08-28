FROM python:3.9-buster

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

RUN pip install waitress

COPY /dist/ /app/

RUN pip install /app/*.whl


ENTRYPOINT ["waitress-serve", "--call", "candle_data_service:create_app"]

# CMD [ "flask", "run" ]
