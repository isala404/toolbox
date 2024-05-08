FROM alpine:3

RUN apk add --no-cache apache2-utils

COPY . .

USER 10014

CMD ["sh", "run.sh"]
