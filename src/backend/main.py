"""
向後相容入口：歷史指令 `uvicorn main:app`、`python main.py` 仍可用。
應用實體定義於 app.main。
"""
from app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    print("启动服务器: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
