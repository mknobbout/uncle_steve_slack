FROM python:3.7-slim-buster

RUN mkdir /code
WORKDIR /code

COPY requirements.txt /code/

RUN apt-get update -y --fix-missing; \
    apt-get install -y git python3-dev tesseract-ocr; \
    apt-get clean -y
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY run_bot.py /code/
# COPY test_model.py /code/
# COPY train_model.py /code/
# COPY data /code/data
COPY model /code/model
COPY unclesteve_qa /code/unclesteve_qa

ENTRYPOINT ["/bin/bash", "-c"]
CMD [ "python /code/run_bot.py" ]
