from collections import OrderedDict

from typing import List

class ContextCache:

    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get_context(self, key: str):
        if key not in self.cache:
            return []
        else:
            self.cache.move_to_end(key)
            return self.cache.get(key)

    def put_context(self, key: str, value: List[str]):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)  # LIFO because last = False

    def upsert_context(self, key: str, value: List[str]):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)  # LIFO because last = False
