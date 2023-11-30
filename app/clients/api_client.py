from typing import Optional, Dict

import requests


class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Optional[Dict] = None, json=None, headers: Optional[Dict] = None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url=url, data=data, json=json, headers=headers)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, data: Dict, headers: Optional[Dict] = None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def post_without_response(self, endpoint: str, data: Dict, headers: Optional[Dict] = None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
