import yaml


class Config:
    def __init__(self, file_path):
        self.file_path = file_path
        self.config_data = self._load_config()

    def _load_config(self):
        try:
            with open(self.file_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")

    def get(self, key, default=None):
        return self.config_data.get(key, default)

    def keys(self):
        return self.config_data.keys()

    def has_key(self, key):
        return key in self.config_data


configuration = Config("config/config.yaml")
