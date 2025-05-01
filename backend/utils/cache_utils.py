import time
from functools import wraps

_cache = {}

def get_cached_data(key):
  """ Get data from cache if it exists """
  if key in _cache:
    expiry, data = _cache[key]
    if expiry > time.time():
      return data
    else:
      del _cache[key]
    return None
  
def set_cached_data(key, data, ttl=3600):
  """ Store data in cache with expriation time """
  expiry = time.time() + ttl
  _cache[key] = (expiry, data)

def cache_decorator(ttl=3600):
  def decorartor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      # Create cache key 
      key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

      # Check cache
      cached_result = get_cached_data(key)
      if cached_result:
        return cached_result
      
      # Call function and cache result
      result = func(*args, **kwargs)
      set_cached_data(key, result, ttl)
      return result 
    return wrapper
  return decorartor