FROM timbru31/java-node:17-jdk-iron

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    golang \
    maven

# Install Ballerina
RUN curl -fsSL https://dist.ballerina.io/downloads/2201.11.0/ballerina-2201.11.0-swan-lake-linux-x64.deb -o ballerina.deb \
    && dpkg -i ballerina.deb \
    && rm ballerina.deb

# Set up Python service
WORKDIR /app/python
COPY python/requirements.txt .
RUN python3 -m venv venv \
    && . venv/bin/activate \
    && pip install -r requirements.txt
COPY python/main.py .

# Set up Go service
WORKDIR /app/go
COPY go/go.mod .
COPY go/main.go .
RUN go build -o main .

# Set up Node service
WORKDIR /app/node
COPY node/package.json .
RUN npm install
COPY node/index.js .

# Set up Java service
WORKDIR /app/java
COPY java/pom.xml .
RUN mvn dependency:go-offline
COPY java/src ./src
RUN mvn package

# Set up Ballerina service
WORKDIR /app/ballerina
COPY ballerina/ .
RUN bal build

# Copy start script
WORKDIR /app
COPY start-services.sh .
RUN chmod +x start-services.sh

# Create a non-root user
USER 10014

CMD ["./start-services.sh"] 
