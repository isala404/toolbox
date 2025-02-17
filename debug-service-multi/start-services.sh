#!/bin/bash

# Start Python service
cd /app/python
source venv/bin/activate
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
bal run target/bin/debug_service_multi.jar &

# Start health check aggregator
cd /app/health-check
node index.js &

# Keep container running
wait 
