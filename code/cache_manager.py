"""
Cache manager for storing and retrieving API call results.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib
import logging
from config import CACHE_DIR, CACHE_ENABLED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """Simple file-based cache for API responses."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_enabled = CACHE_ENABLED
        self.cache_ttl = 86400  # 24 hours in seconds
        
    def _get_cache_path(self, key: str) -> Path:
        """Get the cache file path for a key."""
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result for a key."""
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Check TTL
            if time.time() - data.get('timestamp', 0) > self.cache_ttl:
                logger.debug(f"Cache expired for {key[:10]}...")
                os.remove(cache_path)
                return None
            
            logger.debug(f"Cache hit for {key[:10]}...")
            return data.get('result')
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any]) -> bool:
        """Store a result in cache."""
        if not self.cache_enabled:
            return False
        
        cache_path = self._get_cache_path(key)
        try:
            data = {
                'timestamp': time.time(),
                'result': value
            }
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Cache stored for {key[:10]}...")
            return True
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)
        return {
            "cache_enabled": self.cache_enabled,
            "cache_count": len(files),
            "cache_size_bytes": total_size,
            "cache_size_mb": round(total_size / (1024 * 1024), 2)
        }