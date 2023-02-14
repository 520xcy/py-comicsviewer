FROM ghcr.io/linuxserver/baseimage-alpine:3.17

WORKDIR /

RUN apk update && \
apk add --no-cache python3 zlib-dev && \
python3 -m ensurepip && \
pip3 install click Flask importlib-metadata itsdangerous Jinja2 MarkupSafe Pillow PyMySQL waitress Werkzeug zipp && \
apk del --purge zlib-dev && \
rm -rf /root/.cache /tmp/*

COPY root/ /

EXPOSE 18181

VOLUME /py-comicsviewer/contents
VOLUME /py-comicsviewer/data