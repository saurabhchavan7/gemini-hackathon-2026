"""
Simple cache to avoid redundant Gemini API calls during testing
"""
import hashlib
import json
import os
from datetime import datetime, timedelta

class CacheService:
    """Caches Gemini responses to avoid rate limits during testing"""
    
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, data: bytes) -> str:
        """Generate cache key from data hash"""
        return hashlib.md5(data).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """Get cache file path"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, data: bytes, max_age_minutes: int = 60):
        """Retrieve cached result if exists and not expired"""
        
        cache_key = self._get_cache_key(data)
        cache_path = self._get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check if expired
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > timedelta(minutes=max_age_minutes):
                print(f"[CACHE] Expired for key: {cache_key[:8]}")
                return None
            
            print(f"[CACHE] Hit! Skipping Gemini API call (key: {cache_key[:8]})")
            return cached_data['result']
            
        except Exception as e:
            print(f"[ERROR] Cache read error: {e}")
            return None
    
    def set(self, data: bytes, result: dict):
        """Store result in cache"""
        
        cache_key = self._get_cache_key(data)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'result': result
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"[CACHE] Cached result (key: {cache_key[:8]})")
            
        except Exception as e:
            print(f"[ERROR] Cache write error: {e}")
    
    def clear(self):
        """Clear all cached data"""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)
        print("[CACHE] Cache cleared")