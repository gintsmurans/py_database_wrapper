from typing import Any, Generic, TypeVar

T = TypeVar("T")


class StatusModel:
    status: str
    message: str | None

    def __init__(self, status: str = "ok", message: str | None = None):
        self.status = status
        self.message = message

    def __str__(self):
        return str(self.toDict())

    def __repr__(self):
        return self.__str__()

    def toDict(self) -> dict[str, Any]:
        newDict = {"status": self.status}
        if self.message:
            newDict["message"] = self.message
        return newDict


class MessageModel:
    """
    MessageModel
    """

    msg: str
    code: int

    def __init__(self, msg: str, code: int = 0):
        self.msg = msg
        self.code = code

    def __str__(self) -> str:
        return f"code: {self.code} | message: {self.msg}"

    def toDict(self) -> dict[str, Any]:
        return {
            "msg": self.msg,
            "code": self.code,
        }


class ReturnModel(Generic[T]):
    """
    ReturnModel
    """

    success: bool

    message: str | None
    code: int | None
    result: T | None

    # Additional info
    info: Any | None

    def __init__(
        self,
        success: bool = False,
        message: str | None = None,
        code: int | None = None,
        result: T | None = None,
        info: Any | None = None,
    ):
        self.success = success
        self.message = message
        self.code = code
        self.result = result
        self.info = info

    def __str__(self) -> str:
        return f"success: {self.success} | code: {self.code} | message: {self.message} | result: {self.result} | info: {self.info}"

    def toDict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "code": self.code,
            "result": self.result,
            "info": self.info,
        }
