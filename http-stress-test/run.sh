#!/bin/sh

set -x

# Check if URL is set
if [ -z "$URL" ]; then
    echo "URL environment variable is not set."
    exit 1
fi

# Check if ab is installed
if ! command -v ab &> /dev/null
then
    echo "ab could not be found."
    exit 1
fi

# Set default values if not provided
CONCURRENCY=${CONCURRENCY:-5}
REQUESTS=${REQUESTS:-50}

# Run Apache Benchmark
ab -c $CONCURRENCY -n $REQUESTS $URL
