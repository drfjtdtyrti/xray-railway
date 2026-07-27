FROM alpine:3.19

RUN apk add --no-cache \
    nginx \
    python3 \
    curl \
    bash \
    unzip \
    gettext \
    ca-certificates

# Pull latest xray binary
RUN XRAY_VER=$(curl -fsSL https://api.github.com/repos/XTLS/Xray-core/releases/latest \
        | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": *"\(.*\)".*/\1/') \
    && echo "Downloading Xray ${XRAY_VER}..." \
    && curl -fSL "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VER}/Xray-linux-64.zip" \
        -o /tmp/xray.zip \
    && unzip -q /tmp/xray.zip -d /tmp/xray \
    && install -m 755 /tmp/xray/xray /usr/local/bin/xray \
    && rm -rf /tmp/xray*

# nginx tmp dirs
RUN mkdir -p /var/log/nginx /var/lib/nginx/tmp /run/nginx

WORKDIR /app
COPY config.json     /etc/xray/config.json
COPY nginx.conf.tmpl /etc/nginx/nginx.conf.tmpl
COPY stats_api.py    /app/stats_api.py
COPY start.sh        /app/start.sh
COPY dashboard/      /usr/share/nginx/dashboard/

RUN chmod +x /app/start.sh

EXPOSE 8080
CMD ["/bin/bash", "/app/start.sh"]
