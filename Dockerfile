FROM python:alpine

WORKDIR /app

COPY --chown=root:root . /app/

RUN pip install -r requirements.txt

EXPOSE 80

ENTRYPOINT [ "python", "app.py" ]
