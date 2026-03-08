"""
Run with:
  set REDIS_URL=redis://localhost:6379/0
  py scripts/rq_worker.py
"""

import os
import redis
from rq import Worker, Queue, Connection

listen = ["quiz_generation"]
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
conn = redis.from_url(redis_url)

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker([Queue(name) for name in listen])
        worker.work()
