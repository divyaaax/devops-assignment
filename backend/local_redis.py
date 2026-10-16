"""
Lightweight embedded Redis TCP Server
Provides a 100% Redis-compatible TCP server on 127.0.0.1:6379 using fakeredis.
Allows running the full stack locally on Windows/Linux without Docker or Redis installed!
"""

import sys
import logging
from fakeredis import TcpFakeServer

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [local-redis] %(message)s")
logger = logging.getLogger("local_redis")

def run():
    host = "127.0.0.1"
    port = 6379
    logger.info(f"Starting standalone embedded Redis server on {host}:{port}...")
    server = TcpFakeServer((host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping embedded Redis server.")
    finally:
        server.server_close()

if __name__ == "__main__":
    run()
