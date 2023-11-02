class MyBaseException(Exception):
    def __init__(self, message: str, status: int, error_message: str):
        self.message = message
        self.error_message = error_message
        self.status = status


class InferenceGenerationException(BaseException):
    def __init__(self, message, status, error_message):
        super().__init__(message, status, error_message)


class ClientInteractionException(BaseException):
    def __init__(self, message, status, error_message):
        super().__init__(message, status, error_message)


class LangchainInteractionException(BaseException):
    def __init__(self, message, status, error_message):
        super().__init__(message, status, error_message)


class PineconeInteractionException(BaseException):
    def __init__(self, message, status, error_message):
        super().__init__(message, status, error_message)


class DataBaseInteractionException(BaseException):
    def __init__(self, message, status, error_message):
        super().__init__(message, status, error_message)


class ConfigDetailsFetchException(BaseException):
    def __init__(self, message, status, error_message):
        super().__init__(message, status, error_message)


class IssueSchedulerException(BaseException):
    def __init__(self, message, status, error_message):
        super().__init__(message, status, error_message)


class ReportingSchedulerException(BaseException):
    def __init__(self, message, status, error_message):
        super().__init__(message, status, error_message)



# TODO : write custom handlers for each of the above exception to send proper error message
# Exception handlers for the specific exceptions
# @app.exception_handler(ReportingSchedulerException)
# def reporting_scheduler_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=400,
#         content={"detail": exc.detail},
#     )
