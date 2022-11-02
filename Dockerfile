FROM debian:bullseye-slim

WORKDIR /manhua

COPY . .

RUN apt update && \
apt -y install python3 python3-pip zlib1g-dev && \
python3 -m pip install -r requirements.txt && \
apt --purge -y remove python3-pip zlib1g-dev && \
apt --purge -y autoremove && \
apt clean

EXPOSE 18181

CMD [ "python3", "./web.py" ]