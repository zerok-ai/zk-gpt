import uvicorn
from fastapi import FastAPI

import config
from app.utils import zk_logger
from app.routes import internal_demo_route, inference_route, events_route, deprecated_route
from schedulers.issue_inference_generation_scheduler import issue_scheduler
from schedulers.slack_reporting_scheduler import slack_reporting_scheduler

log_tag = "main"
logger = zk_logger.logger

app = FastAPI()


app.include_router(internal_demo_route.router, prefix="", tags=["internal_demo_route"])
app.include_router(inference_route.router, prefix="", tags=["inference_route"])
app.include_router(events_route.router, prefix="", tags=["events_route"])
app.include_router(deprecated_route.router, prefix="", tags=["deprecated_route"])


def fetch_secrets_and_load_config():
    try:
        config.configuration
        # If successful, return True
        return True
    except Exception as e:
        logger.error(log_tag, f"Error fetching config and secrets: {str(e)}")
        return False


if __name__ == '__main__':
    if fetch_secrets_and_load_config():
        # start issue scheduler
        issue_scheduler.start()
        slack_reporting_scheduler.start()
        # Start the application only if the config and secrets are fetched successfully
        uvicorn.run(app, host="0.0.0.0", port=80)
