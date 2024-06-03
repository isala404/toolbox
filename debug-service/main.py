import asyncio
import os
import time
import random
from typing import Optional, Dict
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import requests
import uvicorn
import logging
import shutil
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import json
from starlette.responses import StreamingResponse

app = FastAPI()

# HTML and XML content
html_content = """
<!DOCTYPE html>
<html>
<body>
<h1>Hello, World!</h1>
</body>
</html>
"""

xml_content = """
<?xml version="1.0" encoding="UTF-8"?>
<root>
    <message>Hello, World!</message>
</root>
"""

# Uploaded file
uploaded_file_path = None
logger = logging.getLogger('uvicorn.error')
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        start_time = time.time()

        # Request details
        request_details = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
        }
        if request.body:
            request_details["body"] = await request.body()

        # Response details
        response = await call_next(request)
        end_time = time.time()

        response_details = {
            "headers": dict(response.headers),
            "status_code": response.status_code,
            "latency": end_time - start_time,
            "client_ip": request.client.host,
        }
        if isinstance(response, StreamingResponse):
            response_details["body"] = "StreamingResponse"
        else:
            response_details["body"] = response.body.decode(
                'utf-8') if response.body else None

        # Combine request and response details into one log
        log_details = {
            "request": request_details,
            "response": response_details,
        }

        # Convert the log details into a JSON string and print it
        logger.info(json.dumps(log_details, default=str))

        return response


app.add_middleware(LoggingMiddleware)


@app.get("/healthz", status_code=200)
def healthz():
    return {"status": "OK"}


@app.post("/debug")
async def debug_endpoint(request: Request, response: Response, seconds: Optional[int] = None, status_code: int = 200) :
    # Delay if 'seconds' is provided
    if seconds:
        time.sleep(seconds)

    # Extract all necessary information from the request
    request_info = {
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "path_params": request.path_params,
        "cookies": request.cookies,
        "client": request.client,
        "method": request.method,
        "url": str(request.url),
        "base_url": str(request.base_url),
        "body": await request.json() if request.headers.get("content-type") == "application/json" else None
    }
    response.status_code = status_code

    return request_info


@app.post("/log")
def log(message: str, level: str):
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.debug(message)
    return {"message": message, "level": level}


class ProxyRequest(BaseModel):
    url: str
    method: str
    payload: dict = None


@app.post("/proxy")
async def proxy(proxy_request: ProxyRequest):
    method = proxy_request.method.lower()
    if method not in ['get', 'post', 'put', 'delete']:
        raise HTTPException(status_code=400, detail="Invalid method")

    try:
        if method == 'get':
            response = requests.get(
                proxy_request.url, params=proxy_request.payload)
        elif method == 'post':
            response = requests.post(
                proxy_request.url, json=proxy_request.payload)
        elif method == 'put':
            response = requests.put(
                proxy_request.url, json=proxy_request.payload)
        elif method == 'delete':
            response = requests.delete(
                proxy_request.url, json=proxy_request.payload)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        body = response.json()
    except ValueError:
        body = response.text

    return {"response": {"headers": dict(response.headers), "body": body}}


@app.post("/custom-headers")
async def custom_headers(custom_headers: Dict[str, str]):
    response = Response()
    response.headers.update(custom_headers)
    return response


@app.get("/proxy-http-bin")
async def proxy_http():
    response = requests.get("http://httpbin.org/anything")
    return response.json()


@app.get("/html", response_class=HTMLResponse)
def html():
    return html_content


@app.get("/xml", response_class=HTMLResponse)
def xml():
    return xml_content


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    global uploaded_file_path
    uploaded_file_path = f"/tmp/{file.filename}"
    with open(uploaded_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}


@app.get("/download")
async def download():
    if uploaded_file_path:
        return FileResponse(uploaded_file_path)
    else:
        return {"message": "No file uploaded"}


@app.get("/stateless")
async def stateless(seconds: Optional[int] = None):
    if seconds:
        await asyncio.sleep(seconds)
    return {"status": "OK", "headers": {"Connection": "close"}}


@app.websocket("/websocket")
async def websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass


@app.get("/sse")
async def sse():
    def event_stream():
        while True:
            yield f"data: The server time is {time.strftime('%X')}\n\n"
            time.sleep(1)
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/crash")
def crash():
    os._exit(1)


@app.get("/shutdown")
def shutdown():
    uvicorn.shutdown()
    os._exit(0)


# Fibonacci endpoint
@app.get("/fibonacci/{number}")
def fibonacci(number: int):
    def fib(n):
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            return fib(n-1) + fib(n-2)

    if number < 0:
        raise HTTPException(status_code=400, detail="Number must be non-negative")

    result = fib(number)
    return {"number": number, "fibonacci": result}

# Sort endpoint
@app.get("/sort")
def sort(n: int):
    if n <= 0:
        raise HTTPException(status_code=400, detail="Number of elements must be positive")

    array = [1] * (10**int(n/3)) + [3] * (10**int(n/3)) + [0] * (10**int(n/3))
    array = sorted(array)

    return {"sorted": True}


if __name__ == "__main__":
    port = 8080
    if "PORT" in os.environ:
        port = os.environ["PORT"]

    if "STARTUP_DELAY" in os.environ:
        time.sleep(int(os.environ["STARTUP_DELAY"]))

    uvicorn.run(app, host="0.0.0.0", port=port)
