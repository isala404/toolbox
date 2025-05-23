from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import threading
import time
import psutil
import multiprocessing
import gc
from typing import Dict, Any

app = FastAPI(title="Resource Stress Testing API", version="1.0.0")

class StressRequest(BaseModel):
    percentage: float = Field(..., ge=0, le=100, description="Percentage of resource to stress (0-100)")
    duration: int = Field(..., gt=0, description="Duration in seconds")

class StressResponse(BaseModel):
    message: str
    percentage: float
    duration: int
    status: str

def stress_cpu(percentage: float, duration: int):
    """Stress CPU by consuming specified percentage for given duration"""
    num_cores = multiprocessing.cpu_count()
    
    def cpu_stress():
        end_time = time.time() + duration
        while time.time() < end_time:
            if percentage < 100:
                # Calculate work/sleep ratio to achieve target percentage
                work_time = percentage / 100 * 0.1
                sleep_time = (100 - percentage) / 100 * 0.1
                
                start = time.time()
                while time.time() - start < work_time:
                    pass  # Busy wait
                time.sleep(sleep_time)
            else:
                # 100% CPU usage - no sleep
                pass
    
    # Start threads for each core to maximize CPU usage
    threads = []
    num_threads = max(1, int(num_cores * percentage / 100))
    
    for _ in range(num_threads):
        thread = threading.Thread(target=cpu_stress)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

def stress_memory(percentage: float, duration: int):
    """Stress memory by consuming specified percentage for given duration"""
    # Get total system memory
    total_memory = psutil.virtual_memory().total
    target_memory = int(total_memory * percentage / 100)
    
    # Allocate memory in chunks
    chunk_size = 1024 * 1024  # 1MB chunks
    chunks = []
    
    try:
        # Allocate memory
        allocated = 0
        while allocated < target_memory:
            remaining = target_memory - allocated
            current_chunk_size = min(chunk_size, remaining)
            chunk = bytearray(current_chunk_size)
            chunks.append(chunk)
            allocated += current_chunk_size
        
        # Hold memory for specified duration
        time.sleep(duration)
        
    finally:
        # Clean up memory
        chunks.clear()
        gc.collect()

def stress_both(percentage: float, duration: int):
    """Stress both CPU and memory simultaneously"""
    cpu_thread = threading.Thread(target=stress_cpu, args=(percentage, duration))
    memory_thread = threading.Thread(target=stress_memory, args=(percentage, duration))
    
    cpu_thread.start()
    memory_thread.start()
    
    cpu_thread.join()
    memory_thread.join()

@app.get("/")
async def root():
    return {"message": "Resource Stress Testing API", "endpoints": ["/stress-cpu", "/stress-memory", "/stress-both"]}

@app.post("/stress-cpu", response_model=StressResponse)
async def stress_cpu_endpoint(request: StressRequest):
    """
    Stress CPU to specified percentage for given duration
    """
    try:
        def run_stress():
            stress_cpu(request.percentage, request.duration)
        
        thread = threading.Thread(target=run_stress)
        thread.start()
        thread.join()
        
        return StressResponse(
            message=f"CPU stressed at {request.percentage}% for {request.duration} seconds",
            percentage=request.percentage,
            duration=request.duration,
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stressing CPU: {str(e)}")

@app.post("/stress-memory", response_model=StressResponse)
async def stress_memory_endpoint(request: StressRequest):
    """
    Stress memory to specified percentage for given duration
    """
    try:
        def run_stress():
            stress_memory(request.percentage, request.duration)
        
        thread = threading.Thread(target=run_stress)
        thread.start()
        thread.join()
        
        return StressResponse(
            message=f"Memory stressed at {request.percentage}% for {request.duration} seconds",
            percentage=request.percentage,
            duration=request.duration,
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stressing memory: {str(e)}")

@app.post("/stress-both", response_model=StressResponse)
async def stress_both_endpoint(request: StressRequest):
    """
    Stress both CPU and memory to specified percentage for given duration
    """
    try:
        def run_stress():
            stress_both(request.percentage, request.duration)
        
        thread = threading.Thread(target=run_stress)
        thread.start()
        thread.join()
        
        return StressResponse(
            message=f"CPU and Memory stressed at {request.percentage}% for {request.duration} seconds",
            percentage=request.percentage,
            duration=request.duration,
            status="completed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stressing resources: {str(e)}")

@app.get("/system-info")
async def get_system_info():
    """Get current system resource information"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    return {
        "cpu_cores": multiprocessing.cpu_count(),
        "cpu_usage_percent": cpu_percent,
        "total_memory_gb": round(memory.total / (1024**3), 2),
        "available_memory_gb": round(memory.available / (1024**3), 2),
        "memory_usage_percent": memory.percent
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
