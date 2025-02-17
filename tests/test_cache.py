import pytest
from datetime import datetime, timedelta
from src.cache import CacheManager, CacheEntry
import time

@pytest.fixture
def cache_manager():
    return CacheManager()

def test_cache_set_and_get(cache_manager):
    """Test basic cache set and get operations"""
    test_data = {"key": "value"}
    cache_manager.set("test_key", test_data, ttl=60)
    
    result = cache_manager.get("test_key")
    assert result == test_data

def test_cache_ttl_expiration(cache_manager):
    """Test that cache entries expire after TTL"""
    test_data = {"key": "value"}
    cache_manager.set("test_key", test_data, ttl=1)  # 1 second TTL
    
    # Initial get should succeed
    assert cache_manager.get("test_key") == test_data
    
    # Wait for TTL to expire
    time.sleep(1.1)
    
    # Get after expiration should return None
    assert cache_manager.get("test_key") is None

def test_cache_invalidation(cache_manager):
    """Test cache invalidation"""
    # Set multiple cache entries
    cache_manager.set("key1", "value1", ttl=60)
    cache_manager.set("key2", "value2", ttl=60)
    
    # Test single key invalidation
    cache_manager.invalidate("key1")
    assert cache_manager.get("key1") is None
    assert cache_manager.get("key2") == "value2"
    
    # Test clear all
    cache_manager.clear()
    assert cache_manager.get("key2") is None

def test_nonexistent_key(cache_manager):
    """Test getting a nonexistent key returns None"""
    assert cache_manager.get("nonexistent") is None

def test_cache_entry_creation():
    """Test CacheEntry creation and timestamp"""
    test_data = {"test": "data"}
    entry = CacheEntry(data=test_data, timestamp=time.time(), ttl=60)
    
    assert entry.data == test_data
    assert isinstance(entry.timestamp, float)
    assert entry.ttl == 60

def test_cache_thread_safety(cache_manager):
    """Test cache operations from multiple threads"""
    import threading
    
    def cache_operation():
        for i in range(100):
            cache_manager.set(f"key_{i}", i, ttl=60)
            cache_manager.get(f"key_{i}")
    
    threads = [
        threading.Thread(target=cache_operation)
        for _ in range(3)
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Verify no exceptions were raised and cache is intact
    assert cache_manager.get("key_50") == 50

def test_cache_size_limit(cache_manager):
    """Test cache behavior with many entries"""
    # Add 1000 entries
    for i in range(1000):
        cache_manager.set(f"key_{i}", i, ttl=60)
    
    # Verify random access
    assert cache_manager.get("key_500") == 500
    assert cache_manager.get("key_999") == 999