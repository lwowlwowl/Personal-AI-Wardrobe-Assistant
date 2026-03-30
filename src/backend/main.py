"""
Backward-compatible entrypoint: `uvicorn main:app` and `python main.py` still work.
The ASGI app lives in app.main.
"""
from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    print("Server: http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
