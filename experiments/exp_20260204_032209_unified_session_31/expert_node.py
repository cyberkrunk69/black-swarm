"""
expert_node.py
----------------
Implements the **Expert Node** as described in SWARM_ARCHITECTURE_V2.md.

Key responsibilities
~~~~~~~~~~~~~~~~~~~~~
* Receive “hydration” payloads from the Gut‑Check Planner.
* Accumulate incoming queries and dispatch them to an expensive LLM
  (e.g., DeepSeek‑R1) in **batches**.
* A batch is sent when **either**:
    - 5 queries have been collected, **or**
    - 10 seconds have elapsed since the first query in the current batch.
* Return the model’s responses back to the caller in the same order as the
  incoming queries.

The implementation is deliberately lightweight – it focuses on the batching
logic, async handling, and a mock integration point for the expensive model.
Replace ``_call_expensive_model`` with a real API client when integrating
into production.
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Deque, List, Tuple, Awaitable, Optional

# --------------------------------------------------------------------------- #
# Helper data structures
# --------------------------------------------------------------------------- #

@dataclass
class _PendingQuery:
    """Container for a single query awaiting batch execution."""
    payload: Any
    future: asyncio.Future  # Will be set with the model's response


# --------------------------------------------------------------------------- #
# ExpertNode implementation
# --------------------------------------------------------------------------- #

class ExpertNode:
    """
    Core class for the Expert Node.

    Usage example
    -------------
    >>> node = ExpertNode()
    >>> result = await node.hydrate({"question": "Explain quantum tunneling."})
    >>> print(result)
    """

    # Batch configuration (as per spec)
    MAX_BATCH_SIZE = 5          # trigger batch when this many queries are queued
    MAX_BATCH_DELAY = 10.0      # seconds – trigger batch after this time

    def __init__(self,
                 model_caller: Optional[Callable[[List[Any]], Awaitable[List[Any]]]] = None):
        """
        Parameters
        ----------
        model_caller : Callable[[List[Any]], Awaitable[List[Any]]], optional
            Async function that receives a list of payloads and returns a list of
            responses in the same order. If omitted, a mock implementation is used.
        """
        self._queue: Deque[_PendingQuery] = deque()
        self._batch_timer_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._model_caller = model_caller or self._call_expensive_model

    async def hydrate(self, payload: Any) -> Any:
        """
        Public entry point used by the Gut‑Check Planner.

        Parameters
        ----------
        payload : Any
            Arbitrary data describing the query (e.g., a dict with a prompt).

        Returns
        -------
        Any
            The response from the expensive model, corresponding to *payload*.
        """
        async with self._lock:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            self._queue.append(_PendingQuery(payload=payload, future=future))

            # Start the timer if this is the first item in a new batch
            if len(self._queue) == 1:
                self._batch_timer_task = asyncio.create_task(self._batch_timer())

            # If we hit the batch size limit, fire immediately
            if len(self._queue) >= self.MAX_BATCH_SIZE:
                await self._dispatch_batch()

        # Wait for the model's answer
        return await future

    # ------------------------------------------------------------------- #
    # Internal batching helpers
    # ------------------------------------------------------------------- #

    async def _batch_timer(self):
        """Waits MAX_BATCH_DELAY seconds and then forces a batch dispatch."""
        await asyncio.sleep(self.MAX_BATCH_DELAY)
        async with self._lock:
            # If there are still pending queries, dispatch them
            if self._queue:
                await self._dispatch_batch()

    async def _dispatch_batch(self):
        """Collects pending queries and sends them to the expensive model."""
        # Cancel the timer if it exists – a new one will be started on the next query
        if self._batch_timer_task and not self._batch_timer_task.done():
            self._batch_timer_task.cancel()
            try:
                await self._batch_timer_task
            except asyncio.CancelledError:
                pass
        self._batch_timer_task = None

        # Extract the current batch
        batch: List[_PendingQuery] = []
        while self._queue and len(batch) < self.MAX_BATCH_SIZE:
            batch.append(self._queue.popleft())

        payloads = [pq.payload for pq in batch]

        # Call the expensive model (async)
        try:
            responses = await self._model_caller(payloads)
        except Exception as exc:
            # Propagate the exception to all pending futures
            for pq in batch:
                if not pq.future.done():
                    pq.future.set_exception(exc)
            return

        # Map responses back to the original futures preserving order
        for pq, resp in zip(batch, responses):
            if not pq.future.done():
                pq.future.set_result(resp)

    # ------------------------------------------------------------------- #
    # Mock / placeholder for the expensive model
    # ------------------------------------------------------------------- #

    async def _call_expensive_model(self, batch_payloads: List[Any]) -> List[Any]:
        """
        Placeholder implementation that pretends to call DeepSeek‑R1 (or similar).

        In a real deployment replace this method with a proper async client call,
        e.g. using ``httpx`` or the vendor SDK.

        For demonstration we simply echo the payload with a short artificial delay.
        """
        await asyncio.sleep(0.5)  # simulate network / compute latency
        # Very naive "processing": just wrap payload in a dict
        return [{"original": p, "response": f"Processed by DeepSeek‑R1"} for p in batch_payloads]

    # ------------------------------------------------------------------- #
    # Graceful shutdown helper (optional)
    # ------------------------------------------------------------------- #

    async def close(self):
        """
        Flush any remaining queries and clean up internal tasks.
        """
        async with self._lock:
            if self._queue:
                await self._dispatch_batch()
            if self._batch_timer_task and not self._batch_timer_task.done():
                self._batch_timer_task.cancel()
                try:
                    await self._batch_timer_task
                except asyncio.CancelledError:
                    pass


# --------------------------------------------------------------------------- #
# Simple self‑test (executed only when run as a script)
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    async def demo():
        node = ExpertNode()

        # Fire a handful of queries at irregular intervals
        async def send(idx):
            payload = {"question": f"What is the meaning of life? ({idx})"}
            resp = await node.hydrate(payload)
            print(f"Result {idx}: {resp}")

        tasks = [asyncio.create_task(send(i)) for i in range(7)]

        # Wait for all to finish
        await asyncio.gather(*tasks)

        await node.close()

    asyncio.run(demo())