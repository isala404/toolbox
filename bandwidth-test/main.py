from fastapi import FastAPI
import speedtest

app = FastAPI()

def run_speed_test():
    st = speedtest.Speedtest()
    st.get_best_server()
    return st

@app.get("/test-ingress")
async def test_ingress():
    """
    Tests download speed.
    """
    st = run_speed_test()
    download_speed = st.download() / 1_000_000  # Convert to Mbps
    return {"download_speed_mbps": download_speed}

@app.get("/test-egress")
async def test_egress():
    """
    Tests upload speed.
    """
    st = run_speed_test()
    upload_speed = st.upload() / 1_000_000  # Convert to Mbps
    return {"upload_speed_mbps": upload_speed}

@app.get("/test-all")
async def test_all():
    """
    Tests both download and upload speed.
    """
    st = run_speed_test()
    download_speed = st.download() / 1_000_000  # Convert to Mbps
    upload_speed = st.upload() / 1_000_000  # Convert to Mbps
    ping = st.results.ping
    return {
        "download_speed_mbps": download_speed,
        "upload_speed_mbps": upload_speed,
        "ping_ms": ping
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
