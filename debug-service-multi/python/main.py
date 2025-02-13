from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "python"}

@app.post("/echo")
async def echo(request: Request):
    body = await request.json()
    return {"service": "python", "echo": body}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081) 