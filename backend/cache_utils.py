import pickle

try:
    import redis
except ImportError:
    redis = None
from flask import current_app


def _client():
    if redis is None:
        return None
    return redis.Redis.from_url(current_app.config["REDIS_URL"])


def cache_get(key):
    try:
        client = _client()
        if client is None:
            return None
        value = client.get(key)
    except Exception:
        return None
    if value is None:
        return None
    try:
        return pickle.loads(value)
    except (pickle.PickleError, EOFError):
        return None


def cache_set(key, value, timeout=None):
    ttl = timeout or current_app.config.get("CACHE_DEFAULT_TIMEOUT", 300)
    try:
        client = _client()
        if client is None:
            return False
        client.setex(key, int(ttl), pickle.dumps(value))
    except Exception:
        return False
    return True


def cache_delete(*keys):
    if not keys:
        return
    try:
        client = _client()
        if client is None:
            return
        client.delete(*keys)
    except Exception:
        return


def cache_delete_pattern(pattern):
    try:
        client = _client()
        if client is None:
            return
        for key in client.scan_iter(match=pattern):
            client.delete(key)
    except Exception:
        return
