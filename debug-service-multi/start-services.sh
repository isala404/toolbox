#!/bin/bash

# Start Python service
cd /app/python
python3 main.py &

# Start Go service
cd /app/go
./main &

# Start Node service
cd /app/node
node index.js &

# Start Java service
cd /app/java
java -jar target/debug-service-1.0-SNAPSHOT.jar &

# Start Ballerina service
cd /app/ballerina
bal run target/bin/service.jar &

# Keep container running
wait 
