import redis

conn = redis.StrictRedis(host='localhost', port=6379, db=9)