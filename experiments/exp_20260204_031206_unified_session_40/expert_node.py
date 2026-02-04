"""
expert_node.py
----------------
Implements the **Expert Node** for the Swarm Architecture.

The node receives “hydration” (context) from the Gut‑Check Planner and
executes expensive reasoning using a large model (e.g., DeepSeek‑R1).
Queries are batched automatically:

* A batch is sent when **5** queries have accumulated **or**
* **10 seconds** have passed since the first pending query.

The implementation is deliberately lightweight – it provides the public
API expected by the rest of the system while keeping the heavy‑model call
as a stub that can be swapped with a real endpoint later.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Deque, List, Tuple

# --------------------------------------------------------------------------- #
# Helper Types
# --------------------------------------------------------------------------- #
QueryCallback = Callable[[str], Awaitable[None]] | Callable[[str], None]


@dataclass
class _PendingQuery:
    """Internal representation of a queued query."""
    prompt: str
    callback: QueryCallback
    timestamp: float  # time when the query was enqueued


# --------------------------------------------------------------------------- #
# Mock Expensive Model
# --------------------------------------------------------------------------- #
async def _expensive_model_batch(prompts: List[str]) -> List[str]:
    """
    Placeholder for the real expensive model (e.g., DeepSeek‑R1).

    In production this would call the model’s API. Here we simulate a
    modest latency and echo the prompt with a dummy suffix.
    """
    # Simulated latency for a heavy model (adjust as needed)
    await asyncio.sleep(0.5)
    return [f"{p}\n\n[DeepSeek‑R1 response]" for p in prompts]


# --------------------------------------------------------------------------- #
# ExpertNode
# --------------------------------------------------------------------------- #
class ExpertNode:
    """
    Core node that batches incoming queries and forwards them to an
    expensive LLM.  It is designed to be started as a background asyncio
    task within the Swarm runtime.

    Example
    -------
    >>> node = ExpertNode()
    >>> asyncio.run(node.start())
    >>> await node.add_query("Explain quantum tunnelling.", print)
    """

    # Batch configuration
    MAX_BATCH_SIZE: int = 5          # trigger batch when this many queries are queued
    MAX_BATCH_AGE: float = 10.0      # seconds – trigger batch after this time

    def __init__(self) -> None:
        # Queue of pending queries (FIFO)
        self._queue: Deque[_PendingQuery] = deque()
        # Event used to wake the background loop when a new query arrives
        self._new_query_event = asyncio.Event()
        # Background task handle
        self._worker_task: asyncio.Task | None = None
        # Shutdown flag
        self._stopped = False

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    async def start(self) -> None:
        """
        Starts the internal batching loop.  This method returns immediately
        after spawning the background task.
        """
        if self._worker_task is not None:
            raise RuntimeError("ExpertNode already started")
        self._stopped = False
        self._worker_task = asyncio.create_task(self._batch_loop())

    async def stop(self) -> None:
        """Gracefully stops the background loop and flushes remaining queries."""
        self._stopped = True
        self._new_query_event.set()  # Wake the loop so it can exit
        if self._worker_task:
            await self._worker_task
            self._worker_task = None

    async def add_query(self, prompt: str, callback: QueryCallback) -> None:
        """
        Enqueue a new query.

        Parameters
        ----------
        prompt: str
            The user / planner prompt to be processed.
        callback: Callable[[str], Awaitable|None]
            Function that receives the model's response.  It may be async
            or sync; the node will handle both.
        """
        self._queue.append(_PendingQuery(prompt=prompt,
                                        callback=callback,
                                        timestamp=time.time()))
        # Signal the background loop that work is available
        self._new_query_event.set()

    # ------------------------------------------------------------------- #
    # Internal Loop
    # ------------------------------------------------------------------- #
    async def _batch_loop(self) -> None:
        """
        Continuously monitors the queue, forming batches according to the
        configured thresholds.  When a batch is ready it calls the model
        and dispatches results to the associated callbacks.
        """
        while not self._stopped:
            # Wait until we have at least one pending query
            if not self._queue:
                self._new_query_event.clear()
                await self._new_query_event.wait()
                continue

            # Determine how long we should wait before forcing a batch
            oldest_ts = self._queue[0].timestamp
            age = time.time() - oldest_ts
            time_to_wait = max(0.0, self.MAX_BATCH_AGE - age)

            # If we already have enough queries, process immediately
            if len(self._queue) >= self.MAX_BATCH_SIZE:
                await self._process_batch()
                continue

            # Otherwise, wait for either a new query or the timeout
            try:
                self._new_query_event.clear()
                await asyncio.wait_for(self._new_query_event.wait(), timeout=time_to_wait)
            except asyncio.TimeoutError:
                # Timeout -> batch based on age
                await self._process_batch()
                continue

        # Flush any remaining queries on shutdown
        if self._queue:
            await self._process_batch()

    async def _process_batch(self) -> None:
        """Collect pending queries into a batch, call the model, and invoke callbacks."""
        batch: List[_PendingQuery] = []

        # Pull up to MAX_BATCH_SIZE items from the queue
        while self._queue and len(batch) < self.MAX_BATCH_SIZE:
            batch.append(self._queue.popleft())

        prompts = [q.prompt for q in batch]

        # Call the (mock) expensive model
        try:
            responses = await _expensive_model_batch(prompts)
        except Exception as exc:
            # If the model fails, propagate the error to each callback
            for q in batch:
                await self._invoke_callback(q.callback, f"Model error: {exc}")
            return

        # Dispatch each response to its original callback
        for q, resp in zip(batch, responses):
            await self._invoke_callback(q.callback, resp)

    async def _invoke_callback(self, cb: QueryCallback, response: str) -> None:
        """Utility that supports both async and sync callbacks."""
        if asyncio.iscoroutinefunction(cb):
            await cb(response)
        else:
            # Run sync callbacks in the default executor to avoid blocking
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, cb, response)


# --------------------------------------------------------------------------- #
# Convenience singleton (optional)
# --------------------------------------------------------------------------- #
# Many parts of the Swarm codebase expect a ready‑to‑use instance.
# Creating it here avoids repeated boilerplate in callers.
expert_node = ExpertNode()