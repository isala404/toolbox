FROM node:alpine

WORKDIR /app
RUN mkdir -p certs

# Install openssl
RUN apk add --no-cache openssl

# Create a non-root user first
RUN adduser -u 10014 -D appuser

COPY package*.json ./
RUN npm install

COPY . .

RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
-keyout certs/server.key -out certs/server.crt \
-subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

RUN chown -R appuser:appuser /app/

# Switch to non-root user
USER 10014

EXPOSE 443

CMD ["npm", "start"]
