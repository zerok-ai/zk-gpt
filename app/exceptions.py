from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from typing import List


# Define a base exception class
class MyBaseException(Exception):
    def __init__(self, detail: str):
        self.detail = detail


# Extend the base exception with more specific exceptions
class CustomExceptionA(MyBaseException):
    pass


class CustomExceptionB(MyBaseException):
    pass


# Define response models for exceptions
class ErrorDetail(BaseModel):
    detail: str

# Exception handlers for the specific exceptions
# @app.exception_handler(CustomExceptionA)
# async def custom_exception_handler_a(request, exc):
#     return JSONResponse(
#         status_code=400,
#         content={"detail": exc.detail},
#     )
#
#
# @app.exception_handler(CustomExceptionB)
# async def custom_exception_handler_b(request, exc):
#     return JSONResponse(
#         status_code=400,
#         content={"detail": exc.detail},
#     )
#
#
# @app.post("/endpoint_a")
# async def raise_custom_exception_a():
#     raise CustomExceptionA(detail="Custom Exception A Occurred")
#
#
# @app.post("/endpoint_b")
# async def raise_custom_exception_b():
#     raise CustomExceptionB(detail="Custom Exception B Occurred")
