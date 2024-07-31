# Use an official Python runtime as a parent image
FROM python:3.10-alpine

# Set the working directory in the container to /app
WORKDIR /app

RUN apk add --no-cache curl bind-tools net-tools jq inetutils-telnet gcc python3-dev musl-dev linux-headers

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Create a non-root user
USER 10014

# Run main.py when the container launches
CMD ["python", "main.py"]
