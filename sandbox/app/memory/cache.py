# Implementação de um sistema básico de cache persistente usando pickle.

import pickle
import os

class NexusCache:
    def __init__(self, cache_file='data/cache/nexus_cache.pkl'):
        self.cache_file = cache_file
        self.cache = {}
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'rb') as f:
                self.cache = pickle.load(f)

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def set(self, key, value):
        self.cache[key] = value
        self._save_cache()

    def get(self, key, default=None):
        return self.cache.get(key, default)

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]
            self._save_cache()