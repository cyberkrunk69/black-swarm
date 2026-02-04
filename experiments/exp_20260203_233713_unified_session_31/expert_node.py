"""
expert_node.py
----------------
Implements the **Expert Node** component of the Swarm architecture.

The node receives “hydration” (i.e., problem statements, context, etc.) from the
Gut‑Check Planner and forwards them to an expensive LLM (e.g., DeepSeek‑R1).
To keep costs and latency reasonable it batches requests:

* **Batch size trigger** – 5 queued queries
* **Time trigger** – 10 seconds since the first query entered the batch

When either trigger fires the node sends the whole batch to the model in a
single call, then routes each individual response back to the original caller.

The implementation is deliberately lightweight, using ``asyncio`` so it can be
integrated into the existing event‑driven Swarm framework without blocking the
main loop.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any, Awaitable, Callable, Deque, List, Tuple

# --------------------------------------------------------------------------- #
# Placeholder for the expensive model call.
# Replace ``call_expensive_model`` with the actual API client for DeepSeek‑R1
# or any other model you intend to use.
# --------------------------------------------------------------------------- #
async def call_expensive_model(queries: List[str]) -> List[str]:
    """
    Simulate a call to an expensive LLM.

    Parameters
    ----------
    queries: List[str]
        The batched queries to be processed.

    Returns
    -------
    List[str]
        Mocked responses – one per query, in the same order.
    """
    # In a real implementation you would call the model here, e.g.:
    # response = await openai.ChatCompletion.acreate(..., messages=queries)
    # return [choice.message.content for choice in response.choices]

    await asyncio.sleep(1)  # simulate network / compute latency
    return [f"Response to: {q}" for q in queries]


# --------------------------------------------------------------------------- #
# ExpertNode definition
# --------------------------------------------------------------------------- #
class ExpertNode:
    """
    Core class handling batched queries for the Expert Node.

    Usage
    -----
    >>> node = ExpertNode()
    >>> asyncio.run(node.start())
    >>> # elsewhere in the code:
    >>> result = await node.add_query("Explain quantum entanglement")
    """

    BATCH_SIZE = 5          # trigger when 5 queries are queued
    BATCH_TIMEOUT = 10.0    # trigger after 10 seconds from first queued query

    def __init__(self) -> None:
        # Queue holds tuples: (query_text, future_to_set_result)
        self._queue: Deque[Tuple[str, asyncio.Future[str]]] = deque()
        self._batch_lock = asyncio.Lock()
        self._batch_task: asyncio.Task | None = None
        self._running = False

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    async def start(self) -> None:
        """
        Starts the background task that monitors the queue and flushes batches.
        This coroutine should be awaited once (typically at application start).
        """
        if self._running:
            return
        self._running = True
        self._batch_task = asyncio.create_task(self._batch_monitor())

    async def stop(self) -> None:
        """
        Gracefully stops the background monitor and flushes any remaining queries.
        """
        self._running = False
        if self._batch_task:
            await self._batch_task
        await self._flush_batch()   # ensure leftovers are processed

    async def add_query(self, query: str) -> str:
        """
        Queue a new query and await its response.

        Parameters
        ----------
        query: str
            The problem / prompt to be sent to the expert model.

        Returns
        -------
        str
            The model's response for this specific query.
        """
        future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        async with self._batch_lock:
            self._queue.append((query, future))
            # If we just hit the batch size, trigger an immediate flush.
            if len(self._queue) >= self.BATCH_SIZE:
                # schedule immediate flush without waiting for timeout
                asyncio.create_task(self._flush_batch())
        return await future

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    async def _batch_monitor(self) -> None:
        """
        Background coroutine that watches the queue and flushes it when the
        timeout condition is met.
        """
        while self._running:
            await asyncio.sleep(0.5)  # poll interval – cheap and responsive
            async with self._batch_lock:
                if not self._queue:
                    continue
                # Determine age of the oldest entry
                oldest_timestamp = getattr(self._queue[0][1], "_enqueue_time", None)
                if oldest_timestamp is None:
                    # Attach a timestamp the first time we see the entry
                    for _, fut in self._queue:
                        setattr(fut, "_enqueue_time", time.monotonic())
                    oldest_timestamp = time.monotonic()
                elapsed = time.monotonic() - oldest_timestamp
                if elapsed >= self.BATCH_TIMEOUT:
                    asyncio.create_task(self._flush_batch())

    async def _flush_batch(self) -> None:
        """
        Pulls up to BATCH_SIZE items from the queue, sends them to the model,
        and resolves each awaiting future with its corresponding response.
        """
        async with self._batch_lock:
            if not self._queue:
                return

            batch: List[Tuple[str, asyncio.Future[str]]] = []
            while self._queue and len(batch) < self.BATCH_SIZE:
                batch.append(self._queue.popleft())

        queries = [q for q, _ in batch]
        try:
            responses = await call_expensive_model(queries)
        except Exception as exc:  # pragma: no cover – defensive
            for _, fut in batch:
                if not fut.done():
                    fut.set_exception(exc)
            return

        # Map each response back to its future
        for resp, (_, fut) in zip(responses, batch):
            if not fut.done():
                fut.set_result(resp)


# --------------------------------------------------------------------------- #
# Convenience singleton for the current experiment (optional)
# --------------------------------------------------------------------------- #
_expert_node_instance: ExpertNode | None = None


async def get_expert_node() -> ExpertNode:
    """
    Retrieve a shared ``ExpertNode`` instance, creating and starting it on first
    use.  This helper mirrors the pattern used by other Swarm components.
    """
    global _expert_node_instance
    if _expert_node_instance is None:
        _expert_node_instance = ExpertNode()
        await _expert_node_instance.start()
    return _expert_node_instance


# --------------------------------------------------------------------------- #
# Example usage (removed from production code – kept for reference)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    async def demo():
        node = await get_expert_node()
        tasks = [node.add_query(f"Query {i}") for i in range(12)]
        results = await asyncio.gather(*tasks)
        for r in results:
            print(r)
        await node.stop()

    asyncio.run(demo())