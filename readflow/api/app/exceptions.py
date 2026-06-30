from fastapi import HTTPException


class ReadFlowException(HTTPException):
    pass


class ParseException(ReadFlowException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=422, detail=detail)
