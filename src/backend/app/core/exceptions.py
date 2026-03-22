"""應用層業務例外；路由可捕獲後轉為 HTTP 回應（與修改.md 對齊）。"""


class AppError(Exception):
    """可預期的業務錯誤，附帶建議的 HTTP 狀態碼。"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
