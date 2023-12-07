""" Utility functions for zk-gpt"""
from datetime import datetime, timezone
import time

from app.utils import zk_logger

log_tag = "zk-gpt-utils"
logger = zk_logger.logger


class Utils:

    @classmethod
    def get_timestamp_from_datetime(cls, date_time: str) -> int:
        # Convert ISO 8601 timestamp to datetime object
        dt_object = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
        epoch_timestamp = int(dt_object.timestamp())
        return epoch_timestamp

    @classmethod
    def get_epoch_current_timestamp(cls) -> int:
        return int(time.time())

    @classmethod
    def get_time_difference_in_minutes(cls, start_time: str, end_time: str):
        try:
            datetime_obj1 = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            datetime_obj2 = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            time_difference = datetime_obj2 - datetime_obj1
            difference_in_minutes = time_difference.total_seconds() / 60
            return int(difference_in_minutes)
        except ValueError as e:
            logger.error(log_tag, f"Error while calculating duration : {e}")
            return 10

    @classmethod
    def get_current_date_time_utc(cls) -> str:
        current_utc_time = datetime.now(timezone.utc)
        current_time_formatted = current_utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return current_time_formatted
