import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class SSEManager:
    """Manages all active SSE client connections using asyncio Queues."""
    def __init__(self):
        self.clients = set() 

    def add_client(self) -> asyncio.Queue:
        """Adds a new client queue to the set and returns it."""
        queue = asyncio.Queue()
        self.clients.add(queue)
        logger.info(f"SSE client connected. Total clients: {len(self.clients)}")
        return queue

    def remove_client(self, queue: asyncio.Queue):
        """Removes a client queue from the set."""
        self.clients.discard(queue)
        logger.info(f"SSE client disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, event_data: dict):
        """Converts event data to a JSON string and pushes it to all client queues."""
        message = f"data: {json.dumps(event_data)}\n\n"
        for queue in list(self.clients):
            try:
                await queue.put(message)
            except Exception as e:
                logger.warning(f"Could not put message in queue, removing client: {e}")
                self.remove_client(queue)

sse_manager = SSEManager()