"""WebSocket endpoint for real-time execution streaming.

The frontend connects to ws://host/ws/executions/{execution_id}
and receives all execution events (agent status changes, output
chunks, completion) in real time via Redis pub/sub.

Flow:
1. Frontend opens WebSocket connection
2. Server subscribes to Redis channel for this execution
3. Execution engine publishes events to the same channel
4. Server forwards events to the WebSocket client
5. Client can send "cancel" message to abort execution
"""

import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.config import get_settings
from app.core.logging import get_logger
from app.services.execution_engine import EXECUTION_CHANNEL_PREFIX, cancel_execution

logger = get_logger(__name__)


async def _listen_redis(pubsub: PubSub, websocket: WebSocket) -> None:
    """Forward Redis pub/sub messages to the WebSocket client.

    Runs in a loop, polling Redis for new messages and sending
    them to the frontend. Exits when the workflow completes.
    """
    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=0.5,
            )

            if message and message["type"] == "message":
                data = message["data"]
                await websocket.send_text(data)

                # Check if workflow is complete
                try:
                    event = json.loads(data)
                    if event.get("type") == "workflow_completed":
                        logger.info(
                            "websocket_workflow_complete",
                            status=event.get("status"),
                        )
                        return
                except json.JSONDecodeError:
                    pass

            # Small sleep to prevent busy-waiting
            await asyncio.sleep(0.05)

    except Exception as exc:
        logger.error("redis_listener_error", error=str(exc))


async def _listen_client(websocket: WebSocket, execution_id: str) -> None:
    """Listen for client messages (e.g., cancel requests).

    Runs concurrently with the Redis listener. If the client
    sends a cancel message, it flags the execution for cancellation.
    """
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "cancel":
                cancel_execution(execution_id)
                logger.info("execution_cancelled_by_client", execution_id=execution_id)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


async def execution_websocket(websocket: WebSocket, execution_id: str) -> None:
    """Handle a WebSocket connection for execution streaming.

    Runs two concurrent tasks:
    - Redis listener: forwards execution events to the client
    - Client listener: handles cancel requests from the client

    When the Redis listener finishes (workflow complete) or the
    client disconnects, both tasks are cancelled and cleaned up.
    """
    await websocket.accept()
    logger.info("websocket_connected", execution_id=execution_id)

    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    pubsub: PubSub = redis.pubsub()
    channel = f"{EXECUTION_CHANNEL_PREFIX}{execution_id}"

    try:
        await pubsub.subscribe(channel)

        # Run both listeners concurrently
        redis_task = asyncio.create_task(_listen_redis(pubsub, websocket))
        client_task = asyncio.create_task(_listen_client(websocket, execution_id))

        # Wait for either to finish (redis completes on workflow_completed,
        # client completes on disconnect)
        done, pending = await asyncio.wait(
            [redis_task, client_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel whichever is still running
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", execution_id=execution_id)
    except Exception as exc:
        logger.error("websocket_error", execution_id=execution_id, error=str(exc))
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await redis.aclose()