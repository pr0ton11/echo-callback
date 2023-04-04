FROM python:alpine

WORKDIR /app

COPY --chown=root:root . /app/

RUN pip install -r requirements.txt

EXPOSE 3000

ENV BEHIND_HTTPS_PROXY "false"

ENTRYPOINT [ "python", "app.py" ]
