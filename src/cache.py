from typing import Any, Dict, Optional
from threading import Lock
from time import time
from dataclasses import dataclass
from datetime import timedelta

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: int  # Time to live in seconds

class CacheManager:
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            
            if time() - entry.timestamp > entry.ttl:
                del self._cache[key]
                return None
                
            return entry.data
    
    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._cache[key] = CacheEntry(
                data=value,
                timestamp=time(),
                ttl=ttl
            )
    
    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()