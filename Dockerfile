FROM docker:24.0.2-dind
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /tmp/requirements.txt
COPY README.md /README.md
COPY .version /.version

COPY ./scripts/start.sh /start.sh
RUN chmod +x /start.sh

COPY ./scripts/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

COPY ./scripts/prestart.sh /prestart.sh
RUN chmod +x /prestart.sh

COPY ./dcrx_api /dcrx_api

COPY ./setup.py /setup.py

RUN apk add --no-cache gcc libc-dev make \
     python3 py3-pip python3-dev linux-headers \
     postgresql-dev musl-dev \
    && ln -sf python3 /usr/bin/python \
    && ln -sf pip3 /usr/bin/pip

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install -e .


WORKDIR /dcrx_api/

EXPOSE 2277

CMD ["/start.sh"]