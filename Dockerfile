FROM alpine:latest

# environment
ENV MIRROR=http://mirrors.cloud.tencent.com/alpine
ENV PACKAGES=alpine-baselayout,\
alpine-keys,\
apk-tools,\
busybox,\
libc-utils,\
xz



RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.cloud.tencent.com/g' /etc/apk/repositories && \
apk update && \
apk add --no-cache \
shadow \
python3 \
python3-dev \
zlib-dev \
jpeg-dev \
gcc \
g++ && \
python3 -m ensurepip && \
pip3 install -i https://mirrors.cloud.tencent.com/pypi/simple click Flask importlib-metadata itsdangerous Jinja2 MarkupSafe Pillow PyMySQL waitress Werkzeug zipp && \
apk del --purge \
zlib-dev \
jpeg-dev \
python3-dev \
gcc \
g++ && \
rm -rf /root/.cache /tmp/* && \
echo "**** create abc user and make our folders ****" && \
groupmod -g 1000 users && \
useradd -u 911 -U -d /workdir -s /bin/sh abc && \
usermod -G users abc && \
mkdir -p /workdir

COPY shell/init.sh /

COPY py-comicsviewer/ /workdir

EXPOSE 18181

VOLUME /workdir/contents
VOLUME /workdir/data

ENTRYPOINT ["/bin/sh", "/init.sh"]
