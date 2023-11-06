import argparse

import uvicorn
from fastapi import FastAPI

from app import config
from app.routes import internal_demo_route, inference_route, events_route, deprecated_route
from app.schedulers.issue_inference_generation_scheduler import issue_scheduler
from app.schedulers.slack_reporting_scheduler import slack_reporting_scheduler
from app.utils import zk_logger

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
    parser = argparse.ArgumentParser(description="Example command-line argument parser")
    parser.add_argument('-c', '--config', type=str, help="Path to the configuration file")
    args = parser.parse_args()
    config_file = args.config
    print(config_file)
    # self.config_file = config_file
    # self.config_data = self._load_config()
    if fetch_secrets_and_load_config():
        # start issue scheduler
        logger.info(log_tag,"staring issue inference generation scheduler")
        issue_scheduler.start()
        logger.info(log_tag,"staring reporting generation scheduler")
        slack_reporting_scheduler.start()
        # Start the application only if the config and secrets are fetched successfully
        uvicorn.run(app, host="0.0.0.0", port=80)
