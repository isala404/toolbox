# Resource Stress Testing API

A FastAPI application for stress testing system resources (CPU and Memory).

## Features

- **CPU Stress Testing**: Stress CPU usage to a specified percentage
- **Memory Stress Testing**: Stress memory usage to a specified percentage  
- **Combined Stress Testing**: Stress both CPU and memory simultaneously
- **System Information**: Get current system resource usage

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. POST `/stress-cpu`
Stress CPU to specified percentage for given duration.

**Request Body:**
```json
{
  "percentage": 75.0,
  "duration": 30
}
```

### 2. POST `/stress-memory`
Stress memory to specified percentage for given duration.

**Request Body:**
```json
{
  "percentage": 50.0,
  "duration": 15
}
```

### 3. POST `/stress-both`
Stress both CPU and memory simultaneously.

**Request Body:**
```json
{
  "percentage": 60.0,
  "duration": 20
}
```

### 4. GET `/system-info`
Get current system resource information.

**Response:**
```json
{
  "cpu_cores": 8,
  "cpu_usage_percent": 12.5,
  "total_memory_gb": 16.0,
  "available_memory_gb": 8.2,
  "memory_usage_percent": 48.8
}
```

## Parameters

- **percentage**: Float between 0-100 representing the percentage of resource to stress
- **duration**: Integer greater than 0 representing duration in seconds

## Example Usage

### Using curl:

```bash
# Stress CPU at 80% for 30 seconds
curl -X POST "http://localhost:8000/stress-cpu" \
     -H "Content-Type: application/json" \
     -d '{"percentage": 80.0, "duration": 30}'

# Stress memory at 60% for 20 seconds
curl -X POST "http://localhost:8000/stress-memory" \
     -H "Content-Type: application/json" \
     -d '{"percentage": 60.0, "duration": 20}'

# Stress both CPU and memory at 70% for 25 seconds
curl -X POST "http://localhost:8000/stress-both" \
     -H "Content-Type: application/json" \
     -d '{"percentage": 70.0, "duration": 25}'

# Get system information
curl -X GET "http://localhost:8000/system-info"
```

### Using Python requests:

```python
import requests

# Stress CPU
response = requests.post(
    "http://localhost:8000/stress-cpu",
    json={"percentage": 75.0, "duration": 30}
)
print(response.json())

# Get system info
response = requests.get("http://localhost:8000/system-info")
print(response.json())
```

## Interactive Documentation

Once the server is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Warning

⚠️ **Use with caution**: This tool can significantly impact system performance and should be used responsibly. High stress levels may cause system instability or unresponsiveness. 
