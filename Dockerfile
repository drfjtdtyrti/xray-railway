FROM alpine:3.19 AS builder
RUN apk add --no-cache wget unzip
RUN wget -q https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip \
      -O /tmp/xray.zip \
    && unzip /tmp/xray.zip xray -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/xray

FROM alpine:3.19
RUN apk add --no-cache ca-certificates
COPY --from=builder /usr/local/bin/xray /usr/local/bin/xray
COPY config.json /etc/xray/config.json
EXPOSE 8080
CMD ["xray", "-config", "/etc/xray/config.json"]
