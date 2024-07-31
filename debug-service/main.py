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
import psutil
import signal
from starlette.types import ASGIApp, Receive, Scope, Send


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


class ResetMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            original_send = send

            async def custom_send(message):
                if message["type"] == "http.response.start" and scope.get("reset_connection", False):
                    headers = message.get("headers", [])
                    headers.append((b"Connection", b"close"))
                    message["headers"] = headers
                await original_send(message)

            await self.app(scope, receive, custom_send)
        else:
            await self.app(scope, receive, send)

app.add_middleware(LoggingMiddleware)
app.add_middleware(ResetMiddleware)




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


@app.get("/stress/cpu")
async def stress_cpu(cpu_percent: int, duration: int):
    if cpu_percent < 0 or cpu_percent > 100:
        raise HTTPException(status_code=400, detail="CPU percentage must be between 0 and 100")
    if duration < 0:
        raise HTTPException(status_code=400, detail="Duration must be non-negative")

    def cpu_load():
        end_time = time.time() + duration
        while time.time() < end_time:
            if psutil.cpu_percent(interval=0.1) < cpu_percent:
                pass  # This will use CPU

    await asyncio.to_thread(cpu_load)
    return {"message": f"CPU stressed at {cpu_percent}% for {duration} seconds"}

# New memory stress endpoint
@app.get("/stress/memory")
async def stress_memory(memory_percent: int, duration: int):
    if memory_percent < 0 or memory_percent > 100:
        raise HTTPException(status_code=400, detail="Memory percentage must be between 0 and 100")
    if duration < 0:
        raise HTTPException(status_code=400, detail="Duration must be non-negative")

    total_memory = psutil.virtual_memory().total
    memory_to_use = int(total_memory * memory_percent / 100)

    def memory_load():
        data = bytearray(memory_to_use)
        time.sleep(duration)
        del data

    await asyncio.to_thread(memory_load)
    return {"message": f"Memory stressed at {memory_percent}% for {duration} seconds"}

@app.get("/reset")
async def reset(request: Request, do: bool = False):
    if do:
        request.scope["reset_connection"] = True
        return Response(content="Connection will be reset", status_code=200, headers={"Connection": "close"})
    return {"message": "Reset not performed"}

server = None
should_exit = asyncio.Event()

# Graceful shutdown handler
async def graceful_shutdown(signum, frame):
    print("Received shutdown signal, closing all connections...")
    global server
    if server:
        await server.shutdown()
        print("All connections closed. Waiting 5 seconds for FIN ACK...")
        await asyncio.sleep(5)  # Wait for 5 seconds after closing connections
    should_exit.set()

# Function to start the server
async def start_server():
    global server
    config = uvicorn.Config(app, host="0.0.0.0", port=8080)
    server = uvicorn.Server(config)
    
    # Setup signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: asyncio.create_task(graceful_shutdown(s, f)))
    
    # Start the server
    await server.serve()

if __name__ == "__main__":
    port = 8080
    if "PORT" in os.environ:
        port = int(os.environ["PORT"])

    if "STARTUP_DELAY" in os.environ:
        time.sleep(int(os.environ["STARTUP_DELAY"]))

    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(start_server())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(graceful_shutdown(None, None))
        loop.close()
