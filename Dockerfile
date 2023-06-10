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

# busybox "ip" is insufficient:
#   [rootlesskit:child ] error: executing [[ip tuntap add name tap0 mode tap] [ip link set tap0 address 02:50:00:00:00:01]]: exit status 1
RUN apk add --no-cache iproute2 fuse-overlayfs

# "/run/user/UID" will be used by default as the value of XDG_RUNTIME_DIR
RUN mkdir /run/user && chmod 1777 /run/user

# create a default user preconfigured for running rootless dockerd
RUN set -eux; \
	adduser -h /home/rootless -g 'Rootless' -D -u 1000 rootless; \
	echo 'rootless:100000:65536' >> /etc/subuid; \
	echo 'rootless:100000:65536' >> /etc/subgid

RUN set -eux; \
	\
	apkArch="$(apk --print-arch)"; \
	case "$apkArch" in \
		'x86_64') \
			url='https://download.docker.com/linux/static/stable/x86_64/docker-rootless-extras-24.0.2.tgz'; \
			;; \
		'aarch64') \
			url='https://download.docker.com/linux/static/stable/aarch64/docker-rootless-extras-24.0.2.tgz'; \
			;; \
		*) echo >&2 "error: unsupported 'rootless.tgz' architecture ($apkArch)"; exit 1 ;; \
	esac; \
	\
	wget -O 'rootless.tgz' "$url"; \
	\
	tar --extract \
		--file rootless.tgz \
		--strip-components 1 \
		--directory /usr/local/bin/ \
		'docker-rootless-extras/rootlesskit' \
		'docker-rootless-extras/rootlesskit-docker-proxy' \
		'docker-rootless-extras/vpnkit' \
	; \
	rm rootless.tgz; \
	\
	rootlesskit --version; \
	vpnkit --version

# pre-create "/var/lib/docker" for our rootless user
RUN set -eux; \
	mkdir -p /home/rootless/.local/share/docker; \
	chown -R rootless:rootless /home/rootless/.local/share/docker

VOLUME /home/rootless/.local/share/docker

USER rootless

WORKDIR /dcrx_api/

EXPOSE 2277

CMD ["/start.sh"]