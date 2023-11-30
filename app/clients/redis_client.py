import json

import redis

from app import config
from app.utils import zk_logger

redis_host = config.configuration.get("redis_host", "localhost")
redis_db = config.configuration.get("redis_db", 6)
redis_pass = config.configuration.get("redis_password", "")
log_tag = "redis_service_client"
logger = zk_logger.logger


class RedisServiceClient:
    def __init__(self):
        # Connect to Redis
        self.api_client = redis.StrictRedis(host=redis_host, port=6379)

    def get_scenario(self, scenario_id: str):
        try:
            # Read the JSON object from the specified key
            json_data = self.api_client.select(redis_db).get(scenario_id)
            # If the key is not found or the value is None, return None
            if json_data is None:
                return None
            # Decode the JSON data
            scenario = json.loads(json_data)
            return scenario
        except redis.exceptions.ConnectionError as e:
            logger.error(log_tag, f"Error connecting to Redis: {e}")
        except Exception as e:
            logger.error(log_tag, f"Error reading JSON from Redis: {e}")
            return None

    def get_prom_id(self):
        try:
            # Read the JSON object from the specified key
            # TODO: get redis DB name from config {use yaml to read redis config yaml from values}
            json_data = self.api_client.select(9).keys
            # If the key is not found or the value is None, return None
            if json_data is None:
                return None
            # Decode the JSON data
            print(json_data)
            prometheus_integration_data = json.loads(json_data)
            return prometheus_integration_data
        except redis.exceptions.ConnectionError as e:
            logger.error(log_tag, f"Error connecting to Redis: {e}")
        except Exception as e:
            logger.error(log_tag, f"Error reading JSON from Redis: {e}")
            return None
